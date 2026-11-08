"""Kiem tra trung lap trong dataset merged_clean.csv.

Phan tich:
1. So dong trung lap hoan toan (ca 7 cot)
2. So dong trung theo subject+body (nhu merge_datasets.py da lam)
3. Trung nhung label khac nhau (mau thuan Nhan - nguy hiem)
4. Ty le trung lap

Cach chay:
    python scripts/check_duplicates.py
"""

import sys
import csv
import hashlib
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

csv.field_size_limit(sys.maxsize)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data_train" / "processed" / "merged_clean.csv"


def main():
    print("=" * 70)
    print("KIEM TRA TRUNG LAP DATASET")
    print("=" * 70)
    print(f"File: {INPUT_CSV}")
    print()

    # --- Doc dataset ---
    print("[1] Doc dataset...")
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    total = len(df)
    print(f"    Tong so dong: {total:,}")
    print(f"    Phan bo label:")
    print(f"      Legit (0):    {(df['label']==0).sum():,} ({(df['label']==0).sum()/total*100:.1f}%)")
    print(f"      Phishing (1): {(df['label']==1).sum():,} ({(df['label']==1).sum()/total*100:.1f}%)")
    print()

    # --- 2. Trung lap hoan toan (ca 7 cot) ---
    print("[2] Trung lap HOAN TOAN (ca 7 cot: sender, receiver, date, subject, body, label, urls)...")
    cols_full = ["sender", "receiver", "date", "subject", "body", "label", "urls"]
    df_full = df[cols_full].fillna("")  # thay NaN bang ""
    dup_full = df_full.duplicated(keep=False)  # keep=False: tat ca dong trung deu True
    n_dup_full = dup_full.sum()
    print(f"    So dong trung lap hoan toan: {n_dup_full:,} ({n_dup_full/total*100:.2f}%)")
    print(f"    So dong duy nhat (khong trung): {total - n_dup_full:,}")
    print()

    # --- 3. Trung theo subject+body (nhu merge_datasets.py) ---
    print("[3] Trung lap theo SUBJECT + BODY (nhu merge_datasets.py da xu ly)...")
    df["hash_subj_body"] = df.apply(
        lambda r: hashlib.md5(
            f"{str(r['subject']).strip()}|{str(r['body']).strip()}".encode("utf-8", errors="ignore")
        ).hexdigest(),
        axis=1,
    )
    dup_sb = df["hash_subj_body"].duplicated(keep=False)
    n_dup_sb = dup_sb.sum()
    print(f"    So dong trung subject+body: {n_dup_sb:,} ({n_dup_sb/total*100:.2f}%)")
    print()

    # --- 4. Trung subject+body nhung label KHAC nhau (mau thuan Nhan) ---
    print("[4] Kiem tra MAU THUAN NHAN (trung subject+body nhung label khac nhau)...")
    conflicts = df.groupby("hash_subj_body")["label"].nunique()
    n_conflict_hashes = (conflicts > 1).sum()
    print(f"    So nhom subject+body co label mau thuan: {n_conflict_hashes:,}")

    if n_conflict_hashes > 0:
        print("    Vi du mau thuuran:")
        conflict_hashes = conflicts[conflicts > 1].index[:3]
        for h in conflict_hashes:
            subset = df[df["hash_subj_body"] == h]
            print(f"      Subject: {str(subset.iloc[0]['subject'])[:60]}")
            print(f"      Labels:  {subset['label'].tolist()}")
    print()

    # --- 5. Trung sender+subject+date (email trung co metadata giong het) ---
    print("[5] Trung lap theo SENDER + SUBJECT + DATE (email trung co metadata giong)...")
    df["hash_full"] = df.apply(
        lambda r: hashlib.md5(
            f"{str(r['sender']).strip()}|{str(r['subject']).strip()}|{str(r['date']).strip()}".encode("utf-8", errors="ignore")
        ).hexdigest(),
        axis=1,
    )
    dup_meta = df["hash_full"].duplicated(keep=False)
    n_dup_meta = dup_meta.sum()
    print(f"    So dong trung sender+subject+date: {n_dup_meta:,} ({n_dup_meta/total*100:.2f}%)")
    print()

    # --- 6. Tong hop ---
    print("=" * 70)
    print("TONG HOP KET QUA")
    print("=" * 70)
    print(f"  Tong so dong:                    {total:,}")
    print(f"  Trung lap hoan toan (7 cot):     {n_dup_full:,} ({n_dup_full/total*100:.2f}%)")
    print(f"  Trung subject+body:              {n_dup_sb:,} ({n_dup_sb/total*100:.2f}%)")
    print(f"  Trung sender+subject+date:       {n_dup_meta:,} ({n_dup_meta/total*100:.2f}%)")
    print(f"  Nhan mau thuan (label khac):     {n_conflict_hashes:,} nhom")
    print()

    if n_dup_full == 0 and n_dup_sb == 0:
        print("  [OK] DATASET SACH: Khong co trung lap!")
    elif n_dup_full == 0:
        print("  [CANH BAO] DATASET co trung subject+body nhung khong trung hoan toan")
        print("     (Co the merge_datasets.py da xu ly trung roi nhung con sot)")
    else:
        print(f"  [LOI] DATASET CO {n_dup_full:,} DONG TRUNG LAP HOAN TOAN!")
        print("     -> Can xu ly truoc khi train de tranh hoc qua nhieu")

    # --- 7. Ghi file CSV 1000 dong mau ---
    print()
    print("=" * 70)
    print("TAO FILE MAU 1,000 DONG CHO EXCEL")
    print("=" * 70)

    sample_path = PROJECT_ROOT / "data_train" / "sample_1000_rows.csv"
    sample = df.sample(n=min(1000, len(df)), random_state=42)
    sample_out = sample[["sender", "receiver", "date", "subject", "body", "label", "urls"]].copy()
    sample_out["subject"] = sample_out["subject"].astype(str).str[:100]  # cat subject 100 ky tu
    sample_out["body"] = sample_out["body"].astype(str).str[:500]  # cat body 500 ky tu
    sample_out["sender"] = sample_out["sender"].astype(str).str[:50]
    sample_out["receiver"] = sample_out["receiver"].astype(str).str[:50]
    sample_out.to_csv(sample_path, index=False, encoding="utf-8-sig")

    print("  [OK] Da luu: " + str(sample_path))
    print(f"     So dong: {len(sample_out):,}")
    print(f"     Phan biet label:")
    print(f"       Legit (0):    {(sample_out['label']==0).sum():,}")
    print(f"       Phishing (1): {(sample_out['label']==1).sum():,}")
    print()
    print("  [Luu y] body da cat ngan 500 ky tu de mo Excel khong lag")
    print("     (Full body van con trong merged_clean.csv)")

    # --- 8. Ghi file CSV 1000 dong tu tung file raw ---
    print()
    print("=" * 70)
    print("TAO FILE MAU TUNG FILE RAW (100 DONG/FILE)")
    print("=" * 70)

    raw_dir = PROJECT_ROOT / "data_train" / "raw"
    raw_sample_dir = PROJECT_ROOT / "data_train" / "raw_samples"
    raw_sample_dir.mkdir(exist_ok=True)

    import csv
    csv.field_size_limit(sys.maxsize)

    for raw_file in sorted(raw_dir.glob("*.csv")):
        try:
            raw_df = pd.read_csv(raw_file, nrows=100, encoding="utf-8", engine="python")
            # Cat body + subject ngan de mo Excel khong lag
            for col in ["body", "subject"]:
                if col in raw_df.columns:
                    raw_df[col] = raw_df[col].astype(str).str[:300]
            out_path = raw_sample_dir / raw_file.name.replace(".csv", "_sample.csv")
            raw_df.to_csv(out_path, index=False, encoding="utf-8-sig")
            print(f"  [OK] {raw_file.name} -> {out_path.name} ({len(raw_df)} dong)")
        except Exception as e:
            print(f"  [ERR] {raw_file.name}: {e}")

    print()
    print(f"  Thu muc mau: {raw_sample_dir}")
    print("  [OK] Moi file chi 100 dong, body cat 300 ky tu -> mo Excel nhanh, khong lag!")

    # --- 9. Tong hop 1,000 dong tu nhieu file raw (de xem phong phu) ---
    print()
    print("=" * 70)
    print("TAO FILE TONG HOP 1,000 DONG TU NHIEU FILE RAW")
    print("=" * 70)

    parts = []
    per_file = 100  # 100 dong x 11 file = 1,100 dong
    for raw_file in sorted(raw_dir.glob("*.csv")):
        try:
            raw_df = pd.read_csv(raw_file, nrows=per_file, encoding="utf-8", engine="python")
            raw_df["source_file"] = raw_file.stem  # them cot nguon
            for col in ["body", "subject"]:
                if col in raw_df.columns:
                    raw_df[col] = raw_df[col].astype(str).str[:300]
            parts.append(raw_df)
        except Exception as e:
            print(f"  [ERR] {raw_file.name}: {e}")

    if parts:
        combined = pd.concat(parts, ignore_index=True, sort=False)
        # Cat dung 1,000 dong dau
        combined = combined.head(1000)
        combined_path = PROJECT_ROOT / "data_train" / "raw_samples" / "ALL_RAW_combined_1000.csv"
        combined.to_csv(combined_path, index=False, encoding="utf-8-sig")
        print(f"  [OK] Da luu: {combined_path}")
        print(f"       So dong: {len(combined):,}")
        print(f"       Cot: {list(combined.columns)}")


if __name__ == "__main__":
    main()

