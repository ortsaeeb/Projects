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
    if watch:
        more = f" Top {WATCH_LIST_MAX} of {len(watch)}." if len(watch) > WATCH_LIST_MAX else ""
        lines.append(f"🪙 <b>PENNY CHANCES</b>: price unknown until you scan. Could be $0.01. "
                     f"The price shown is regular retail.{more}")
        for l in watch[:WATCH_LIST_MAX]:
            it = l["item"]
            flag = "⚠️ RECALLED " if sec.get("recalls", {}).get(it["s"], {}).get("status") == "recalled" else ""
            where = f"{len(l['clearance'])} stores" if len(l["clearance"]) > 1 else (
                l["clearance"][0]["n"] if l["clearance"] else "in stock, inactive")
            il = f" · IL: {esc(it['il'])}" if it.get("il") else ""
            lines.append(f"• {flag}<a href=\"{esc(product_url(it))}\">{esc(short(it['n']))}</a> · "
                         f"retail {money(it.get('p'))}, may ring <b>$0.01</b> · in clearance at {esc(where)}{il} "
                         f"<code>{esc(it['s'])}</code>")
    if deals:
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
                    help="create one tab per area in the group the bot was just added to, then print the config")
    ap.add_argument("--list-only", action="store_true",
                    help="send and pin only the full list (no header or cards), e.g. to restore a missed list")
    ap.add_argument("--no-recall-check", action="store_true",
                    help="skip checking card items against the CPSC recall database")
    ap.add_argument("--dry-run", action="store_true", help="print the messages instead of sending them")
    args = ap.parse_args()
    if args.setup_topics:
        return setup_topics(args.config)
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8")) if Path(args.config).exists() else {}
    tg_cfg = cfg.get("telegram") or {}

    if not args.board:
        ap.error("--board is required")
    board = load_board(args.board)
    prev = load_board(args.prev) if args.prev and Path(args.prev).exists() else None

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
                ids, label = tab_ids(topics, sec["area"]["zip"]), sec["area"]["label"]
                if ids["penny"] == ids["deals"]:
                    rows.append([{"text": f"📍 {label} · {len(sec['cards'])} cards", "url": bot.topic_link(ids["penny"])}])
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


def setup_topics(config_path):
    """Give each area a 🪙 Pennies tab and a 🏷 Deals tab in the group, then print the config block.

    Uses the group already in config.json, or else the group with Topics the bot was added to. An
    existing one-tab-per-area setup is reused: that tab is renamed to the Pennies tab."""
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
    old = {str(k): v for k, v in (tg.get("topics") or {}).items()}
    gold, green = 16766590, 9367192
    topics = {}
    try:
        for area in cfg["areas"]:
            zip_code, label = area["zip"], area["label"]
            ids = tab_ids(old, zip_code)
            penny_name, deals_name = f"🪙 {label} ({zip_code}) · Pennies", f"🏷 {label} ({zip_code}) · Deals"
            if ids.get("penny"):
                bot.edit_topic(ids["penny"], penny_name)
                penny = ids["penny"]
            else:
                penny = bot.create_topic(penny_name, gold)
            if ids.get("deals") and ids["deals"] != penny:
                deals = ids["deals"]
                bot.edit_topic(deals, deals_name)
            else:
                deals = bot.create_topic(deals_name, green)
            topics[zip_code] = {"penny": penny, "deals": deals}
            bot.send_message(f"{PENNY_TAB_NOTE}\nStores around {esc(zip_code)} only. The full penny list stays "
                             "pinned here.", thread=penny)
            bot.send_message(f"{DEALS_TAB_NOTE}\nStores around {esc(zip_code)} only. The full deals list stays "
                             "pinned here.", thread=deals)
        bot.send_message("🔨 <b>Penny Hunt</b> now has a 🪙 Pennies tab and a 🏷 Deals tab for each area. "
                         "Each morning a summary lands here with a button for every tab.")
    except TelegramError as e:
        sys.exit(f"telegram_digest: {e}. Make sure the bot is an admin with Manage Topics and Pin Messages.")
    print(json.dumps({"telegram": {"chat_id": chat_id, "group": title, "topics": topics}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
