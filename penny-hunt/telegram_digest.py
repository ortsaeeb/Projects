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
Cards and the list are grouped by area (config.json order, main area first),
since clearance and penny prices only apply at the store that has the item.
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
NEARBY_MILES = 15       # leads at a store this close rank higher
WATCH_LIST_MAX = 20  # penny-chance lines per area in the pinned list


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
            near = 1.5 if min(s["mi"] for _, s in marked) <= NEARBY_MILES else 0
            kind, score = "deal", 10 * pct + value_points(retail) + il + near
        elif clearance or inactive:
            recent = 1.5 if days is not None and days <= 2 else 0.75 if days is not None and days <= 10 else 0
            near = 1.5 if min(s["mi"] for s in clearance + [s for s, _ in inactive]) <= NEARBY_MILES else 0
            kind, score = "watch", value_points(retail) + recent + il + (1 if inactive else 0) + near
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


def recall_line(recall, checked):
    if not recall:
        return None
    if recall["status"] == "recalled":
        return f"⚠️ <b>Recall:</b> {esc(recall['title'])} ({esc(recall['date'])})"
    if recall["status"] == "clear":
        return f"✅ No CPSC recall found (checked {esc(checked)})"
    return "❔ Recall check didn't finish today. Check cpsc.gov/Recalls before reselling."


def card(lead, note, recall=None, checked=""):
    """Caption and buttons for one deal card."""
    it = lead["item"]
    lines = [PENNY_BADGE if lead["kind"] == "watch" else DEAL_BADGE]
    if recall and recall["status"] == "recalled":
        lines.insert(0, "⚠️ <b>RECALLED: don't buy this to resell</b>")
    if note:
        lines.append(f"<i>{esc(note)}</i>")
    lines.append(f"<b>{esc(it['n'])}</b>")
    il = f" · IL: {esc(it['il'])}" if it.get("il") else ""
    if lead["kind"] == "deal":
        best = lead["marked"][0][0]
        at_best = [s for p, s in lead["marked"] if p == best]
        others = [(p, s) for p, s in lead["marked"] if p != best]
        lines.append(f"💲 <b>{money(best)} in store</b>  <s>{money(it.get('p'))}</s>  −{round(lead['pct'] * 100)}%")
        lines.append(f"🌐 Website still shows {money(it.get('p'))}. Clearance prices are in-store only.")
        lines.append(f"📍 {esc(store_names(at_best))}")
        if others:
            lines.append(f"     also {esc(store_names([s for _, s in others], 2))} from {money(others[0][0])}")
        lines.append(f"ℹ️ Rang up $0.01 at other stores ({age_text(lead['days'])}{il}), so this price may keep dropping.")
        target = at_best[0]
    else:
        lines.append(f"💲 Retail {money(it.get('p'))} (the website shows full price) · rang up <b>$0.01</b> "
                     f"elsewhere {age_text(lead['days'])}{il}")
        if lead["clearance"]:
            lines.append(f"📍 In clearance, none showing online: {esc(store_names(lead['clearance']))}")
        if lead["inactive"]:
            lines.append("📦 Still shows stock: " + esc(", ".join(f"{s['n']} ({q})" for s, q in lead["inactive"][:3])))
        lines.append("👉 Find it on the shelf and scan the box barcode at self-checkout.")
        target = (lead["clearance"] or [s for s, _ in lead["inactive"]])[0]
    if recall_line(recall, checked):
        lines.append(recall_line(recall, checked))
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
    if recall and recall["status"] == "recalled":
        buttons.insert(0, [{"text": "⚠️ Read the recall notice", "url": recall["url"]}])
    return caption, buttons


def area_board(board, zip_code):
    """The board narrowed to one area's stores."""
    ids = {s["id"] for s in board["stores"] if s.get("r") == zip_code}
    items = []
    for it in board["items"]:
        per = {sid: v for sid, v in (it.get("per") or {}).items() if sid in ids}
        items.append({**it, "per": per} if per else {k: v for k, v in it.items() if k != "per"})
    return {**board, "stores": [s for s in board["stores"] if s["id"] in ids], "items": items}


def area_line(area, stores, limit=3):
    shown = " · ".join(f"{s['n']} {s['mi']:g} mi" for s in stores[:limit])
    more = f" · +{len(stores) - limit} more" if len(stores) > limit else ""
    return f"📍 <b>{esc(area['label'].upper())}</b> · {esc(shown + more)}"


