# Penny Hunt

Checks the latest Home Depot penny reports against the stores near you, and builds the Penny Hunt Board page from the results.

Each run:
1. Pulls recent $0.01 reports from [PennyCentral's penny list](https://www.pennycentral.com/penny-list), plus any SKUs added by hand in `skus_extra.tsv`.
2. Finds the Home Depot stores around each area in `config.json`.
3. Checks every item at every store: the store's status (`CLEARANCE`, `INACTIVE`, `DELETED` or `ACTIVE`), the in-store quantity the website shows, and any store clearance price.
4. Writes a CSV of leads ranked by store. With `--board`, it also writes the board page.

A penny price never appears online. Treat every lead as a reason to go look, then confirm by scanning the product's UPC at self-checkout.

## Run it

Needs Python 3.9+ and nothing else.

```sh
python3 penny_scan.py                                   # leads CSV only
python3 penny_scan.py --board penny-hunt-board.html     # CSV + board page
```

A run of about 95 items across 16 stores makes about 1,500 requests and takes about 6 minutes. A few runs a week is plenty.

## Settings

`config.json`:
- `areas`: the ZIP codes to search around, with a radius in miles and a label for the board. A 50-mile radius around 61761 reaches Normal, Peoria and Champaign. A 12-mile radius around 60645 covers 13 Chicago-area stores.
- `max_age_days`: drop reports last seen longer ago than this.
- `extra_skus`: the file of hand-added SKUs.

`skus_extra.tsv` is for penny finds the feed doesn't have, for example from [Penny Pinchin' Mom](https://pennypinchinmom.com/home-depot-penny-list/). It has four tab-separated columns: store SKU, name, date last seen, and states.

## Reading the results

| Status | What it usually means |
|---|---|
| `CLEARANCE` + clearance price | Marked down at this store now. A good flip even if it never reaches a penny. |
| `CLEARANCE`, no stock showing | The app shows the item as unavailable. If one is still on a shelf, it's the most likely penny. |
| `INACTIVE` with stock | No longer a regular item, but units still show. Scan them. |
| `DELETED` | Removed from the store's system. Usually already pulled. |

These meanings come from how the statuses behave. Home Depot doesn't document them.

Before reselling anything, check [cpsc.gov/Recalls](https://www.cpsc.gov/Recalls).
