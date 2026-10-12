#!/usr/bin/env python3
"""Check penny-list SKUs against nearby Home Depot stores.

For each store near the given ZIP codes and each SKU in skus.tsv, this asks
homedepot.com for the store's status for the item (CLEARANCE, INACTIVE,
DELETED or ACTIVE), its in-store quantity and any store clearance price, then
writes a ranked CSV of leads.

A $0.01 price never shows online, so every lead still has to be scanned in
the store. Keep runs occasional (once a week is plenty): the script makes one
request per item per store.

Usage:
    python3 penny_scan.py --zip 61761 --zip 60645 --radius 10
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")
GRAPHQL = "https://www.homedepot.com/federation-gateway/graphql?opname=productClientOnlyProduct"
QUERY = """query productClientOnlyProduct($itemId: String!, $storeId: String, $zipCode: String) {
  product(itemId: $itemId) {
    itemId
    identifiers { productLabel brandName storeSkuNumber }
    pricing(storeId: $storeId) { value clearance { value } }
    fulfillment(storeId: $storeId, zipCode: $zipCode) {
      anchorStoreStatusType
      fulfillmentOptions { services { type locations { isAnchor inventory { quantity } } } }
    }
  }
}"""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def http(url, data=None, headers=None, follow=True):
    h = {"User-Agent": UA, "Accept": "application/json, text/html"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    for attempt in range(3):
        try:
            with opener.open(req, timeout=30) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                return e.code, e.headers, b""
            if attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(3 * (attempt + 1))


def find_stores(zip_code, radius):
    url = (f"https://www.homedepot.com/StoreSearchServices/v2/storesearch"
           f"?address={zip_code}&radius={radius}&pagesize=30")
    _, _, body = http(url)
    return [dict(id=s["storeId"], name=s["name"], zip=zip_code,
                 address=f'{s["address"]["street"]}, {s["address"]["city"]}',
                 miles=round(s["distance"], 1))
            for s in json.loads(body)["stores"]]


def resolve_item_id(sku):
    """Store SKU -> online item id, or None if the SKU has no product page."""
    status, headers, _ = http(f"https://www.homedepot.com/s/{sku}", follow=False)
    m = re.search(r"/p/[^ ]*/(\d{9})", headers.get("Location", "") if status in (301, 302) else "")
    return m.group(1) if m else None


def check(item_id, store):
    body = json.dumps({"operationName": "productClientOnlyProduct",
                       "variables": {"itemId": item_id, "storeId": store["id"], "zipCode": store["zip"]},
                       "query": QUERY}).encode()
    _, _, raw = http(GRAPHQL, data=body, headers={
        "content-type": "application/json", "x-experience-name": "general-merchandise",
        "x-hd-dc": "origin", "x-debug": "false", "Origin": "https://www.homedepot.com",
        "Referer": "https://www.homedepot.com/"})
    p = json.loads(raw)["data"]["product"]
    f = p.get("fulfillment") or {}
    qty = None
    for opt in f.get("fulfillmentOptions") or []:
        for svc in opt.get("services") or []:
            if svc["type"] == "bopis":
                for loc in svc["locations"]:
                    if loc.get("isAnchor"):
                        qty = loc["inventory"]["quantity"]
    pricing = p.get("pricing") or {}
    return dict(status=f.get("anchorStoreStatusType"), qty=qty,
                price=pricing.get("value"), clearance=(pricing.get("clearance") or {}).get("value"))


def score(row):
    """Rough lead ranking: deep local markdown > clearance status > inactive with stock."""
    s = 0.0
    if row["clearance"] and row["price"]:
        s += 4 + 4 * (1 - row["clearance"] / row["price"])
    elif row["status"] == "CLEARANCE":
        s += 3
    elif row["status"] == "INACTIVE" and (row["qty"] or 0) > 0:
        s += 3
    price = row["price"] or 0
    s += 3 if price >= 150 else 2 if price >= 50 else 1
    if "IL" in row["states"].split():
        s += 2
    if "Today" in row["seen"] or "Yesterday" in row["seen"]:
        s += 1.5
    return round(s, 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", action="append", required=True, help="ZIP code to search near (repeatable)")
    ap.add_argument("--radius", type=int, default=10, help="store search radius in miles (default 10)")
    ap.add_argument("--skus", default=str(Path(__file__).with_name("skus.tsv")),
                    help="tab-separated: sku, name, where/when reported, states")
    ap.add_argument("--out", default="penny_leads.csv")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    skus = [line.rstrip("\n").split("\t") for line in open(args.skus, encoding="utf-8") if line.strip()]
    stores = {}
    for z in args.zip:
        for s in find_stores(z, args.radius):
            stores.setdefault(s["id"], s)
    print(f"{len(stores)} stores, {len(skus)} SKUs", file=sys.stderr)

    with ThreadPoolExecutor(args.workers) as ex:
        ids = dict(zip([s[0] for s in skus], ex.map(resolve_item_id, [s[0] for s in skus])))
    gone = [s for s in skus if not ids[s[0]]]
    print(f"{len(skus) - len(gone)} SKUs found online, {len(gone)} delisted", file=sys.stderr)

    jobs = [(s, st) for s in skus if ids[s[0]] for st in stores.values()]

    def run(job):
        (sku, name, seen, states), st = job
        try:
            r = check(ids[sku], st)
        except Exception as e:  # keep going; one bad response shouldn't sink the run
            print(f"skip {sku} @ {st['name']}: {e}", file=sys.stderr)
            return None
        return dict(store=st["name"], store_id=st["id"], miles=st["miles"], sku=sku, name=name,
                    seen=seen, states=states, **r)

    with ThreadPoolExecutor(args.workers) as ex:
        rows = [r for r in ex.map(run, jobs) if r and r["status"] != "ACTIVE"]
    for r in rows:
        r["pct_off"] = round(100 * (1 - r["clearance"] / r["price"])) if r["clearance"] and r["price"] else ""
        r["score"] = score(r)
    rows.sort(key=lambda r: (r["store"], -r["score"]))

    fields = ["store", "store_id", "miles", "score", "sku", "name", "status", "qty", "price",
              "clearance", "pct_off", "seen", "states"]
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        for sku, name, seen, states in gone:
            w.writerow(dict(store="(any - delisted online)", sku=sku, name=name, seen=seen, states=states))
    print(f"wrote {len(rows)} leads to {args.out}", file=sys.stderr)

    for st in sorted(stores.values(), key=lambda s: s["miles"]):
        top = [r for r in rows if r["store_id"] == st["id"]][:5]
        if top:
            print(f"\n{st['name']} ({st['address']}, {st['miles']} mi)")
            for r in top:
                tag = f"${r['clearance']} ({r['pct_off']}% off)" if r["clearance"] else r["status"].lower()
                print(f"  {r['sku']:>10}  {r['name'][:48]:48}  {tag}")


if __name__ == "__main__":
    main()