def area_list_lines(sec, title=None, kinds=("watch", "deal")):
    """One area's leads, one line each, for its pinned list (only the given kinds)."""
    deals = [l for l in sec["leads"] if l["kind"] == "deal"] if "deal" in kinds else []
    watch = [l for l in sec["leads"] if l["kind"] == "watch"] if "watch" in kinds else []
    lines = [title] if title else []
    lines.append(area_line(sec["area"], sec["stores"]))
    both = "watch" in kinds and "deal" in kinds
    if watch:
        more = f" Top {WATCH_LIST_MAX} of {len(watch)}." if len(watch) > WATCH_LIST_MAX else ""
        if both:
            lines.append(DIVIDER)
        lines.append(f"🪙 <b>PENNY CHANCES</b>: price unknown until you scan. Could be $0.01. "
                     f"The price shown is regular retail.{more}")
        for l in watch[:WATCH_LIST_MAX]:
            it = l["item"]
            flag = "⚠️ RECALLED " if sec.get("recalls", {}).get(it["s"], {}).get("status") == "recalled" else ""
            # Name the stores: an area tab covers several, and the item may not be in clearance at all of them.
            where = (f"in clearance at {store_names(l['clearance'])}" if l["clearance"] else
                     f"phasing out, stock showing at {store_names([s for s, _ in l['inactive']])}")
            il = f" · IL: {esc(it['il'])}" if it.get("il") else ""
            lines.append(f"• {flag}<a href=\"{esc(product_url(it))}\">{esc(short(it['n']))}</a> · "
                         f"retail {money(it.get('p'))}, may ring <b>$0.01</b> · {esc(where)}{il} "
                         f"<code>{esc(it['s'])}</code>")
    if deals:
        if both:
            lines += ["", DIVIDER]
        lines.append("🏷 <b>CLEARANCE DEALS</b>: the store's current marked-down price, in-store only "
                     "(the website shows full price). Not a penny.")
        for l in deals:
            it, (best, store) = l["item"], l["marked"][0]
            flag = "⚠️ RECALLED " if sec.get("recalls", {}).get(it["s"], {}).get("status") == "recalled" else ""
            lines.append(f"• {flag}<b>{money(best)}</b> (was {money(it.get('p'))}, −{round(l['pct'] * 100)}%) "
                         f"<a href=\"{esc(product_url(it))}\">{esc(short(it['n']))}</a> · at {esc(store['n'])} "
                         f"<code>{esc(it['s'])}</code>")
    if not watch and not deals:
        lines.append({("watch",): "No penny chances at these stores right now.",
                      ("deal",): "No clearance deals at these stores right now."}.get(
                          tuple(kinds), "Nothing on the penny lists is in clearance at these stores right now."))
    return lines


DIVIDER = "━━━━━━━━━━━━━━━━━━"
PENNY_BANNER = f"{DIVIDER}\n🪙🪙 <b>PENNIES</b> 🪙🪙\nMay ring up $0.01. Scan the box barcode to find out.\n{DIVIDER}"
DEALS_BANNER = f"{DIVIDER}\n🏷🏷 <b>DEALS</b> 🏷🏷\nReal in-store clearance prices. Not pennies.\n{DIVIDER}"
PENNY_TAB_NOTE = "🪙 <b>PENNIES</b>: items that may ring up $0.01 here. Scan the box barcode to find out."
DEALS_TAB_NOTE = "🏷 <b>DEALS</b>: real in-store clearance prices (the website shows full price). Not pennies."


def tab_ids(topics, zip_code):
    """{"penny": thread, "deals": thread} for an area. An older setup with one tab per area uses it for both."""
    t = topics.get(zip_code)
    return {"penny": t, "deals": t} if isinstance(t, int) else (t or {})


def gone_lines(board):
    gone = [it for it in board["items"] if not it.get("per")]
    if not gone:
        return []
    lines = ["👀 <b>NOT ON THE WEBSITE</b>: rang up $0.01 elsewhere, but Home Depot's site has no price or "
             "stock for it. Scan any you spot on a shelf."]
    lines += [f"• {esc(short(it['n']))} <code>{esc(it['s'])}</code>" for it in gone]
    return lines


def list_title(board):
    return (f"📋 <b>Every lead · {esc(board['checked'])}</b>\n"
            "Tap a name for the Home Depot page, tap a SKU to copy it.")


def list_lines(board, sections):
    """Every lead for every area, for the pinned list in a one-chat setup."""
    lines = [list_title(board)]
    for sec in sections:
        lines += [""] + area_list_lines(sec)
    gone = gone_lines(board)
    return lines + ([""] + gone if gone else [])


# ---- Two-tab layout: one 🪙 Pennies tab and one 🏷 Deals tab for all areas ----------------------

