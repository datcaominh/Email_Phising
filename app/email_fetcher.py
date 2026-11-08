"""Email Fetcher: ket noi Gmail IMAP, doc email moi va phan tich phishing.

Ket hop ML Engine + Telegram Notifier de tu dong canh bao.
"""

from __future__ import annotations

import email
import imaplib
import os
import sys
from datetime import datetime
from email.header import decode_header
from typing import Any, Dict, List, Optional

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

from app.ml_engine import predict_phishing
from app.orchestrator import extract_text_body, extract_urls
from app.telegram_notifier import send_alert


load_dotenv()

IMAP_SERVER = "imap.gmail.com"
SEEN_IDS_FILE = "logs/seen_email_ids.txt"


def _load_seen_ids() -> set[str]:
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def _save_seen_ids(ids: set[str]) -> None:
    os.makedirs(os.path.dirname(SEEN_IDS_FILE), exist_ok=True)
    with open(SEEN_IDS_FILE, "w", encoding="utf-8", errors="replace") as f:
        for id_ in sorted(ids):
            f.write(id_ + "\n")


def _decode_subject(subject: str) -> str:
    if not subject:
        return ""
    decoded_parts = decode_header(subject)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _parse_email_message(msg: email.message.Message) -> Dict[str, Any]:
    sender = msg.get("From", "")
    subject = _decode_subject(msg.get("Subject", ""))
    date = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")

    body = extract_text_body(msg)
    urls = extract_urls(body)

    return {
        "message_id": message_id,
        "sender": sender,
        "subject": subject,
        "date": date,
        "body": body,
        "urls": urls,
    }


def fetch_and_analyze(
    gmail_address: Optional[str] = None,
    app_password: Optional[str] = None,
    max_emails: int = 10,
    min_risk_score: float = 60.0,
) -> List[Dict[str, Any]]:
    gmail_address = gmail_address or os.getenv("GMAIL_ADDRESS", "")
    app_password = (app_password or os.getenv("GMAIL_APP_PASSWORD", "")).replace(" ", "")

    if not gmail_address or not app_password:
        print("[Fetcher] THIEU GMAIL_ADDRESS hoac GMAIL_APP_PASSWORD trong .env")
        return []

    seen_ids = _load_seen_ids()
    results: List[Dict[str, Any]] = []

    try:
        print(f"[Fetcher] Dang ket noi {IMAP_SERVER}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(gmail_address, app_password)
        mail.select("INBOX")

        _, msg_ids = mail.search(None, "UNSEEN")
        id_list = msg_ids[0].split()

        if not id_list:
            print("[Fetcher] Khong co email moi.")
            mail.logout()
            return []

        print(f"[Fetcher] Tim thay {len(id_list)} email chua doc.")

        for raw_id in id_list[-max_emails:]:
            _, msg_data = mail.fetch(raw_id, "(RFC822)")
            raw_email = msg_data[0][1]

            msg = email.message_from_bytes(raw_email)
            email_data = _parse_email_message(msg)

            mid = email_data.get("message_id", "") or raw_id.decode()
            if mid in seen_ids:
                continue

            ml_result = predict_phishing(email_data)
            score = float(ml_result.get("score", 0))

            try:
                print(f"[Fetcher] {email_data['subject'][:50]}... -> Diem: {score}%")
            except Exception:
                print(f"[Fetcher] (encoding issue) -> Diem: {score}%")

            result = {
                "email_data": email_data,
                "ml_result": ml_result,
            }

            if score >= min_risk_score:
                print(f"[Fetcher] GUI CANH BAO VE TELEGRAM (diem {score}%)")
                send_alert(email_data, ml_result)
                result["notified"] = True
            else:
                result["notified"] = False

            results.append(result)
            seen_ids.add(mid)

        mail.logout()
        _save_seen_ids(seen_ids)
        print(f"[Fetcher] Hoan tat. {len(results)} email duoc phan tich.")

    except imaplib.IMAP4.error as e:
        print(f"[Fetcher] Loi IMAP: {e}")
    except Exception as e:
        print(f"[Fetcher] Loi: {e}")

    return results
