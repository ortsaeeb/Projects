# Penny Hunt

Checks Home Depot items that shoppers have reported ringing up at $0.01 against the stores near you. For each store and item it reports:

- the store's status for the item: `CLEARANCE`, `INACTIVE`, `DELETED` or `ACTIVE`
- the in-store quantity the website shows
- any store clearance price

The output is a CSV of leads ranked for each store.

A penny price never appears online. Treat every lead as a reason to go look, then confirm by scanning the product's UPC at self-checkout.

## Run it

Needs Python 3.9+ and nothing else.

```sh
python3 penny_scan.py --zip 61761 --zip 60645 --radius 10
```

- `--radius` is the store search radius in miles. Ten miles around 60645 covers about 11 Chicago-area stores. Around 61761 you need about 50 to also reach Peoria and Champaign.
- `--skus` points at the list of SKUs to check (default `skus.tsv`).
- `--out` sets the CSV path (default `penny_leads.csv`).

A run of about 100 SKUs across 15 stores makes about 1,500 requests and takes about 5 minutes. Running it once a week is plenty.

## Refresh the SKU list

`skus.tsv` has four tab-separated columns: SKU, name, where and when it was reported, and states. To refresh it, copy recent finds from:

- [PennyCentral penny list](https://www.pennycentral.com/penny-list)
- [Penny Pinchin' Mom](https://pennypinchinmom.com/home-depot-penny-list/)

Prefer recent reports, and especially Illinois ones.

## Reading the results

| Status | What it usually means |
|---|---|
| `CLEARANCE` + clearance price | Marked down at this store now. A good flip even if it never reaches a penny. |
| `CLEARANCE`, no stock showing | The app shows the item as unavailable. If one is still on a shelf, it's the most likely penny. |
| `INACTIVE` with stock | No longer a regular item, but units still show. Scan them. |
| `DELETED` | Removed from the store's system. Usually already pulled. |

These meanings come from how the statuses behave. Home Depot doesn't document them.

Before reselling anything, check [cpsc.gov/Recalls](https://www.cpsc.gov/Recalls).