def by_area(board, pairs, key=lambda x: x):
    """Group stores (or (price, store) pairs) by area, in config order."""
    groups = {}
    for p in pairs:
        groups.setdefault(key(p)["r"], []).append(p)
    return [(a, groups[a["zip"]]) for a in board["areas"] if a["zip"] in groups]


def type_card(lead, note, recall, checked, board, short_names):
    """A card that lists the stores in every area, for the two-tab layout."""
    it = lead["item"]
    lines = [PENNY_BADGE if lead["kind"] == "watch" else DEAL_BADGE]
    if recall and recall["status"] == "recalled":
        lines.insert(0, "⚠️ <b>RECALLED: don't buy this to resell</b>")
    if note:
        lines.append(f"<i>{esc(note)}</i>")
    lines.append(f"<b>{esc(it['n'])}</b>")
    il = f" · IL: {esc(it['il'])}" if it.get("il") else ""
    targets = []
    if lead["kind"] == "deal":
        best = lead["marked"][0][0]
        lines.append(f"💲 <b>{money(best)} in store</b>  <s>{money(it.get('p'))}</s>  −{round(lead['pct'] * 100)}%")
        lines.append(f"🌐 Website still shows {money(it.get('p'))}. Clearance prices are in-store only.")
        for area, rows in by_area(board, lead["marked"], key=lambda r: r[1]):
            low = rows[0][0]
            at_low = [s for p, s in rows if p == low]
            more = len(rows) - len(at_low)
            lines.append(f"📍 <b>{esc(short_names[area['zip']])}</b>: {esc(store_names(at_low, 2))} {money(low)}"
                         + (f" · {more} more from {money(rows[len(at_low)][0])}" if more else ""))
            targets.append(at_low[0])
        lines.append(f"ℹ️ Rang up $0.01 at other stores ({age_text(lead['days'])}{il}), so this price may keep dropping.")
    else:
        lines.append(f"💲 Retail {money(it.get('p'))} (the website shows full price) · rang up <b>$0.01</b> "
                     f"elsewhere {age_text(lead['days'])}{il}")
        stores = sorted(lead["clearance"] + [s for s, _ in lead["inactive"]], key=lambda s: s["mi"])
        for area, group in by_area(board, stores):
            lines.append(f"📍 <b>{esc(short_names[area['zip']])}</b>: {esc(store_names(group))}")
            targets.append(group[0])
        if lead["inactive"]:
            lines.append("📦 Still shows stock: " + esc(", ".join(f"{s['n']} ({q})" for s, q in lead["inactive"][:3])))
        lines.append("👉 Find it on the shelf and scan the box barcode at self-checkout.")
    if recall_line(recall, checked):
        lines.append(recall_line(recall, checked))
    ids = f"🔢 SKU <code>{esc(it['s'])}</code>"
    if it.get("model"):
        ids += f" · Model <code>{esc(it['model'])}</code>"
    lines.append(ids)
    caption = "\n".join(lines)
    if len(caption) > CAPTION_LIMIT:
        caption = caption[:CAPTION_LIMIT - 1] + "…"
    buttons = [[{"text": "🛒 Home Depot", "url": product_url(it)}, {"text": "💰 eBay sold", "url": ebay_sold_url(it)}],
               [{"text": f"🗺 {s['n']}", "url": directions_url(s)} for s in targets[:2]]]
    if recall and recall["status"] == "recalled":
        buttons.insert(0, [{"text": "⚠️ Read the recall notice", "url": recall["url"]}])
    return caption, buttons


