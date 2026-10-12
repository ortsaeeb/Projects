"""Minimal Telegram Bot API client shared by the Penny Hunt notifiers.

Reads TELEGRAM_BOT_TOKEN and, optionally, TELEGRAM_CHAT_ID from the
environment. Without a chat id it uses the chat of the latest private
message sent to the bot (Telegram keeps those for 24 hours).
"""
import json
import os
import time
import urllib.error
import urllib.request
from http.client import HTTPException


class TelegramError(Exception):
    pass


class NotConfigured(TelegramError):
    pass


class Bot:
    def __init__(self, token=None, chat_id=None):
        self.token = (token if token is not None else os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
        self.chat_id = (chat_id if chat_id is not None else os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
        self.found_chat_id = False
        if not self.token:
            raise NotConfigured("missing TELEGRAM_BOT_TOKEN")

    def call(self, method, payload=None):
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=json.dumps(payload or {}).encode(), headers={"Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    body = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                body = json.loads(e.read() or b"{}")
                retry = (body.get("parameters") or {}).get("retry_after")
                if e.code == 429 and retry and attempt < 2:  # flood limit: wait as told
                    time.sleep(retry + 1)
                    continue
                # Telegram explains the problem in the body (bad token, chat not found, ...).
                raise TelegramError(f"{method}: {body.get('description', e.reason)}") from None
            except (urllib.error.URLError, HTTPException, ConnectionError, TimeoutError) as e:
                # Dropped connection or timeout: try again, then give up with a clear error.
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise TelegramError(f"{method}: couldn't reach Telegram ({e})") from None
        if not body.get("ok"):
            raise TelegramError(f"{method}: {body.get('description', 'not accepted')}")
        return body.get("result")

    def resolve_chat(self):
        """Make sure chat_id is set, looking it up from recent messages if needed."""
        if self.chat_id:
            return self.chat_id
        for update in reversed(self.call("getUpdates") or []):
            msg = update.get("message") or update.get("edited_message") or {}
            chat = msg.get("chat") or {}
            if chat.get("type") == "private" and chat.get("id"):
                self.chat_id, self.found_chat_id = str(chat["id"]), True
                return self.chat_id
        bot = (self.call("getMe") or {}).get("username", "your bot")
        raise TelegramError(f"TELEGRAM_CHAT_ID isn't set and nobody has messaged @{bot} in the last 24 hours. "
                            f"Open t.me/{bot} in Telegram, tap Start, send any message, then run this again.")

    def send_message(self, html, buttons=None, silent=False, thread=None):
        payload = {"chat_id": self.resolve_chat(), "text": html, "parse_mode": "HTML",
                   "disable_web_page_preview": True, "disable_notification": silent}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        if thread:
            payload["message_thread_id"] = thread
        return self.call("sendMessage", payload)

    def send_photo(self, photo_url, html_caption, buttons=None, silent=False, thread=None):
        payload = {"chat_id": self.resolve_chat(), "photo": photo_url, "caption": html_caption,
                   "parse_mode": "HTML", "disable_notification": silent}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        if thread:
            payload["message_thread_id"] = thread
        return self.call("sendPhoto", payload)

    def pin(self, message_id, thread=None):
        """Pin a message, replacing earlier pins (in that topic only, for a topic)."""
        if thread:
            self.call("unpinAllForumTopicMessages", {"chat_id": self.resolve_chat(), "message_thread_id": thread})
        else:
            self.call("unpinAllChatMessages", {"chat_id": self.resolve_chat()})
        self.call("pinChatMessage", {"chat_id": self.chat_id, "message_id": message_id,
                                     "disable_notification": True})

    # Groups with Topics (forums): each topic works like a tab.

    def is_forum(self):
        return bool((self.call("getChat", {"chat_id": self.resolve_chat()}) or {}).get("is_forum"))

    def find_forum_group(self):
        """The most recent group with Topics that the bot has seen in the last 24 hours."""
        for update in reversed(self.call("getUpdates") or []):
            for key in ("message", "edited_message", "my_chat_member"):
                chat = (update.get(key) or {}).get("chat") or {}
                if chat.get("type") == "supergroup" and chat.get("id"):
                    info = self.call("getChat", {"chat_id": chat["id"]}) or {}
                    if info.get("is_forum"):
                        return str(chat["id"]), info.get("title", "")
        return None, None

    def create_topic(self, name, color=None):
        payload = {"chat_id": self.resolve_chat(), "name": name}
        if color:
            payload["icon_color"] = color
        return (self.call("createForumTopic", payload) or {})["message_thread_id"]

    def edit_topic(self, thread, name):
        self.call("editForumTopic", {"chat_id": self.resolve_chat(), "message_thread_id": thread, "name": name})

    def delete_topic(self, thread):
        self.call("deleteForumTopic", {"chat_id": self.resolve_chat(), "message_thread_id": thread})

    def close_topic(self, thread):
        self.call("closeForumTopic", {"chat_id": self.resolve_chat(), "message_thread_id": thread})

    def topic_link(self, thread):
        """Link that opens a topic (works for members of the group)."""
        return f"https://t.me/c/{str(self.chat_id).removeprefix('-100')}/{thread}"
