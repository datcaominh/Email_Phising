"""Chuan bi dataset JSONL hoi thoai cho fine-tuning LLM.

Input:
    data_train/CEAS_08.csv voi schema:
    sender, receiver, date, subject, body, label, urls

Output:
    data_train/ceas_llm_dataset.jsonl

Cach chay:
    python scripts/prepare_llm_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data_train" / "CEAS_08.csv"
OUTPUT_JSONL = PROJECT_ROOT / "data_train" / "ceas_llm_dataset.jsonl"
SYSTEM_PROMPT = (
    "Ban la chuyen gia SecOps phan tich email phishing. "
    "Hay danh gia email la phishing hay safe va giai thich ngan gon bang tieng Viet."
)


def make_assistant_answer(label: int, row: pd.Series) -> str:
    """Tao cau tra loi mau cho assistant dua tren label co san."""
    verdict = "Phishing" if int(label) == 1 else "Safe"
    reason = (
        "Email co dau hieu rui ro nhu link/yeu cau hanh dong bat thuong, can cach ly va xac minh."
        if int(label) == 1
        else "Email khong co dau hieu phishing ro rang trong du lieu gan nhan."
    )
    return f"Ket luan: {verdict}\nGiai thich: {reason}"


def row_to_chat_json(row: pd.Series) -> dict:
    """Chuyen 1 dong CSV thanh format messages dung cho fine-tuning chat."""
    user_content = f"""
Sender: {row.get("sender", "")}
Receiver: {row.get("receiver", "")}
Date: {row.get("date", "")}
Subject: {row.get("subject", "")}
URLs: {row.get("urls", "")}

Body:
{row.get("body", "")}
""".strip()
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": make_assistant_answer(int(row["label"]), row)},
        ]
    }


def main() -> None:
    """Lay mau phan tang 500 phishing + 500 safe va ghi JSONL."""
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Khong tim thay dataset: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    required_columns = {"sender", "receiver", "date", "subject", "body", "label", "urls"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Dataset thieu cot: {sorted(missing)}")

    df = df.dropna(subset=["subject", "body", "label"]).copy()
    df["label"] = df["label"].astype(int)

    phishing = df[df["label"] == 1].sample(n=min(500, (df["label"] == 1).sum()), random_state=42)
    safe = df[df["label"] == 0].sample(n=min(500, (df["label"] == 0).sum()), random_state=42)
    sampled = pd.concat([phishing, safe]).sample(frac=1, random_state=42)

    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSONL.open("w", encoding="utf-8") as file:
        for _, row in sampled.iterrows():
            file.write(json.dumps(row_to_chat_json(row), ensure_ascii=False) + "\n")

    print(f"Da ghi {len(sampled)} mau vao {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