def type_list_lines(board, leads, kind, recalls, short_names):
    """Pinned list for the Pennies or Deals tab: each item once, with its stores by area."""
    recalled = lambda it: "⚠️ RECALLED " if (recalls.get(it["s"]) or {}).get("status") == "recalled" else ""
    lines = [list_title(board), ""]
    if kind == "watch":
        watch = [l for l in leads if l["kind"] == "watch"]
        more = f" Top {WATCH_LIST_MAX * 2} of {len(watch)}." if len(watch) > WATCH_LIST_MAX * 2 else ""
        lines.append(f"🪙 <b>PENNY CHANCES</b>: price unknown until you scan. Could be $0.01. "
                     f"The price shown is regular retail.{more}")
        for l in watch[:WATCH_LIST_MAX * 2]:
            it = l["item"]
            stores = l["clearance"] + [s for s, _ in l["inactive"]]
            where = " · ".join(f"{short_names[a['zip']]}: {g[0]['n'] if len(g) == 1 else f'{len(g)} stores'}"
                               for a, g in by_area(board, sorted(stores, key=lambda s: s["mi"])))
            il = f" · IL: {esc(it['il'])}" if it.get("il") else ""
            lines.append(f"• {recalled(it)}<a href=\"{esc(product_url(it))}\">{esc(short(it['n']))}</a> · "
                         f"retail {money(it.get('p'))} · {esc(where)}{il} <code>{esc(it['s'])}</code>")
        if not watch:
            lines.append("No penny chances at your stores right now.")
    else:
        deals = [l for l in leads if l["kind"] == "deal"]
        lines.append("🏷 <b>CLEARANCE DEALS</b>: the store's current marked-down price, in-store only "
                     "(the website shows full price). Not a penny.")
        for l in deals:
            it = l["item"]
            where = " · ".join(f"{short_names[a['zip']]}: {rows[0][1]['n']} {money(rows[0][0])}"
                               for a, rows in by_area(board, l["marked"], key=lambda r: r[1]))
            lines.append(f"• {recalled(it)}<b>{money(l['marked'][0][0])}</b> (was {money(it.get('p'))}, "
                         f"−{round(l['pct'] * 100)}%) <a href=\"{esc(product_url(it))}\">{esc(short(it['n']))}</a> · "
                         f"{esc(where)} <code>{esc(it['s'])}</code>")
        if not deals:
            lines.append("No clearance deals at your stores right now.")
    return lines


