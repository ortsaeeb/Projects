"""Check items against the CPSC recall database (saferproducts.gov).

Downloads every recall since 2018 (a year at a time, splitting any range the
service answers with an empty list) and matches locally, because its own UPC
and model searches miss recalls whose numbers only appear in the notice text.

An item counts as recalled only on an exact match:
  - its UPC is listed in a recall, or
  - its model number appears in a recall's text (for short or all-digit model
    numbers, only when the brand is named in the same recall).
Same-brand recalls for other products are ignored.

    from recall_check import check_items
    check_items([{"s": "1007712596", "brand": "Milwaukee", "model": "48-22-8445", "upc": "045242617593"}])
    -> {"1007712596": {"status": "clear"}}

status is "clear", "recalled" (with title, date and url) or "unknown" (some of
the database couldn't be downloaded and nothing matched in the rest).
"""
import gzip
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from http.client import HTTPException
from pathlib import Path

API = "https://www.saferproducts.gov/RestWebServices/Recall?format=json&"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")
SINCE_YEAR = 2018
SNAPSHOT = Path(__file__).resolve().parent / "recalls_snapshot.json.gz"
# How brands appear in recall notices when it differs from Home Depot's spelling.
ALIASES = {
    "BLACK+DECKER": ["black & decker", "black+decker", "black and decker"],
    "RYOBI": ["ryobi"],
    "DEWALT": ["dewalt"],
}


def _range(start, end, timeout=90):
    """Recalls dated start..end, or None if the service didn't answer."""
    url = API + urllib.parse.urlencode({"RecallDateStart": start, "RecallDateEnd": end})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
                data = json.loads(r.read() or b"[]") or []
            # The service answers "no results" with one blank record.
            return [rec for rec in data if rec and rec.get("RecallNumber")]
        except (urllib.error.URLError, HTTPException, ConnectionError, TimeoutError, ValueError):
            time.sleep(3 * (attempt + 1))
    return None


def _fetch_split(first, last, missing, deadline):
    """Recalls dated first..last. The service sometimes answers a range that has
    recalls with an empty list, so an empty range is split in half until the
    pieces answer or are single days. Ranges that never answer, or that come up
    after the deadline, go in missing."""
    if time.monotonic() > deadline:
        missing.append(f"{first}..{last}")
        return []
    batch = _range(first.isoformat(), last.isoformat())
    if batch is None:
        missing.append(f"{first}..{last}")
        return []
    if batch or first == last:
        return batch
    mid = first + (last - first) // 2
    return (_fetch_split(first, mid, missing, deadline)
            + _fetch_split(mid + timedelta(days=1), last, missing, deadline))


def load_recalls(since_year=SINCE_YEAR, snapshot=SNAPSHOT, overlap_days=60, budget_s=300):
    """All recalls since since_year, plus any date ranges that couldn't be downloaded.

    Older recalls come from the saved snapshot when there is one, so only the
    last couple of months are downloaded live. Downloading stops after budget_s
    seconds; whatever is left counts as missing, so items read "unknown" rather
    than holding up the daily update."""
    deadline = time.monotonic() + budget_s
    today = date.today()
    recalls, missing = {}, []
    start = date(since_year, 1, 1)
    if snapshot and Path(snapshot).exists():
        saved = json.loads(gzip.decompress(Path(snapshot).read_bytes()))
        for rec in saved["recalls"]:
            recalls[rec["RecallNumber"]] = rec
        start = max(start, date.fromisoformat(saved["through"]) - timedelta(days=overlap_days))
    for year in range(start.year, today.year + 1):
        first = max(start, date(year, 1, 1))
        for rec in _fetch_split(first, min(date(year, 12, 31), today), missing, deadline):
            recalls[rec["RecallNumber"]] = rec
    return list(recalls.values()), missing


def save_snapshot(recalls, through, path=SNAPSHOT):
    """Keep only what matching needs, gzipped, so the repo copy stays small."""
    slim = [{"RecallNumber": r["RecallNumber"], "RecallDate": r.get("RecallDate"), "Title": r.get("Title"),
             "URL": r.get("URL"), "Description": r.get("Description"),
             "Products": [{k: p.get(k) for k in ("Name", "Model", "Description", "Type")} for p in r.get("Products") or []],
             "ProductUPCs": [{"UPC": u.get("UPC")} for u in r.get("ProductUPCs") or []]}
            for r in recalls]
    Path(path).write_bytes(gzip.compress(json.dumps({"through": str(through), "recalls": slim}).encode(), 9))


def _digits(s):
    return re.sub(r"\D", "", s or "")


def _text(rec):
    parts = [rec.get("Title") or "", rec.get("Description") or ""]
    for p in rec.get("Products") or []:
        parts += [p.get("Name") or "", p.get("Model") or "", p.get("Description") or "", p.get("Type") or ""]
    return " ".join(parts).lower()


def _summary(rec):
    return {"status": "recalled", "title": rec.get("Title") or "Recall",
            "date": (rec.get("RecallDate") or "")[:10], "url": rec.get("URL") or "https://www.cpsc.gov/Recalls"}


def check_items(items, recalls=None, missing=None):
    if recalls is None:
        recalls, missing = load_recalls()
    by_upc = {}
    for rec in recalls:
        for u in rec.get("ProductUPCs") or []:
            d = _digits(u.get("UPC"))
            if len(d) >= 11:
                by_upc.setdefault(d[-12:] if len(d) >= 12 else d, rec)
    texts = [(_text(rec), rec) for rec in recalls]

    def check(it):
        upc = _digits(it.get("upc"))[-12:]
        if upc and (upc in by_upc or upc[:11] in by_upc):
            return _summary(by_upc.get(upc) or by_upc[upc[:11]])
        model = (it.get("model") or "").strip().lower()
        if len(model) >= 4:
            weak = model.isdigit() or len(model) < 6
            brand = (it.get("brand") or "").strip()
            brand_names = ALIASES.get(brand, [brand.lower()]) if brand else []
            pattern = re.compile(r"(?<![a-z0-9])" + re.escape(model) + r"(?![a-z0-9])")
            for text, rec in texts:
                if pattern.search(text) and (not weak or any(b and b in text for b in brand_names)):
                    return _summary(rec)
        return {"status": "unknown" if missing else "clear"}

    return {it["s"]: check(it) for it in items}


if __name__ == "__main__":
    # Rebuild the saved snapshot: python3 recall_check.py --refresh-snapshot
    import sys
    if "--refresh-snapshot" in sys.argv:
        recalls, missing = load_recalls(snapshot=None, budget_s=7200)
        if missing:
            sys.exit(f"recall_check: couldn't download {missing}; snapshot not saved")
        save_snapshot(recalls, date.today())
        print(f"recall_check: saved {len(recalls)} recalls to {SNAPSHOT.name}")
