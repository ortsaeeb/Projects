#!/usr/bin/env python3
"""Send a Penny Hunt update to Telegram.

Reads the message text from stdin and sends it through your Telegram bot,
with a button that opens the Penny Hunt Board.

Environment variables:
    TELEGRAM_BOT_TOKEN   the token @BotFather gave you (required)
    TELEGRAM_CHAT_ID     your chat id. Optional: if it's missing, the script
                         uses the chat of the last message you sent the bot
                         (within 24 hours) and prints the id to save.

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
    if not token:
        print("notify_telegram: not set up, missing TELEGRAM_BOT_TOKEN; nothing sent", file=sys.stderr)
        sys.exit(3)

    found = False
    if not chat_id:
        chat_id = find_chat_id(token)
        if not chat_id:
            sys.exit("notify_telegram: TELEGRAM_CHAT_ID isn't set and nobody has messaged the bot in the "
                     "last 24 hours. Send your bot any message in Telegram, then run this again.")
        payload["chat_id"], found = chat_id, True

    call(token, "sendMessage", payload)
    print("notify_telegram: sent", file=sys.stderr)
    if found:
        print(f"notify_telegram: found your chat ID {chat_id} from your last message to the bot. "
              f"Save TELEGRAM_CHAT_ID={chat_id} in the environment so updates keep working; "
              "the bot only remembers messages for 24 hours.", file=sys.stderr)


def call(token, method, payload=None):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload or {}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        # Telegram explains the problem in the body (bad token, chat not found, bot blocked, ...).
        detail = json.loads(e.read() or b"{}").get("description", e.reason)
        sys.exit(f"notify_telegram: Telegram refused {method}: {detail}")
    if not body.get("ok"):
        sys.exit(f"notify_telegram: Telegram did not accept {method}")
    return body.get("result")


def find_chat_id(token):
    """The chat of the most recent private message sent to the bot (Telegram keeps them 24 hours)."""
    for update in reversed(call(token, "getUpdates") or []):
        msg = update.get("message") or update.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("type") == "private" and chat.get("id"):
            return str(chat["id"])
    return None


if __name__ == "__main__":
    main()