def send_by_type(args, board, prev, tg_cfg, cfg, summary):
    """Two-tab layout: every item once, in the 🪙 Pennies or 🏷 Deals tab, with its stores in each area."""
    short_names = {a["zip"]: a.get("short") or a["label"] for a in cfg.get("areas", [])}
    for a in board["areas"]:
        short_names.setdefault(a["zip"], a["label"])
    leads = find_leads(board)
    card_leads = [l for l in leads if (l["item"].get("p") or 0) >= args.min_retail]
    if prev:
        prev_items = {it["s"]: it for it in prev["items"]}
        candidates = [(l, n) for l in card_leads if (n := change_note(l, prev_items))]
    else:
        candidates = [(l, None) for l in card_leads]
    counts_cfg = tg_cfg.get("cards") or {}
    pennies = [c for c in candidates if c[0]["kind"] == "watch"][:counts_cfg.get("penny", 5)]
    deals = [c for c in candidates if c[0]["kind"] == "deal"][:counts_cfg.get("deals", 4)]

    recalls = {}
    if not args.no_recall_check:
        from recall_check import check_items
        recalls = check_items(board["items"])
        tally = {s: sum(1 for r in recalls.values() if r["status"] == s) for s in ("clear", "recalled", "unknown")}
        print(f"telegram_digest: recall check: {tally['clear']} clear, {tally['recalled']} recalled, "
              f"{tally['unknown']} couldn't be checked", file=sys.stderr)

    def cards(picked):
        return [(type_card(l, n, recalls.get(l["item"]["s"]), board["checked"], board, short_names),
                 l["item"].get("img")) for l, n in picked]

    new = "new " if prev else ""
    p, d = len(pennies), len(deals)
    tabs = [("watch", tg_cfg["topics"]["penny"], cards(pennies),
             f"{p} {new}penny chance{'s' if p != 1 else ''}", PENNY_TAB_NOTE),
            ("deal", tg_cfg["topics"]["deals"], cards(deals),
             f"{d} {new}clearance deal{'s' if d != 1 else ''}", DEALS_TAB_NOTE)]
    header = [f"🔨 <b>Penny Hunt</b> · {esc(board['checked'])}"]
    if summary:
        header.append(esc(summary))
    header.append(f"🪙 {tabs[0][3]} · 🏷 {tabs[1][3]}" if p or d or not prev else "Nothing new since the last update.")
    header.append("Stores: " + " · ".join(f"{short_names[a['zip']]} area" for a in board["areas"]))
    header.append("👇 Tap a tab below.")
    header_text = "\n".join(header)

    if args.dry_run:
        print("[two tabs: Pennies + Deals]")
        print(header_text, "\n" + "=" * 40)
        for kind, _, tab_cards, what, note in tabs:
            print(f"[tab {'Pennies' if kind == 'watch' else 'Deals'}] {what}")
            for (caption, buttons), _ in tab_cards:
                print(caption, "\n  buttons:", " | ".join(b["text"] for row in buttons for b in row), "\n" + "-" * 40)
            for part in chunk(type_list_lines(board, leads, kind, recalls, short_names)):
                print(part, "\n" + "=" * 40)
        if gone_lines(board):
            print("[General]", "\n".join(gone_lines(board)))
        print(f"{p + d} cards", file=sys.stderr)
        return

    from telegram_api import Bot, NotConfigured, TelegramError

    def send_list(bot, lines, thread):
        first = None
        for part in chunk(lines):
            time.sleep(0.4)
            msg = bot.send_message(part, silent=True, thread=thread)
            first = first or msg
        if first:
            try:
                bot.pin(first["message_id"], thread=thread)
            except TelegramError as e:
                print(f"telegram_digest: couldn't pin the list ({e})", file=sys.stderr)

    try:
        bot = Bot(chat_id=str(tg_cfg["chat_id"]))
        if args.list_only:
            for kind, thread, *_ in tabs:
                send_list(bot, type_list_lines(board, leads, kind, recalls, short_names), thread)
            print("telegram_digest: sent and pinned the full lists", file=sys.stderr)
            return
        buttons = [[{"text": f"🪙 Pennies ({p})", "url": bot.topic_link(tabs[0][1])},
                    {"text": f"🏷 Deals ({d})", "url": bot.topic_link(tabs[1][1])}],
                   [{"text": "📋 Open the full board", "url": args.board_url}]]
        bot.send_message(header_text, buttons=buttons)
        for kind, thread, tab_cards, what, note in tabs:
            time.sleep(0.4)
            bot.send_message(f"🔨 <b>{esc(board['checked'])}</b> · {what}\n{note}", silent=True, thread=thread)
            for (caption, btns), img in tab_cards:
                time.sleep(0.4)
                try:
                    if not img:
                        raise TelegramError("no photo")
                    bot.send_photo(img, caption, btns, silent=True, thread=thread)
                except TelegramError:  # photo missing or Telegram couldn't fetch it: send the text alone
                    bot.send_message(caption, btns, silent=True, thread=thread)
            send_list(bot, type_list_lines(board, leads, kind, recalls, short_names), thread)
        if gone_lines(board):
            time.sleep(0.4)
            bot.send_message("\n".join(gone_lines(board))[:TEXT_LIMIT], silent=True)
    except NotConfigured as e:
        print(f"telegram_digest: not set up, {e}; nothing sent", file=sys.stderr)
        sys.exit(3)
    except TelegramError as e:
        sys.exit(f"telegram_digest: {e}")
    print(f"telegram_digest: sent header, {p} penny-chance and {d} clearance-deal cards to the Pennies and Deals tabs",
          file=sys.stderr)


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
    ap.add_argument("--board", help="the new board page from penny_scan.py --board")
    ap.add_argument("--prev", help="the previous board page, to send cards only for what changed")
    ap.add_argument("--summary-file", help="plain-text summary to put in the header")
    ap.add_argument("--penny-cards", type=int, default=3, help="most penny-chance cards per area (default 3)")
    ap.add_argument("--deal-cards", type=int, default=2, help="most clearance-deal cards per area (default 2)")
    ap.add_argument("--min-retail", type=float, default=25,
                    help="only send cards for items retailing at least this much (default $25)")
    ap.add_argument("--board-url", default=BOARD_URL)
    ap.add_argument("--config", default=str(Path(__file__).resolve().parent / "config.json"),
                    help="config.json; its optional \"telegram\" block names the group and one tab per area")
    ap.add_argument("--setup-topics", action="store_true",
                    help="create fresh tabs in the group (removing old ones), then print the config block")
    ap.add_argument("--layout", choices=("area", "type"), default="area",
                    help="with --setup-topics: one tab per area (pennies and deals inside, default), or one "
                         "Pennies tab and one Deals tab for all areas")
    ap.add_argument("--list-only", action="store_true",
                    help="send and pin only the full list (no header or cards), e.g. to restore a missed list")
    ap.add_argument("--no-recall-check", action="store_true",
                    help="skip checking card items against the CPSC recall database")
    ap.add_argument("--dry-run", action="store_true", help="print the messages instead of sending them")
    args = ap.parse_args()
    if args.setup_topics:
        return setup_topics(args.config, args.layout)
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8")) if Path(args.config).exists() else {}
    tg_cfg = cfg.get("telegram") or {}
    short_names = {a["zip"]: a.get("short") or a["label"] for a in cfg.get("areas", [])}

    if not args.board:
        ap.error("--board is required")
    board = load_board(args.board)
    prev = load_board(args.prev) if args.prev and Path(args.prev).exists() else None
    for a in board["areas"]:
        short_names.setdefault(a["zip"], a["label"])
    if tg_cfg.get("layout") == "type":
        summary = Path(args.summary_file).read_text(encoding="utf-8").strip() if args.summary_file else ""
        return send_by_type(args, board, prev, tg_cfg, cfg, summary)

    # One section per area, in config order (the first area is the user's main one).
    sections = []
    for area in board["areas"]:
        sub = area_board(board, area["zip"])
        if not sub["stores"]:
            continue
        leads = find_leads(sub)
        card_leads = [l for l in leads if (l["item"].get("p") or 0) >= args.min_retail]
        if prev:
            prev_items = {it["s"]: it for it in area_board(prev, area["zip"])["items"]}
            candidates = [(l, n) for l in card_leads if (n := change_note(l, prev_items))]
        else:
            candidates = [(l, None) for l in card_leads]
        sections.append(dict(
            area=area, stores=sorted(sub["stores"], key=lambda s: s["mi"]), leads=leads,
            pennies=[c for c in candidates if c[0]["kind"] == "watch"][:args.penny_cards],
            deals=[c for c in candidates if c[0]["kind"] == "deal"][:args.deal_cards]))

    summary = Path(args.summary_file).read_text(encoding="utf-8").strip() if args.summary_file else ""
    new = "new " if prev else ""

    def counts(sec):
        p, d = len(sec["pennies"]), len(sec["deals"])
        return (f"{p} {new}penny chance{'s' if p != 1 else ''} · {d} {new}clearance deal{'s' if d != 1 else ''}"
                if p or d else "nothing new")

    header = [f"🔨 <b>Penny Hunt</b> · {esc(board['checked'])}"]
    if summary:
        header.append(esc(summary))
    header += [f"📍 {esc(sec['area']['label'])}: {counts(sec)}" for sec in sections]
    header.append("🪙 = may ring up $0.01, scan to check · 🏷 = marked-down price, not a penny")
    topics = {str(k): v for k, v in (tg_cfg.get("topics") or {}).items()}
    use_topics = bool(topics) and all(tab_ids(topics, sec["area"]["zip"]).get("penny") for sec in sections)
    header.append("👇 Tap a tab below." if use_topics else "📌 Every lead for each area is in the pinned list.")
    header_text = "\n".join(header)[:TEXT_LIMIT]

    recalls = {}
    if not args.no_recall_check:
        from recall_check import check_items
        recalls = check_items(board["items"])  # every item, so the pinned list can flag recalls too
        tally = {s: sum(1 for r in recalls.values() if r["status"] == s) for s in ("clear", "recalled", "unknown")}
        print(f"telegram_digest: recall check: {tally['clear']} clear, {tally['recalled']} recalled, "
              f"{tally['unknown']} couldn't be checked", file=sys.stderr)
    for sec in sections:
        sec["recalls"] = recalls
        sec["penny_cards"] = [(card(l, n, recalls.get(l["item"]["s"]), board["checked"]), l["item"].get("img"))
                              for l, n in sec["pennies"]]
        sec["deal_cards"] = [(card(l, n, recalls.get(l["item"]["s"]), board["checked"]), l["item"].get("img"))
                             for l, n in sec["deals"]]
        sec["cards"] = sec["penny_cards"] + sec["deal_cards"]
    n_cards = sum(len(sec["cards"]) for sec in sections)

    def tab_threads(sec):
        """(kinds, thread) for each tab an area posts to."""
        ids = tab_ids(topics, sec["area"]["zip"])
        if ids["penny"] == ids["deals"]:
            return [(("watch", "deal"), ids["penny"])]
        return [(("watch",), ids["penny"]), (("deal",), ids["deals"])]

    if args.dry_run:
        print(f"[{'group tabs' if use_topics else 'one chat'}]")
        print(header_text, "\n" + "=" * 40)
        for sec in sections:
            names = {("watch",): ("Pennies", sec["penny_cards"]), ("deal",): ("Deals", sec["deal_cards"])}
            groups = ([(*names.get(kinds, ("Pennies + Deals", sec["cards"])), kinds) for kinds, _ in tab_threads(sec)]
                      if use_topics else [(None, sec["cards"], ("watch", "deal"))])
            if not use_topics:
                print(area_line(sec["area"], sec["stores"]))
            for tab, cards, kinds in groups:
                if tab:
                    print(f"[tab {sec['area']['label']} · {tab}]")
                for (caption, buttons), _ in cards:
                    print(caption, "\n  buttons:", " | ".join(b["text"] for row in buttons for b in row), "\n" + "-" * 40)
                if use_topics:
                    for part in chunk([list_title(board), ""] + area_list_lines(sec, kinds=kinds)):
                        print(part, "\n" + "=" * 40)
        if not use_topics:
            for part in chunk(list_lines(board, sections)):
                print(part, "\n" + "=" * 40)
        elif gone_lines(board):
            print("[General]", "\n".join(gone_lines(board)))
        print(f"{n_cards} cards", file=sys.stderr)
        return

    from telegram_api import Bot, NotConfigured, TelegramError

    def send_cards(bot, cards, thread=None):
        for (caption, buttons), img in cards:
            time.sleep(0.4)
            try:
                if not img:
                    raise TelegramError("no photo")
                bot.send_photo(img, caption, buttons, silent=True, thread=thread)
            except TelegramError:  # photo missing or Telegram couldn't fetch it: send the text alone
                bot.send_message(caption, buttons, silent=True, thread=thread)

    def send_list(bot, lines, thread=None):
        first = None
        for part in chunk(lines):
            time.sleep(0.4)
            msg = bot.send_message(part, silent=True, thread=thread)
            first = first or msg
        if first:
            try:
                bot.pin(first["message_id"], thread=thread)
            except TelegramError as e:
                print(f"telegram_digest: couldn't pin the list ({e})", file=sys.stderr)

    try:
        bot = Bot(chat_id=str(tg_cfg["chat_id"]) if tg_cfg.get("chat_id") else None)
        if args.list_only:
            if use_topics:
                for sec in sections:
                    for kinds, thread in tab_threads(sec):
                        send_list(bot, [list_title(board), ""] + area_list_lines(sec, kinds=kinds), thread)
            else:
                send_list(bot, list_lines(board, sections))
            print("telegram_digest: sent and pinned the full list", file=sys.stderr)
            return
        if use_topics:
            # Group with Topics: General gets the summary with a button per tab; each tab gets its own cards
            # and pinned list (pennies and deals in separate tabs when the setup has them).
            rows = []
            for sec in sections:
                ids, label = tab_ids(topics, sec["area"]["zip"]), short_names[sec["area"]["zip"]]
                if ids["penny"] == ids["deals"]:
                    rows.append([{"text": f"📍 {label} · 🪙 {len(sec['penny_cards'])} pennies · 🏷 {len(sec['deal_cards'])} deals",
                                  "url": bot.topic_link(ids["penny"])}])
                else:
                    rows.append([{"text": f"🪙 {label} pennies ({len(sec['penny_cards'])})",
                                  "url": bot.topic_link(ids["penny"])},
                                 {"text": f"🏷 {label} deals ({len(sec['deal_cards'])})",
                                  "url": bot.topic_link(ids["deals"])}])
            bot.send_message(header_text, buttons=rows + [[{"text": "📋 Open the full board", "url": args.board_url}]])
            for sec in sections:
                for kinds, thread in tab_threads(sec):
                    cards = {("watch",): sec["penny_cards"], ("deal",): sec["deal_cards"]}.get(kinds, sec["cards"])
                    note = {("watch",): PENNY_TAB_NOTE, ("deal",): DEALS_TAB_NOTE}.get(kinds)
                    n = len(cards)
                    what = {("watch",): f"{n} {new}penny chance{'s' if n != 1 else ''}",
                            ("deal",): f"{n} {new}clearance deal{'s' if n != 1 else ''}"}.get(kinds, counts(sec))
                    time.sleep(0.4)
                    bot.send_message(f"🔨 <b>{esc(board['checked'])}</b> · {what}" + (f"\n{note}" if note else ""),
                                     silent=True, thread=thread)
                    if kinds == ("watch", "deal"):
                        for banner, kind_cards, none in ((PENNY_BANNER, sec["penny_cards"], "No new penny chances today."),
                                                         (DEALS_BANNER, sec["deal_cards"], "No new clearance deals today.")):
                            time.sleep(0.4)
                            bot.send_message(banner + ("" if kind_cards else f"\n{none}"), silent=True, thread=thread)
                            send_cards(bot, kind_cards, thread)
                    else:
                        send_cards(bot, cards, thread)
                    send_list(bot, [list_title(board), ""] + area_list_lines(sec, kinds=kinds), thread)
            if gone_lines(board):
                time.sleep(0.4)
                bot.send_message("\n".join(gone_lines(board))[:TEXT_LIMIT], silent=True)
        else:
            bot.send_message(header_text, buttons=[[{"text": "📋 Open the full board", "url": args.board_url}]])
            for sec in sections:
                if sec["cards"]:
                    time.sleep(0.4)
                    bot.send_message(area_line(sec["area"], sec["stores"]), silent=True)
                    send_cards(bot, sec["cards"])
            send_list(bot, list_lines(board, sections))
    except NotConfigured as e:
        print(f"telegram_digest: not set up, {e}; nothing sent", file=sys.stderr)
        sys.exit(3)
    except TelegramError as e:
        sys.exit(f"telegram_digest: {e}")
    print(f"telegram_digest: sent header and {n_cards} cards "
          f"{'in the group tabs' if use_topics else 'in one chat'}", file=sys.stderr)
    if bot.found_chat_id:
        print(f"telegram_digest: found your chat ID {bot.chat_id} from your last message to the bot. "
              f"Save TELEGRAM_CHAT_ID={bot.chat_id} in the environment so updates keep working; "
              "the bot only remembers messages for 24 hours.", file=sys.stderr)


