"""Report the actual dataset filtering and stratified 80/20 split used by compare_models.py."""
from pathlib import Path
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_train" / "processed" / "merged_clean.csv"
REQUIRED = ["subject", "body", "label"]


def show_counts(name: str, labels: pd.Series) -> None:
    counts = labels.value_counts().reindex([0, 1], fill_value=0)
    total = len(labels)
    print(f"{name}: {total:,} mẫu")
    print(f"  Legit (0):    {counts[0]:,} ({counts[0] / total:.2%})")
    print(f"  Phishing (1): {counts[1]:,} ({counts[1] / total:.2%})")


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"Không tìm thấy dataset: {DATA}")

    print("BÁO CÁO NẠP VÀ CHIA DỮ LIỆU")
    print(f"Tệp: {DATA.relative_to(ROOT)}")
    print("Cách chia: train/test = 80/20, stratified, random_state=42\n")

    df = pd.read_csv(DATA, low_memory=False)
    print(f"Số hàng trong CSV: {len(df):,}")
    missing = [col for col in REQUIRED if col not in df.columns]
    if missing:
        raise ValueError(f"Thiếu các cột bắt buộc: {', '.join(missing)}")

    df = df.dropna(subset=REQUIRED).copy()
    df["label"] = df["label"].astype(int)
    print(f"Số email hợp lệ sau khi lọc: {len(df):,}")
    show_counts("Toàn bộ tập dữ liệu", df["label"])

    train_idx, test_idx = train_test_split(
        list(range(len(df))), test_size=0.2, random_state=42, stratify=df["label"]
    )
    print()
    show_counts("Train", df.iloc[train_idx]["label"])
    show_counts("Test", df.iloc[test_idx]["label"])


if __name__ == "__main__":
    main()
