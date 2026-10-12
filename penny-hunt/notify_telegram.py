#!/usr/bin/env python3
"""Send a plain Penny Hunt message to Telegram.

Reads the message text from stdin and sends it through your Telegram bot,
with a button that opens the Penny Hunt Board. For the daily deal cards,
use telegram_digest.py instead.

Environment variables:
    TELEGRAM_BOT_TOKEN   the token @BotFather gave you (required)
    TELEGRAM_CHAT_ID     your chat id. Optional: if it's missing, the script
                         uses the chat of the last message you sent the bot
                         (within 24 hours) and prints the id to save.

Usage:
    echo "3 new leads at Evanston" | python3 notify_telegram.py
"""
import argparse
import html
import sys

from telegram_api import Bot, NotConfigured, TelegramError

BOARD_URL = "https://claude.ai/artifact/UXy1qhNygWumMsT6uvyKxd"
LIMIT = 4096  # Telegram's maximum message length


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board-url", default=BOARD_URL)
    args = ap.parse_args()

    text = sys.stdin.read().strip()
    if not text:
        sys.exit("notify_telegram: no message on stdin")
    text = html.escape(text)
    if len(text) > LIMIT:
        text = text[:LIMIT - 1] + "…"

    try:
        bot = Bot()
        bot.send_message(text, buttons=[[{"text": "Open Penny Hunt Board", "url": args.board_url}]])
    except NotConfigured as e:
        print(f"notify_telegram: not set up, {e}; nothing sent", file=sys.stderr)
        sys.exit(3)
    except TelegramError as e:
        sys.exit(f"notify_telegram: {e}")
    print("notify_telegram: sent", file=sys.stderr)
    if bot.found_chat_id:
        print(f"notify_telegram: found your chat ID {bot.chat_id} from your last message to the bot. "
              f"Save TELEGRAM_CHAT_ID={bot.chat_id} in the environment so updates keep working; "
              "the bot only remembers messages for 24 hours.", file=sys.stderr)


if __name__ == "__main__":
    main()
