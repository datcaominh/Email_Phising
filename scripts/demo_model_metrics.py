"""In chi tay tung mo hinh: TP/FN/FP/TN + cong thuc FNR, FPR, Accuracy, Precision, Recall, F1.

Dung cho demo truc tiep (GVHD/cham do) — mo VSCode va chay:

    python -X utf8 scripts/demo_model_metrics.py              # toan bo 4 model
    python -X utf8 scripts/demo_model_metrics.py rf           # chi Random Forest
    python -X utf8 scripts/demo_model_metrics.py lr           # chi Logistic Regression
    python -X utf8 scripts/demo_model_metrics.py xgb          # chi XGBoost
    python -X utf8 scripts/demo_model_metrics.py mnb          # chi Naive Bayes

So lieu doc tu results/model_comparison.csv (sinh boi scripts/compare_models.py).
Neu CSV chua co hoac muon tinh lai tu dau:
    python -X utf8 scripts/compare_models.py        (khoang 20 phut)

Moi lan chay demo chi doc CSV nen in ket qua NGAY LAP TUC.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_CSV = PROJECT_ROOT / "results" / "model_comparison.csv"

# Kich thuoc dataset (giong split trong compare_models.py)
TOTAL_ROWS = 206_722        # tong so dong trong merged_clean.csv
TOTAL_VALID = 204_294       # sau khi loai dong null (dropna)
TRAIN_SIZE = 163_435
TEST_SIZE = 40_859          # = 20% cua 204,294 email hop le


def fmt(n: int) -> str:
    """18943 -> '18,943'"""
    return f"{n:,}"


def pct(x: float) -> str:
    return f"{x:.2f}%"


def print_model(row: pd.Series) -> None:
    name = str(row["Model"])
    tp = int(row["TP"])
    fp = int(row["FP"])
    tn = int(row["TN"])
    fn = int(row["FN"])

    # Cong thuc tinh tu TP/FP/TN/FN (khong doc truc tiep cac cot %)
    fnr = fn / (fn + tp) * 100
    fpr = fp / (fp + tn) * 100
    acc = (tp + tn) / (tp + tn + fp + fn) * 100
    precision = tp / (tp + fp) * 100
    recall = tp / (tp + fn) * 100
    f1 = 2 * precision * recall / (precision + recall)

    print("=" * 78)
    print(f"MODEL: {name}")
    print("=" * 78)
    print(f"Test set: {fmt(TEST_SIZE)} email (20% cua {fmt(TOTAL_VALID)} email hop le; "
          f"file goc {fmt(TOTAL_ROWS)} dong, loai null xong con {fmt(TOTAL_VALID)})")
    print()
    print(f"  TP = {fmt(tp):>8}  (bat dung phishing)")
    print(f"  FN = {fmt(fn):>8}  (bo rot phishing)     <- FNR")
    print(f"  FP = {fmt(fp):>8}  (bao dong gia)        <- FPR")
    print(f"  TN = {fmt(tn):>8}  (nhan dung hop le)")
    print()
    print(f"  FNR      = {fmt(fn)} / ({fmt(fn)} + {fmt(tp)})"
          f"     = {fmt(fn)}/{fmt(fn + tp)}        = {pct(fnr)}")
    print(f"  FPR      = {fmt(fp)} / ({fmt(fp)} + {fmt(tn)})"
          f"     = {fmt(fp)}/{fmt(fp + tn)}        = {pct(fpr)}")
    print(f"  Accuracy = ({fmt(tp)} + {fmt(tn)})/{fmt(TEST_SIZE)}"
          f" = {fmt(tp + tn)}/{fmt(TEST_SIZE)} = {pct(acc)}")
    print(f"  Precision= {fmt(tp)} / ({fmt(tp)} + {fmt(fp)})"
          f" = {fmt(tp)}/{fmt(tp + fp)} = {pct(precision)}")
    print(f"  Recall   = {fmt(tp)} / ({fmt(tp)} + {fmt(fn)})"
          f" = {fmt(tp)}/{fmt(tp + fn)} = {pct(recall)}")
    print(f"  F1       = 2 x ({precision:.2f} x {recall:.2f})"
          f"/({precision:.2f} + {recall:.2f}) = {pct(f1)}")
    print()

    # Kiem tra khop voi CSV (chong lech so lieu khi trinh bay)
    mismatches = []
    checks = [
        ("Accuracy", pct(acc)),
        ("FNR", pct(fnr)),
        ("FPR", pct(fpr)),
    ]
    for col, computed in checks:
        if str(row.get(col, "")) != computed:
            mismatches.append(f"{col}: CSV={row.get(col)} vs tinh={computed}")
    if mismatches:
        print("  [CANH BAO] Lech so lieu CSV:")
        for m in mismatches:
            print(f"    - {m}")
        print()
    else:
        print("  [OK] Khop voi results/model_comparison.csv")
        print()


# Tu khoa rat ngan cho tung model (khong phan biet hoa/thuong)
MODEL_KEYS = {
    "rf": "Random Forest",
    "random": "Random Forest",
    "lr": "Logistic Regression",
    "logistic": "Logistic Regression",
    "xgb": "XGBoost",
    "xgboost": "XGBoost",
    "mnb": "Multinomial Naive Bayes",
    "naive": "Multinomial Naive Bayes",
    "nb": "Multinomial Naive Bayes",
}


def pick_models(df: pd.DataFrame, arg: str | None) -> pd.DataFrame:
    """Loc 1 model theo tu khoa; khong truyen thi lay toan bo."""
    if not arg:
        return df
    key = MODEL_KEYS.get(arg.strip().lower())
    if key is None:
        # neu user go truc tiep ten day du chua tu khoa
        hit = df[df["Model"].str.contains(arg, case=False, na=False)]
        if hit.empty:
            print(f"Khong tim thay model chua '{arg}'.")
            print("Tu khoa hop le: rf | lr | xgb | mnb")
            sys.exit(1)
        return hit
    hit = df[df["Model"].str.contains(key, case=False, na=False)]
    if hit.empty:
        print(f"Khong tim thay model '{key}' trong CSV.")
        sys.exit(1)
    return hit


def main() -> None:
    if not RESULTS_CSV.exists():
        print(f"Khong tim thay {RESULTS_CSV}")
        print("Chay truoc:  python -X utf8 scripts/compare_models.py")
        sys.exit(1)

    df = pd.read_csv(RESULTS_CSV, encoding="utf-8-sig")
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    df = pick_models(df, arg)

    # Thu tu in: model van hanh truoc, roi 3 model con lai theo F1 giam dan
    order = []
    for key in ["Random Forest", "Logistic", "XGBoost", "Multinomial"]:
        hit = df[df["Model"].str.contains(key, case=False, na=False)]
        if not hit.empty:
            order.append(hit.index[0])
    order += [i for i in df.index if i not in order]

    print()
    print("#" * 78)
    print("#  DEMO CHI TAY 4 MO HINH - HE THONG PHAT HIEN EMAIL PHISHING")
    print(f"#  Dataset: merged_clean.csv - {fmt(TOTAL_ROWS)} dong, "
          f"{fmt(TOTAL_VALID)} email hop le (sau dropna)")
    print(f"#  Split 80/20 stratified, seed=42 -> Train {fmt(TRAIN_SIZE)}"
          f" / Test {fmt(TEST_SIZE)}")
    print("#  Features: TF-IDF 30,000 + 9 Security = 30,009 chieu")
    print("#" * 78)
    print()

    for i in order:
        print_model(df.loc[i])

    # Bang tong hop cuoi cung
    print("=" * 78)
    print("TONG HOP (tinh tu TP/FP/TN/FN nhu tren)")
    print("=" * 78)
    header = (f"{'Model':<30}{'Acc':>9}{'FNR':>9}{'FPR':>9}"
              f"{'Precis':>9}{'Recall':>9}{'F1':>9}")
    print(header)
    print("-" * len(header))
    for i in order:
        r = df.loc[i]
        tp, fp, tn, fn = int(r["TP"]), int(r["FP"]), int(r["TN"]), int(r["FN"])
        acc = (tp + tn) / (tp + tn + fp + fn) * 100
        fnr = fn / (fn + tp) * 100
        fpr = fp / (fp + tn) * 100
        prec = tp / (tp + fp) * 100
        rec = tp / (tp + fn) * 100
        f1 = 2 * prec * rec / (prec + rec)
        print(f"{str(r['Model'])[:29]:<30}{pct(acc):>9}{pct(fnr):>9}"
              f"{pct(fpr):>9}{pct(prec):>9}{pct(rec):>9}{pct(f1):>9}")
    print()
    print("LUU Y KHI TRINH BAY:")
    print("- Cac so % o bang chinh (Accuracy/F1/...) la gia tri weighted")
    print("  (trung binh co trong 2 lop) - xem results/model_comparison.csv.")
    print("- Precision/Recall/F1 rieng o tren day la CUA LOP PHISHING (1),")
    print("  tinh bang cong thuc Precision=TP/(TP+FP) nhu GVHD yeu cau.")
    print("  Vi du RF: weighted F1 = 97.23%, phishing-class F1 = 97.10%.")
    print()


if __name__ == "__main__":
    main()
