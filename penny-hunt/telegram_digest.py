#!/usr/bin/env python3
"""Send the day's Penny Hunt deals to Telegram, readable right in the chat.

Reads the board page that penny_scan.py built and sends:
  1. A short header (with an optional summary), which buzzes your phone.
  2. Photo cards in two clearly labeled kinds:
       🪙 PENNY CHANCE: rang up $0.01 elsewhere and sits in clearance at your
          stores with no stock showing. Might be a penny; scan it to find out.
       🏷 CLEARANCE DEAL: your store shows a real markdown price. Not a penny.
     Each card has the SKU to tap-copy and buttons for the Home Depot page,
     eBay sold prices and directions to the store.
  3. Every lead as a compact list in the same two groups, pinned to the top
     of the chat.
Everything after the header is sent silently.

With --prev (yesterday's board), cards only cover what changed: new items,
new or lower clearance prices, and new Illinois reports.

Usage:
    python3 telegram_digest.py --board new.html [--prev old.html] [--summary-file s.txt]
    python3 telegram_digest.py --board new.html --dry-run     # print instead of sending

Needs TELEGRAM_BOT_TOKEN (and ideally TELEGRAM_CHAT_ID), like notify_telegram.py.
"""
import argparse
import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote, quote_plus

BOARD_URL = "https://claude.ai/artifact/UXy1qhNygWumMsT6uvyKxd"
CAPTION_LIMIT = 1024
TEXT_LIMIT = 4000  # a little under Telegram's 4096 so chunk joins never spill over
MIN_DEAL_PCT = 0.4      # a markdown this deep or deeper counts as a deal
MIN_MARKDOWN_PCT = 0.2  # smaller "clearance" cuts aren't worth listing
WATCH_LIST_MAX = 30


def esc(s):
    return html.escape(str(s or ""), quote=False)


def money(v):
    return f"${v:,.2f}" if v is not None else "?"


def load_board(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<script id="hunt-data" type="application/json">(.*?)</script>', text, re.S)
    if not m:
        sys.exit(f"telegram_digest: no board data found in {path}")
    return json.loads(m.group(1))


def age_days(board, item):
    if not item.get("seen"):
        return None
    return (date.fromisoformat(board["checkedISO"]) - date.fromisoformat(item["seen"])).days


def age_text(days):
    if days is None:
        return "date unknown"
    return "today" if days <= 0 else "yesterday" if days == 1 else f"{days} days ago"


def value_points(retail):
    return 3 if retail >= 150 else 2 if retail >= 50 else 1


def find_leads(board):
    """Rank every item that's marked down or in clearance at one of the user's stores."""
    stores = {s["id"]: s for s in board["stores"]}
    leads = []
    for it in board["items"]:
        per = it.get("per")
        if not per:
            continue
        retail = it.get("p") or 0
        marked = sorted(((v[2], stores[sid]) for sid, v in per.items()
                         if v[2] and v[0] != "A" and sid in stores and retail
                         and v[2] <= (1 - MIN_MARKDOWN_PCT) * retail), key=lambda x: (x[0], x[1]["mi"]))
        clearance = sorted((stores[sid] for sid, v in per.items() if v[0] == "C" and sid in stores),
                           key=lambda s: s["mi"])
        inactive = sorted(((stores[sid], v[1]) for sid, v in per.items()
                           if v[0] == "i" and v[1] > 0 and sid in stores), key=lambda x: x[0]["mi"])
        days = age_days(board, it)
        il = 2 if it.get("il") else 0
        pct = 1 - marked[0][0] / retail if marked and retail else 0
        if pct >= MIN_DEAL_PCT:
            kind, score = "deal", 10 * pct + value_points(retail) + il
        elif clearance or inactive:
            recent = 1.5 if days is not None and days <= 2 else 0.75 if days is not None and days <= 10 else 0
            kind, score = "watch", value_points(retail) + recent + il + (1 if inactive else 0)
        else:
            continue
        leads.append(dict(item=it, kind=kind, score=score, pct=pct, marked=marked, clearance=clearance,
                          inactive=inactive, days=days))
    leads.sort(key=lambda l: -l["score"])
    return leads


def change_note(lead, prev_items):
    """Why this lead is news compared with the previous board, or None."""
    it = lead["item"]
    prev = prev_items.get(it["s"])
    if prev is None:
        return "🆕 New penny report"
    if lead["kind"] == "deal":
        prev_prices = [v[2] for v in (prev.get("per") or {}).values() if v[2] and v[0] != "A"]
        best = lead["marked"][0][0]
        if not prev_prices:
            return "🔥 New markdown"
        if best < min(prev_prices) - 0.009:
            return f"📉 Price drop from {money(min(prev_prices))}"
    new_il = set(filter(None, (it.get("il") or "").split(", "))) - set(filter(None, (prev.get("il") or "").split(", ")))
    if new_il:
        return "📍 New Illinois report: " + ", ".join(sorted(new_il))
    return None


def short(name, limit=60):
    return name if len(name) <= limit else name[:limit - 1].rstrip() + "…"


def store_names(stores, limit=3):
    names = [s["n"] for s in stores[:limit]]
    more = len(stores) - limit
    return ", ".join(names) + (f" +{more} more" if more > 0 else "")


def product_url(it):
    url = it.get("url")
    return f"https://www.homedepot.com{url}" if url and url.startswith("/") else f"https://www.homedepot.com/s/{it['s']}"


def ebay_sold_url(it):
    query = f"{it.get('brand', '')} {it['model']}".strip() if it.get("model") else it["n"]
    return f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}&LH_Sold=1&LH_Complete=1"


