"""Auto Monitor: chay vong lap tu dong kiem tra email moi va gui canh bao Telegram.

Cach chay:
    python scripts/run_auto_monitor.py

Hoac chay nen (background):
    python scripts/run_auto_monitor.py --background
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from datetime import datetime

from app.email_fetcher import fetch_and_analyze


RUNNING = True


def _handle_signal(sig, frame):
    global RUNNING
    print("\n[Monitor] Dang dung...")
    RUNNING = False


def run_once(min_score: float = 60.0) -> int:
    results = fetch_and_analyze(min_risk_score=min_score)
    notified = sum(1 for r in results if r.get("notified"))
    print(f"[Monitor] {datetime.now().strftime('%H:%M:%S')} - {len(results)} email, {notified} canh bao.")
    return notified


def run_loop(interval: int = 30, min_score: float = 60.0) -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print(f"[Monitor] Bat dau vong lap. Kiem tra moi {interval}s. Diem toi thieu: {min_score}%")
    print("[Monitor] Nhan Ctrl+C de dung.")

    while RUNNING:
        try:
            run_once(min_score)
        except Exception as e:
            print(f"[Monitor] Loi: {e}")
        time.sleep(interval)

    print("[Monitor] Da dung.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto monitor email phishing + Telegram alert")
    parser.add_argument("--interval", type=int, default=30, help="Thoi gian kiem tra (giay)")
    parser.add_argument("--min-score", type=float, default=60.0, help="Diem toi thieu de gui canh bao")
    parser.add_argument("--once", action="store_true", help="Chi chay 1 lan")
    args = parser.parse_args()

    if args.once:
        run_once(args.min_score)
    else:
        run_loop(args.interval, args.min_score)


if __name__ == "__main__":
    main()
