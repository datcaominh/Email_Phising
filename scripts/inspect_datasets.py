"""Phan tich chi tung file dataset trong data_train/raw."""

import sys
import csv
import pandas as pd
from pathlib import Path

csv.field_size_limit(sys.maxsize)

RAW = Path("data_train/raw")

for f in sorted(RAW.glob("*.csv")):
    print("=" * 70)
    print(f"FILE: {f.name}  ({round(f.stat().st_size/1024/1024,1)} MB)")
    print("=" * 70)
    try:
        df = pd.read_csv(f, nrows=3, encoding="utf-8", engine="python")
    except Exception:
        df = pd.read_csv(f, nrows=3, encoding="latin-1", engine="python")

    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes.to_string()}")

    # dem tong so hang (chunked cho file lon)
    total = 0
    try:
        for chunk in pd.read_csv(f, usecols=[0], encoding="utf-8", engine="python", chunksize=50000):
            total += len(chunk)
    except Exception:
        total = -1
    print(f"Total rows: {total}")

    print(f"\n--- Sample row 1 ---")
    for col in df.columns:
        val = str(df.iloc[0][col])[:300]
        print(f"  {col}: {val}")

    # phan bo label neu co
    for label_col in ["label", "Label", "label_num", "class", "target"]:
        if label_col in df.columns:
            try:
                full = pd.read_csv(f, usecols=[label_col], encoding="utf-8", engine="python")
                print(f"\n--- Label distribution ({label_col}) ---")
                print(full[label_col].value_counts(dropna=False).to_string())
            except Exception as e:
                print(f"(khong doc duoc label: {e})")
            break
    print()
