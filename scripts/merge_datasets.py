"""Gộp 11 dataset từ Champa et al. (2024) + tiền xử lý.

Input:  data_train/raw/*.csv       (file gốc chưa xử lý)
Output: data_train/processed/merged_clean.csv (file đã gộp + xử lý)

Cach chay:
    python scripts/merge_datasets.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data_train" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data_train" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "merged_clean.csv"

# Cột chuẩn cần có
CANONICAL_COLUMNS = ["sender", "receiver", "date", "subject", "body", "label", "urls"]


def clean_text(text: str) -> str:
    """Làm sạch text: bỏ HTML, chuẩn hóa whitespace."""
    if not isinstance(text, str):
        return ""
    # Bỏ HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Bỏ URL trong body (vì đã có cột urls riêng)
    # text = re.sub(r"https?://\S+", "", text)
    # Chuẩn hóa whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_label(value) -> int:
    """Chuẩn hóa label về 0 hoặc 1."""
    if pd.isna(value):
        return -1  # invalid
    s = str(value).strip().lower()
    if s in ("1", "phishing", "spam", "true", "yes"):
        return 1
    if s in ("0", "ham", "legitimate", "legit", "safe", "false", "no"):
        return 0
    try:
        return int(float(s))
    except ValueError:
        return -1


def load_one_file(path: Path) -> pd.DataFrame:
    """Đọc 1 file CSV, chuẩn hóa schema về CANONICAL_COLUMNS."""
    df = None
    for enc in ("utf-8", "latin-1"):
        for engine in ("c", "python"):
            kwargs = dict(encoding=enc, on_bad_lines="skip", engine=engine)
            if engine == "c":
                kwargs["low_memory"] = False
            try:
                df = pd.read_csv(path, **kwargs)
                break
            except Exception:
                df = None
        if df is not None:
            break
    if df is None:
        raise RuntimeError(f"Khong doc duoc file: {path.name}")

    source = path.stem  # tên file làm tên nguồn

    # Đổi tên cột nếu có khác biệt (vd: "Text" -> "body")
    rename_map = {}
    for col in df.columns:
        low = col.strip().lower()
        if low in ("text", "message", "content", "email_body", "email body"):
            rename_map[col] = "body"
        elif low in ("subject_line", "email_subject", "email subject"):
            rename_map[col] = "subject"
        elif low in ("class", "target", "spam_label", "is_phishing"):
            rename_map[col] = "label"
        elif low in ("email", "from", "sender_address"):
            rename_map[col] = "sender"
        elif low in ("to", "recipient"):
            rename_map[col] = "receiver"
        elif low in ("url", "link", "links"):
            rename_map[col] = "urls"
        elif low in ("timestamp", "time", "sent_date"):
            rename_map[col] = "date"
    if rename_map:
        df = df.rename(columns=rename_map)

    # Thêm cột thiếu với giá trị rỗng
    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # Giữ đúng các cột chuẩn + thêm cột source
    df = df[CANONICAL_COLUMNS].copy()
    df["source"] = source

    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Tiền xử lý: clean text, normalize label, dedup."""
    total_before = len(df)

    # 1. Clean text
    df["subject"] = df["subject"].apply(clean_text)
    df["body"] = df["body"].apply(clean_text)

    # 2. Normalize label
    df["label"] = df["label"].apply(normalize_label)

    # 3. Bỏ label invalid (-1)
    invalid = (df["label"] == -1).sum()
    df = df[df["label"] != -1].copy()

    # 4. Bỏ email rỗng (cả subject và body đều rỗng)
    empty = (df["subject"] == "") & (df["body"] == "")
    df = df[~empty].copy()

    # 5. Convert label về int
    df["label"] = df["label"].astype(int)

    # 6. Dedup: bỏ trùng theo subject + body
    dup_before = len(df)
    df = df.drop_duplicates(subset=["subject", "body"], keep="first").copy()
    dup_removed = dup_before - len(df)

    total_after = len(df)

    return df, {
        "before": total_before,
        "invalid_label": int(invalid),
        "empty_removed": int(empty.sum()),
        "duplicates_removed": int(dup_removed),
        "after": total_after,
    }


def main() -> None:
    print("=" * 60)
    print("GOP + TIEN XU LY 11 DATASET (Champa et al. 2024)")
    print("=" * 60)

    # Kiểm tra thư mục raw
    if not RAW_DIR.exists():
        print(f"LOI: Khong tim thay thu muc {RAW_DIR}")
        sys.exit(1)

    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        print(f"LOI: Khong co file CSV nao trong {RAW_DIR}")
        sys.exit(1)

    print(f"\nTim thay {len(csv_files)} file CSV:\n")

    # Bước 1: Đọc từng file
    frames = []
    file_stats = []
    for path in csv_files:
        df = load_one_file(path)
        n_phish = (df["label"] == 1).sum() if "label" in df.columns else 0
        n_legit = (df["label"] == 0).sum() if "label" in df.columns else 0
        file_stats.append((path.name, len(df), int(n_phish), int(n_legit)))
        frames.append(df)

    # In bảng thống kê từng file
    print(f"{'File':<25} {'So luong':>10} {'Phishing':>10} {'Legit':>10}")
    print("-" * 60)
    for name, total, p, l in file_stats:
        print(f"{name:<25} {total:>10,} {p:>10,} {l:>10,}")
    print("-" * 60)

    # Bước 2: Gộp
    print("\nDang gộp...")
    merged = pd.concat(frames, ignore_index=True)
    print(f"  Tong sau gộp: {len(merged):,} email")

    # Bước 3: Tiền xử lý
    print("Dang tien xu ly...")
    cleaned, stats = preprocess(merged)

    print(f"\n  Truoc xu ly:     {stats['before']:>10,}")
    print(f"  - Label invalid:  {stats['invalid_label']:>10,}")
    print(f"  - Email rong:     {stats['empty_removed']:>10,}")
    print(f"  - Trung lap:      {stats['duplicates_removed']:>10,}")
    print(f"  Sau xu ly:        {stats['after']:>10,}")

    # Bước 4: Thống kê cuối
    n_phish = (cleaned["label"] == 1).sum()
    n_legit = (cleaned["label"] == 0).sum()
    print(f"\n  Phishing (1):     {n_phish:>10,} ({100*n_phish/len(cleaned):.1f}%)")
    print(f"  Legit    (0):     {n_legit:>10,} ({100*n_legit/len(cleaned):.1f}%)")

    # Bước 5: Thống kê theo nguồn
    print(f"\n  Theo nguon:")
    by_source = cleaned.groupby("source").agg(
        total=("label", "count"),
        phishing=("label", "sum"),
    )
    by_source["legit"] = by_source["total"] - by_source["phishing"]
    for src, row in by_source.iterrows():
        print(f"    {src:<25} {row['total']:>8,}  (P:{row['phishing']:>6,} L:{row['legit']:>6,})")

    # Bước 6: Lưu
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"\nDa luu: {OUTPUT_CSV}")
    print(f"Kich thuoc: {OUTPUT_CSV.stat().st_size / 1024 / 1024:.1f} MB")
    print("\nHoan tat!")


if __name__ == "__main__":
    main()