def directions_url(store):
    return "https://www.google.com/maps/dir/?api=1&destination=" + quote(f"The Home Depot, {store['a']}")


PENNY_BADGE = "🪙 <b>PENNY CHANCE</b> · may ring up $0.01"
DEAL_BADGE = "🏷 <b>CLEARANCE DEAL</b> · marked down, not a penny"


def card(lead, note):
    """Caption and buttons for one deal card."""
    it = lead["item"]
    lines = [PENNY_BADGE if lead["kind"] == "watch" else DEAL_BADGE]
    if note:
        lines.append(f"<i>{esc(note)}</i>")
    lines.append(f"<b>{esc(it['n'])}</b>")
    il = f" · IL: {esc(it['il'])}" if it.get("il") else ""
    if lead["kind"] == "deal":
        best = lead["marked"][0][0]
        at_best = [s for p, s in lead["marked"] if p == best]
        others = [(p, s) for p, s in lead["marked"] if p != best]
        lines.append(f"💲 <b>{money(best)}</b>  <s>{money(it.get('p'))}</s>  −{round(lead['pct'] * 100)}%")
        lines.append(f"📍 {esc(store_names(at_best))}")
        if others:
            lines.append(f"     also {esc(store_names([s for _, s in others], 2))} from {money(others[0][0])}")
        lines.append(f"ℹ️ Rang up $0.01 at other stores ({age_text(lead['days'])}{il}), so this price may keep dropping.")
        target = at_best[0]
    else:
        lines.append(f"💲 Retail {money(it.get('p'))} · rang up <b>$0.01</b> elsewhere {age_text(lead['days'])}{il}")
        if lead["clearance"]:
            lines.append(f"📍 In clearance, none showing online: {esc(store_names(lead['clearance']))}")
        if lead["inactive"]:
            lines.append("📦 Still shows stock: " + esc(", ".join(f"{s['n']} ({q})" for s, q in lead["inactive"][:3])))
        lines.append("👉 Find it on the shelf and scan the box barcode at self-checkout.")
        target = (lead["clearance"] or [s for s, _ in lead["inactive"]])[0]
    ids = f"🔢 SKU <code>{esc(it['s'])}</code>"
    if it.get("model"):
        ids += f" · Model <code>{esc(it['model'])}</code>"
    lines.append(ids)
    caption = "\n".join(lines)
    if len(caption) > CAPTION_LIMIT:
        caption = caption[:CAPTION_LIMIT - 1] + "…"
    buttons = [
        [{"text": "🛒 Home Depot", "url": product_url(it)}, {"text": "💰 eBay sold", "url": ebay_sold_url(it)}],
        [{"text": f"🗺 Directions · {target['n']}", "url": directions_url(target)}],
    ]
    return caption, buttons


def list_lines(board, leads):
    """Every lead, one line each, for the pinned list."""
    lines = [f"📋 <b>Every lead · {esc(board['checked'])}</b>",
             "Tap a name for the Home Depot page, tap a SKU to copy it."]
    deals = [l for l in leads if l["kind"] == "deal"]
    watch = [l for l in leads if l["kind"] == "watch"][:WATCH_LIST_MAX]
    if watch:
        lines += ["", "🪙 <b>PENNY CHANCES</b>: may ring up $0.01. Scan to find out."]
        for l in watch:
            it = l["item"]
            where = f"{len(l['clearance'])} stores" if len(l["clearance"]) > 1 else (
                l["clearance"][0]["n"] if l["clearance"] else "in stock, inactive")
            il = f" · IL: {esc(it['il'])}" if it.get("il") else ""
            lines.append(f"• <a href=\"{esc(product_url(it))}\">{esc(short(it['n']))}</a> {money(it.get('p'))} · "
                         f"{esc(where)}{il} <code>{esc(it['s'])}</code>")
    if deals:
        lines += ["", "🏷 <b>CLEARANCE DEALS</b>: marked-down price, not a penny."]
        for l in deals:
            it, (best, store) = l["item"], l["marked"][0]
            lines.append(f"• <b>{money(best)}</b> −{round(l['pct'] * 100)}% "
                         f"<a href=\"{esc(product_url(it))}\">{esc(short(it['n']))}</a> · {esc(store['n'])} "
                         f"<code>{esc(it['s'])}</code>")
    gone = [it for it in board["items"] if not it.get("per")]
    if gone:
        lines += ["", "👀 <b>NOT ON THE WEBSITE</b>: pennied elsewhere, look on shelves."]
        for it in gone:
            lines.append(f"• {esc(short(it['n']))} <code>{esc(it['s'])}</code>")
    return lines


