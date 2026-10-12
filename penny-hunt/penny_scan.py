#!/usr/bin/env python3
"""Check the latest Home Depot penny reports against the stores near you.

1. Pulls recent $0.01 reports from PennyCentral's public penny list, plus any
   SKUs you add by hand in skus_extra.tsv.
2. Finds the Home Depot stores around each area in config.json.
3. Asks homedepot.com, for every item at every store, for the store's status
   (CLEARANCE, INACTIVE, DELETED or ACTIVE), its in-store quantity and any
   store clearance price.
4. Writes a ranked CSV of leads and, with --board, the Penny Hunt Board page.

A $0.01 price never shows online, so every lead still has to be scanned in
the store. Keep runs occasional (a few times a week at most): the script makes
one request per item per store.

Usage:
    python3 penny_scan.py                      # CSV only
    python3 penny_scan.py --board board.html   # CSV + board page
"""
import argparse
import csv
import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")
PENNY_LIST = "https://www.pennycentral.com/api/penny-list?perPage=100&page={page}"
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
        except (urllib.error.URLError, http.client.HTTPException, ConnectionError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(3 * (attempt + 1))


def fetch_penny_reports(max_age_days):
    """Recent $0.01 reports from PennyCentral, newest first."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    items, page = [], 1
    while True:
        _, _, body = http(PENNY_LIST.format(page=page))
        data = json.loads(body)
        for it in data["items"]:
            seen = datetime.fromisoformat(it["lastSeenAt"].replace("Z", "+00:00"))
            if seen < cutoff:
                continue
            locs = it.get("locations") or {}
            items.append(dict(
                sku=it["sku"],
                item_id=it.get("internetNumber") or None,
                name=" ".join(x for x in (it.get("brand"), it["name"]) if x),
                retail=it.get("retailPrice"),
                seen=seen.date().isoformat(),
                states=" ".join(f"{k}{v}" for k, v in sorted(locs.items(), key=lambda kv: -kv[1])),
                il_cities=", ".join(sorted((it.get("cityLocations") or {}).get("IL", {}))),
            ))
        if page >= data.get("pageCount", 1):
            return items
        page += 1


def load_extra(path):
    """Hand-added SKUs: tab-separated sku, name, date seen (YYYY-MM-DD), states."""
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        p = (line.split("\t") + ["", "", "", ""])[:4]
        rows.append(dict(sku=p[0].replace("-", "").strip(), item_id=None, name=p[1], retail=None,
                         seen=p[2] or None, states=p[3], il_cities=""))
    return rows


def resolve_item_id(sku):
    """Store SKU -> online item id, or None if the SKU has no product page."""
    status, headers, _ = http(f"https://www.homedepot.com/s/{sku}", follow=False)
    m = re.search(r"/p/[^ ]*/(\d{9})", headers.get("Location", "") if status in (301, 302) else "")
    return m.group(1) if m else None


def find_stores(area):
    url = (f"https://www.homedepot.com/StoreSearchServices/v2/storesearch"
           f"?address={area['zip']}&radius={area['radius']}&pagesize=30")
    _, _, body = http(url)
    out = []
    for s in json.loads(body)["stores"]:
        a, hours = s["address"], s.get("storeHours", {}).get("monday", {})
        out.append(dict(id=s["storeId"], name=s["name"].replace("Mccormick", "McCormick"), zip=area["zip"],
                        address=f'{a["street"]}, {a["city"]} {a["postalCode"]}', phone=s.get("phone", ""),
                        miles=round(s["distance"], 1),
                        hours=f'{hours.get("open", "")}–{hours.get("close", "")}'))
    return out


def check(item_id, store):
    body = json.dumps({"operationName": "productClientOnlyProduct",
                       "variables": {"itemId": item_id, "storeId": store["id"], "zipCode": store["zip"]},
                       "query": QUERY}).encode()
    _, _, raw = http(GRAPHQL, data=body, headers={
        "content-type": "application/json", "x-experience-name": "general-merchandise",
        "x-hd-dc": "origin", "x-debug": "false", "Origin": "https://www.homedepot.com",
        "Referer": "https://www.homedepot.com/"})
    p = json.loads(raw)["data"]["product"]
    if not p:
        return None
    f = p.get("fulfillment") or {}
    qty = None
    for opt in f.get("fulfillmentOptions") or []:
        for svc in opt.get("services") or []:
            if svc["type"] == "bopis":
                for loc in svc["locations"]:
                    if loc.get("isAnchor"):
                        qty = loc["inventory"]["quantity"]
    pricing = p.get("pricing") or {}
    return dict(status=f.get("anchorStoreStatusType") or "UNKNOWN", qty=qty, price=pricing.get("value"),
                clearance=(pricing.get("clearance") or {}).get("value"),
                label=(p.get("identifiers") or {}).get("productLabel"))


def score(row, today):
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
    if row["il_cities"]:
        s += 2
    if row["seen"] and (today - datetime.fromisoformat(row["seen"]).date()).days <= 2:
        s += 1.5
    return round(s, 2)


def build_board(template, out, areas, stores, items, results, checked):
    code = {"CLEARANCE": "C", "ACTIVE": "A", "INACTIVE": "i", "DELETED": "d"}
    data = dict(
        checked=f"{checked:%b} {checked.day}, {checked.year}", checkedISO=checked.isoformat(),
        areas=[dict(zip=a["zip"], label=a["label"]) for a in areas],
        stores=[dict(id=s["id"], n=s["name"], r=s["zip"], a=s["address"], ph=s["phone"], mi=s["miles"], h=s["hours"])
                for s in stores],
        items=[])
    for it in items:
        per = {sid: [code.get(r["status"], "?"), -1 if r["qty"] is None else r["qty"], r["clearance"]]
               for (sku, sid), r in results.items() if sku == it["sku"]}
        price = next((r["price"] for (sku, _), r in results.items() if sku == it["sku"] and r["price"]), it["retail"])
        e = dict(s=it["sku"], n=it["name"], p=price, seen=it["seen"] or "", st=it["states"], il=it["il_cities"])
        if per:
            e["per"] = per
        data["items"].append(e)
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = Path(template).read_text(encoding="utf-8").replace("__DATA__", payload)
    Path(out).write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--out", default="penny_leads.csv", help="CSV of leads (default penny_leads.csv)")
    ap.add_argument("--board", help="also write the Penny Hunt Board page to this path")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    today = datetime.now().date()

    items = fetch_penny_reports(cfg.get("max_age_days", 45))
    have = {it["sku"] for it in items}
    items += [x for x in load_extra(HERE / cfg.get("extra_skus", "skus_extra.tsv")) if x["sku"] not in have]
    with ThreadPoolExecutor(args.workers) as ex:
        missing = [it for it in items if not it["item_id"]]
        for it, iid in zip(missing, ex.map(lambda it: resolve_item_id(it["sku"]), missing)):
            it["item_id"] = iid

    stores = {}
    for area in cfg["areas"]:
        for s in find_stores(area):
            stores.setdefault(s["id"], s)
    print(f"{len(items)} penny reports, {len(stores)} stores", file=sys.stderr)

    jobs = [(it, st) for it in items if it["item_id"] for st in stores.values()]

    def run(job):
        it, st = job
        try:
            return (it["sku"], st["id"]), check(it["item_id"], st)
        except Exception as e:  # keep going; one bad response shouldn't sink the run
            print(f"skip {it['sku']} @ {st['name']}: {e}", file=sys.stderr)
            return (it["sku"], st["id"]), None

    with ThreadPoolExecutor(args.workers) as ex:
        results = {k: r for k, r in ex.map(run, jobs) if r}
    print(f"{len(results)} item/store checks", file=sys.stderr)

    by_sku = {it["sku"]: it for it in items}
    rows = []
    for (sku, sid), r in results.items():
        if r["status"] == "ACTIVE":
            continue
        it, st = by_sku[sku], stores[sid]
        row = dict(store=st["name"], store_id=sid, miles=st["miles"], sku=sku, name=it["name"],
                   seen=it["seen"], states=it["states"], il_cities=it["il_cities"], **r)
        row["pct_off"] = round(100 * (1 - r["clearance"] / r["price"])) if r["clearance"] and r["price"] else ""
        row["score"] = score(row, today)
        rows.append(row)
    rows.sort(key=lambda r: (r["miles"], r["store"], -r["score"]))

    fields = ["store", "store_id", "miles", "score", "sku", "name", "status", "qty", "price",
              "clearance", "pct_off", "seen", "il_cities", "states"]
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} leads to {args.out}", file=sys.stderr)

    if args.board:
        build_board(HERE / "board_template.html", args.board, cfg["areas"], list(stores.values()),
                    items, results, today)
        print(f"wrote board to {args.board}", file=sys.stderr)


if __name__ == "__main__":
    main()