def setup_topics(config_path, layout="area"):
    """Create fresh tabs in the group, remove the old ones, and print the config block.

    layout "area": one 📍 tab per area (pennies and deals inside, split by banners).
    layout "type": one 🪙 Pennies tab and one 🏷 Deals tab covering every area.
    Uses the group already in config.json, or else the group with Topics the bot was added to. Old tabs
    are deleted when the bot may delete messages; otherwise they're closed and labeled so you can
    delete them yourself."""
    from telegram_api import Bot, TelegramError
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    tg = cfg.get("telegram") or {}
    bot = Bot(chat_id="")
    chat_id, title = str(tg.get("chat_id") or ""), tg.get("group", "")
    if not chat_id:
        chat_id, title = bot.find_forum_group()
    if not chat_id:
        sys.exit("telegram_digest: no group with Topics found. Add the bot to the group as an admin "
                 "(Manage Topics + Pin Messages), turn on Topics, send any message in the group, "
                 "then run this again within 24 hours.")
    bot.chat_id = chat_id
    old = []
    for v in (tg.get("topics") or {}).values():
        old += [x for x in (v.values() if isinstance(v, dict) else [v]) if isinstance(x, int)]
    short_names = {a["zip"]: a.get("short") or a["label"] for a in cfg["areas"]}
    colors = [9367192, 7322096, 16766590, 13338331, 16749490, 16478047]
    removed, closed = [], []
    try:
        if layout == "type":
            areas = " and ".join(f"{n} area" for n in short_names.values())
            topics = {"penny": bot.create_topic("🪙 Pennies", 16766590), "deals": bot.create_topic("🏷 Deals", 9367192)}
            bot.send_message(f"{PENNY_TAB_NOTE}\nEach item shows up once, with the stores in the {esc(areas)} that "
                             "have it. The full penny list stays pinned here.", thread=topics["penny"])
            bot.send_message(f"{DEALS_TAB_NOTE}\nEach item shows up once, with its price at your stores in the "
                             f"{esc(areas)}. The full deals list stays pinned here.", thread=topics["deals"])
            summary = "two tabs: 🪙 <b>Pennies</b> and 🏷 <b>Deals</b>"
        else:
            topics = {}
            for i, area in enumerate(cfg["areas"]):
                name = short_names[area["zip"]]
                thread = bot.create_topic(f"📍 {name}", colors[i % len(colors)])
                topics[area["zip"]] = thread
                bot.send_message(f"📍 <b>{esc(name)}</b>: penny chances and clearance deals at the stores within "
                                 f"{area.get('radius', '')} miles of {esc(area['zip'])}. Each morning: 🪙 PENNIES "
                                 "first, then 🏷 DEALS, and the full list stays pinned here.", thread=thread)
            summary = "a tab for each area: " + ", ".join(f"📍 <b>{esc(n)}</b>" for n in short_names.values())
        for thread in dict.fromkeys(old):
            try:
                bot.delete_topic(thread)
                removed.append(thread)
            except TelegramError:
                try:
                    bot.edit_topic(thread, "🗑 Old tab (you can delete it)")
                    bot.close_topic(thread)
                    closed.append(thread)
                except TelegramError:
                    pass  # already gone
        note = (f"\nThe {len(closed)} old tabs are closed and marked 🗑. Long-press each one and tap Delete to "
                "remove it." if closed else "")
        bot.send_message(f"🔨 <b>Penny Hunt</b> now has {summary}. Each morning a summary lands here with a "
                         "button for each tab." + note)
    except TelegramError as e:
        sys.exit(f"telegram_digest: {e}. Make sure the bot is an admin with Manage Topics and Pin Messages.")
    print(json.dumps({"telegram": {"chat_id": chat_id, "group": title, "layout": layout, "topics": topics},
                      "old_tabs": {"deleted": removed, "closed": closed}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