def visible_len(text):
    """Length as Telegram counts it: tags and link targets don't count."""
    return len(html.unescape(re.sub(r"<[^>]+>", "", text)))


def chunk(lines, limit=TEXT_LIMIT):
    chunks, cur, cur_len = [], "", 0
    for line in lines:
        n = visible_len(line)
        if cur and cur_len + 1 + n > limit:
            chunks.append(cur)
            cur, cur_len = line, n
        else:
            cur, cur_len = (f"{cur}\n{line}", cur_len + 1 + n) if cur else (line, n)
    if cur:
        chunks.append(cur)
    return chunks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board", required=True, help="the new board page from penny_scan.py --board")
    ap.add_argument("--prev", help="the previous board page, to send cards only for what changed")
    ap.add_argument("--summary-file", help="plain-text summary to put in the header")
    ap.add_argument("--penny-cards", type=int, default=4, help="most penny-chance cards to send (default 4)")
    ap.add_argument("--deal-cards", type=int, default=3, help="most clearance-deal cards to send (default 3)")
    ap.add_argument("--min-retail", type=float, default=25,
                    help="only send cards for items retailing at least this much (default $25)")
    ap.add_argument("--board-url", default=BOARD_URL)
    ap.add_argument("--dry-run", action="store_true", help="print the messages instead of sending them")
    args = ap.parse_args()

    board = load_board(args.board)
    leads = find_leads(board)
    card_leads = [l for l in leads if (l["item"].get("p") or 0) >= args.min_retail]
    if args.prev and Path(args.prev).exists():
        prev_items = {it["s"]: it for it in load_board(args.prev)["items"]}
        candidates = [(l, n) for l in card_leads if (n := change_note(l, prev_items))]
    else:
        candidates = [(l, None) for l in card_leads]
    pennies = [c for c in candidates if c[0]["kind"] == "watch"][:args.penny_cards]
    deal_cards = [c for c in candidates if c[0]["kind"] == "deal"][:args.deal_cards]
    picked = pennies + deal_cards

    summary = Path(args.summary_file).read_text(encoding="utf-8").strip() if args.summary_file else ""
    deals = sum(1 for l in leads if l["kind"] == "deal")
    watch = sum(1 for l in leads if l["kind"] == "watch")
    header = [f"🔨 <b>Penny Hunt</b> · {esc(board['checked'])}"]
    if summary:
        header.append(esc(summary))
    new = "new " if args.prev else ""
    if picked:
        header.append(f"👇 <b>{len(pennies)}</b> {new}penny chance{'s' if len(pennies) != 1 else ''} · "
                      f"<b>{len(deal_cards)}</b> {new}clearance deal{'s' if len(deal_cards) != 1 else ''}")
    else:
        header.append("Nothing new since the last update.")
    header.append("🪙 = may ring up $0.01, scan to check · 🏷 = marked-down price, not a penny")
    header.append(f"📌 Pinned list: all {watch} penny chances and {deals} clearance deals.")
    header_text = "\n".join(header)[:TEXT_LIMIT]
    cards = [card(l, n) for l, n in picked]
    lists = chunk(list_lines(board, leads))

    if args.dry_run:
        print(header_text, "\n" + "=" * 40)
        for caption, buttons in cards:
            print(caption, "\n  buttons:", " | ".join(b["text"] for row in buttons for b in row), "\n" + "-" * 40)
        for part in lists:
            print(part, "\n" + "=" * 40)
        print(f"{len(cards)} cards, {len(lists)} list message(s)", file=sys.stderr)
        return

    from telegram_api import Bot, NotConfigured, TelegramError
    try:
        bot = Bot()
        bot.send_message(header_text, buttons=[[{"text": "📋 Open the full board", "url": args.board_url}]])
        for (caption, buttons), (lead, _) in zip(cards, picked):
            time.sleep(0.4)
            img = lead["item"].get("img")
            try:
                if not img:
                    raise TelegramError("no photo")
                bot.send_photo(img, caption, buttons, silent=True)
            except TelegramError:  # photo missing or Telegram couldn't fetch it: send the text alone
                bot.send_message(caption, buttons, silent=True)
        first = None
        for part in lists:
            time.sleep(0.4)
            msg = bot.send_message(part, silent=True)
            first = first or msg
        if first:
            try:
                bot.pin(first["message_id"])
            except TelegramError as e:
                print(f"telegram_digest: couldn't pin the list ({e})", file=sys.stderr)
    except NotConfigured as e:
        print(f"telegram_digest: not set up, {e}; nothing sent", file=sys.stderr)
        sys.exit(3)
    except TelegramError as e:
        sys.exit(f"telegram_digest: {e}")
    print(f"telegram_digest: sent header, {len(pennies)} penny-chance and {len(deal_cards)} clearance-deal cards, "
          f"{len(lists)} list message(s)", file=sys.stderr)
    if bot.found_chat_id:
        print(f"telegram_digest: found your chat ID {bot.chat_id} from your last message to the bot. "
              f"Save TELEGRAM_CHAT_ID={bot.chat_id} in the environment so updates keep working; "
              "the bot only remembers messages for 24 hours.", file=sys.stderr)


if __name__ == "__main__":
    main()
