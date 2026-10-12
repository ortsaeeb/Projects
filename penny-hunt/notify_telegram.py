#!/usr/bin/env python3
"""Send a Penny Hunt update to Telegram.

Reads the message text from stdin and sends it through your Telegram bot,
with a button that opens the Penny Hunt Board.

Needs two environment variables:
    TELEGRAM_BOT_TOKEN   the token @BotFather gave you
    TELEGRAM_CHAT_ID     your chat id (message @userinfobot to get it)

Usage:
    echo "3 new leads at Evanston" | python3 notify_telegram.py
    python3 notify_telegram.py --dry-run < summary.txt
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BOARD_URL = "https://claude.ai/artifact/UXy1qhNygWumMsT6uvyKxd"
LIMIT = 4096  # Telegram's maximum message length


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board-url", default=BOARD_URL)
    ap.add_argument("--dry-run", action="store_true", help="print the request instead of sending it")
    args = ap.parse_args()

    text = sys.stdin.read().strip()
    if not text:
        sys.exit("notify_telegram: no message on stdin")
    if len(text) > LIMIT:
        text = text[:LIMIT - 1] + "…"

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
        "reply_markup": {"inline_keyboard": [[{"text": "Open Penny Hunt Board", "url": args.board_url}]]},
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if not token or not chat_id:
        missing = [n for n, v in (("TELEGRAM_BOT_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id)) if not v]
        print(f"notify_telegram: not set up, missing {', '.join(missing)}; nothing sent", file=sys.stderr)
        sys.exit(3)

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = json.loads(r.read()).get("ok")
    except urllib.error.HTTPError as e:
        # Telegram explains the problem in the body (bad token, chat not found, bot blocked, ...).
        detail = json.loads(e.read() or b"{}").get("description", e.reason)
        sys.exit(f"notify_telegram: Telegram refused the message: {detail}")
    if not ok:
        sys.exit("notify_telegram: Telegram did not accept the message")
    print("notify_telegram: sent", file=sys.stderr)


if __name__ == "__main__":
    main()
