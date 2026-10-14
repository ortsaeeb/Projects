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
- `areas`: the ZIP codes to search around, with a radius in miles and a label for the board. A 10-mile radius around 61761 is just the Normal store, and 50 miles reaches Peoria and Champaign too. A 12-mile radius around 60645 covers 13 Chicago-area stores. Add `"paused": true` to an area to skip it (no scan, no Telegram posts) without losing its settings or its tab. `telegram_digest.py` follows these settings even when the board was built with wider ones.
- `max_age_days`: drop reports last seen longer ago than this.
- `extra_skus`: the file of hand-added SKUs.

`skus_extra.tsv` is for penny finds the feed doesn't have, for example from [Penny Pinchin' Mom](https://pennypinchinmom.com/home-depot-penny-list/). It has four tab-separated columns: store SKU, name, date last seen, and states.

## Telegram updates

`telegram_digest.py` turns a board page into messages you can read right in Telegram:
- **A header** with an optional summary. It's the only message that buzzes your phone.
- **Photo cards in two clearly labeled kinds:**
  - 🪙 **Penny chance**: the item rang up $0.01 at other stores, and at yours it's in clearance with no stock showing online. It might be a penny, and you find out by scanning it.
  - 🏷 **Clearance deal**: your store shows a real markdown price. It's a good flip, but not a penny.

  Each card has the SKU and model number to tap-copy. Its buttons open the **Home Depot** page, **eBay sold** listings for that model, and **directions** to the store.
- **Every lead as a compact list** in the same two groups, pinned to the top of the chat.

```sh
python3 penny_scan.py --board new.html
python3 telegram_digest.py --board new.html --prev old.html --summary-file summary.txt
python3 telegram_digest.py --board new.html --dry-run    # preview without sending
```

With `--prev` (the previous board), cards only cover what changed: new items, new or lower clearance prices, and new Illinois reports. Messages are grouped by area, in the order the areas appear in `config.json`, so put the area you're in most first. Clearance and penny prices only apply at the store that has the item. Each area gets up to `--penny-cards` (default 3) penny chances and `--deal-cards` (default 2) clearance deals, and leads at a store within 15 miles rank higher. Cards skip items under `--min-retail` (default $25), but the pinned list still shows them.

### Recall check

Before sending, `telegram_digest.py` checks every item against the CPSC recall database (`recall_check.py`).
- Each card shows ✅ **No CPSC recall found**, or ⚠️ **RECALLED: don't buy this to resell** with a button to the recall notice.
- Recalled items are also flagged in the pinned list.
- An item only counts as recalled when its UPC is listed in a recall, or its model number appears in a recall's text. Short or all-digit model numbers also need the brand named in the same recall.

The CPSC database is slow and sometimes returns empty results, so older recalls come from a saved copy, `recalls_snapshot.json.gz`, and only the last couple of months are downloaded each run. Refresh the saved copy now and then with `python3 recall_check.py --refresh-snapshot`.

If the download runs past 5 minutes, the run moves on, and cards say the recall check didn't finish instead of showing a false "no recall". Use `--no-recall-check` to skip the check.

### One tab per area (Telegram Topics)

In a Telegram group with **Topics** turned on, each area gets its own tab with its own cards and pinned list. The **General** tab gets the daily summary, with buttons that jump to each area's tab. To set it up:

1. Create a group, add the bot, and turn on **Topics** in the group settings.
2. Make the bot an admin with **Manage Topics** and **Pin Messages**, then send any message in the group.
3. Within 24 hours, run `python3 telegram_digest.py --setup-topics` with the bot token set. It creates the tabs and prints a `"telegram"` block, for example `{"chat_id": "-100…", "topics": {"61761": 2, "60645": 4}}`.
4. Add that block to `config.json`. From then on, the digest posts to the group's tabs instead of the private chat.

`notify_telegram.py` sends a plain message read from stdin:

```sh
echo "3 new leads at Evanston" | python3 notify_telegram.py
```

It reads two environment variables:
- `TELEGRAM_BOT_TOKEN`: from @BotFather. Required.
- `TELEGRAM_CHAT_ID`: your chat id. Optional. If it's missing, the script uses the chat of the last message you sent the bot within 24 hours, and prints the id so you can save it.

Set them in the cloud environment's settings, never in this repo. If there's no token, the script sends nothing and exits with code 3.

## Reading the results

| Status | What it usually means |
|---|---|
| `CLEARANCE` + clearance price | Marked down at this store now. A good flip even if it never reaches a penny. |
| `CLEARANCE`, no stock showing | The app shows the item as unavailable. If one is still on a shelf, it's the most likely penny. |
| `INACTIVE` with stock | No longer a regular item, but units still show. Scan them. |
| `DELETED` | Removed from the store's system. Usually already pulled. |

These meanings come from how the statuses behave. Home Depot doesn't document them.

Before reselling anything, check [cpsc.gov/Recalls](https://www.cpsc.gov/Recalls).
