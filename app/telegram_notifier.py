"""Telegram Notifier: gui canh bao phishing qua Telegram Bot.

Can cau hinh trong .env:
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=...
"""

from __future__ import annotations

import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv


load_dotenv()

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _get_config() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def format_alert_message(email_data: Dict[str, Any], ml_result: Dict[str, Any]) -> str:
    score = float(ml_result.get("score", 0))
    if score >= 60:
        icon = "PHISHING"
    else:
        icon = "NOT PHISHING"

    urls = email_data.get("urls") or []
    url_text = "\n".join(f"  {u}" for u in urls[:5]) if urls else "  Khong co"

    sender = email_data.get("sender", "Khong ro")
    subject = email_data.get("subject", "Khong co tieu de")
    date = email_data.get("date", "Khong ro")

    return f"""
{icon} - PHISHING ALERT

Nguoi gui: {sender}
Chu de: {subject}
Ngay: {date}
Diem rui ro ML: {score}%
Ket luan: {icon}

URLs phat hien:
{url_text}

Han dong: Khong bam link khi chua xac minh!
"""


def send_telegram(message: str) -> bool:
    token, chat_id = _get_config()
    if not token or not chat_id:
        print("[Telegram] THIEU BOT_TOKEN hoac CHAT_ID trong .env")
        return False

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("[Telegram] Da gui thanh cong.")
            return True
        else:
            print(f"[Telegram] Loi {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"[Telegram] Loi ket noi: {e}")
        return False


def send_alert(email_data: Dict[str, Any], ml_result: Dict[str, Any]) -> bool:
    score = float(ml_result.get("score", 0))
    if score < 60:
        print(f"[Telegram] Diem {score}% < 60, khong gui canh bao.")
        return False

    message = format_alert_message(email_data, ml_result)
    return send_telegram(message)
