"""So sanh 4 model ML cho phishing email detection.

Mo hinh so sanh:
    1. Random Forest (200 cay)     - model hien tai (baseline)
    2. Logistic Regression
    3. Multinomial Naive Bayes
    4. XGBoost

Input:  data_train/processed/merged_clean.csv (206K email)
Output: results/model_comparison.csv  (bang chi tat ca chi so)
        results/roc_comparison.png    (bieu do ROC so sanh 4 model)
        results/confusion_matrix_<rf|lr|mnb|xgb>.png
                                     (ma tran nham lan heatmap, dung chen bao cao)

Cach chay:
    python scripts/compare_models.py                # toan bo 4 model
    python scripts/compare_models.py "Logistic"     # chi 1 model
"""

from __future__ import annotations

import sys
import time
import csv
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    roc_curve,
    roc_auc_score,
)

from app.features import SecurityFeatureExtractor

# Optional import (XGBoost)
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data_train" / "processed" / "merged_clean.csv"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_CSV = RESULTS_DIR / "model_comparison.csv"
ROC_PNG = RESULTS_DIR / "roc_comparison.png"

# Ten file dung cho anh ma tran nham lan (app + bao cao doc tai truc tiep)
CM_KEYS = {
    "Random Forest (200 cay)": "rf",
    "Logistic Regression": "lr",
    "Multinomial Naive Bayes": "mnb",
    "XGBoost": "xgb",
}
CM_LABELS = {
    "rf": "Random Forest",
    "lr": "Logistic Regression",
    "mnb": "Multinomial Naive Bayes",
    "xgb": "XGBoost",
}


def combine_text(row: pd.Series) -> str:
    """Gop metadata + subject + body + urls thanh text dau vao cho model."""
    return f"""
Sender: {row.get("sender", "")}
Receiver: {row.get("receiver", "")}
Subject: {row.get("subject", "")}
URLs: {row.get("urls", "")}

Body:
{row.get("body", "")}
""".strip()


def build_models() -> dict:
    """Dinh nghia cac model can so sanh (4 model)."""
    models = {
        "Random Forest (200 cay)": RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            max_depth=30,
        ),
        "Logistic Regression": LogisticRegression(
            max_iter=5000,
            random_state=42,
            solver="saga",
            tol=1e-4,
        ),
        "Multinomial Naive Bayes": MultinomialNB(alpha=1.0),
    }

    if HAS_XGB:
        models["XGBoost"] = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            eval_metric="logloss",
            verbosity=0,
        )

    return models


def save_confusion_matrix_png(
    key: str, cm: np.ndarray, y_true: np.ndarray, y_pred: np.ndarray
) -> Path:
    """Ve ma tran nham lan 2x2 dang heatmap, luu results/confusion_matrix_<key>.png.

    Moi o hien so email + ty le trong tong test set. Dung chen truc tiep
    vao bao cao Word/PowerPoint (thay cho in bang text).
    """
    tn, fp, fn, tp = cm.ravel()
    total = cm.sum()
    labels = ["Not Phishing (0)", "Phishing (1)"]
    cell_text = [
        [f"TN = {tn:,}\n({tn/total*100:.2f}%)", f"FP = {fp:,}\n({fp/total*100:.2f}%)"],
        [f"FN = {fn:,}\n({fn/total*100:.2f}%)", f"TP = {tp:,}\n({tp/total*100:.2f}%)"],
    ]

    fig, ax = plt.subplots(figsize=(5.4, 4.6), dpi=150)
    im = ax.imshow(cm, cmap="Blues")

    ax.set_xticks([0, 1], labels=labels, fontsize=9)
    ax.set_yticks([0, 1], labels=labels, fontsize=9)
    ax.set_xlabel("Dự đoán của mô hình", fontsize=10)
    ax.set_ylabel("Nhãn thực tế", fontsize=10)
    ax.set_title(f"Ma trận nhầm lẫn — {CM_LABELS.get(key, key)}", fontsize=11)

    # Ghi so len tung o; mau chu trang neu o toi (chu xanh se kho doc)
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() * 0.6 else "black"
            ax.text(
                j, i, cell_text[i][j],
                ha="center", va="center", fontsize=10, color=color, fontweight="bold",
            )

    fig.tight_layout()
    out = RESULTS_DIR / f"confusion_matrix_{key}.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def save_roc_png(roc_data: dict) -> Path:
    """Ve bieu do ROC so sanh cac model da train, luu results/roc_comparison.png.

    roc_data: {ten model: (fpr, tpr, auc_value)}
    """
    fig, ax = plt.subplots(figsize=(7.0, 5.2), dpi=150)

    # Duong chong: mo hinh doan ngau nhien (AUC = 0.5)
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Ngẫu nhiên (AUC = 0.5)")

    colors = {
        "Random Forest (200 cay)": "#1f77b4",
        "Logistic Regression": "#d62728",
        "Multinomial Naive Bayes": "#2ca02c",
        "XGBoost": "#ff7f0e",
    }
    for name, (fpr, tpr, auc_value) in roc_data.items():
        color = colors.get(name)
        short = name.replace(" (200 cay)", "")
        ax.plot(fpr, tpr, linewidth=2, color=color,
                label=f"{short} (AUC = {auc_value:.4f})")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.5, 1.0])
    ax.set_xlabel("FPR — Tỷ lệ báo giả (False Positive Rate)", fontsize=10)
    ax.set_ylabel("TPR — Tỷ lệ bắt được (True Positive Rate / Recall)", fontsize=10)
    ax.set_title("So sánh ROC Curve của 4 mô hình", fontsize=12)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(ROC_PNG, bbox_inches="tight")
    plt.close(fig)
    return ROC_PNG


def main() -> None:
    print("=" * 70)
    print("SO SANH MODEL - PHISHING EMAIL DETECTION")
    print("=" * 70)
    print(f"XGBoost: {'CO' if HAS_XGB else 'KHONG CAI'}")
    print()

    # --- 1. Doc dataset ---
    print("[1/4] Doc dataset...")
    t0 = time.time()
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    df = df.dropna(subset=["subject", "body", "label"]).copy()
    df["label"] = df["label"].astype(int)
    texts = df.apply(combine_text, axis=1)
    labels = df["label"]
    print(f"      {len(df):,} email ({time.time()-t0:.1f}s)")
    print(f"      Phishing: {(labels==1).sum():,} | Legit: {(labels==0).sum():,}")

    # --- 2. Train/test split (giu nguyen 80/20 stratified, seed 42) ---
    print("[2/4] Chia train/test 80/20 (stratified, seed=42)...")
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"      Train: {len(x_train):,} | Test: {len(x_test):,}")

    # --- 3. Feature extraction (TF-IDF 30K + 9 security features) ---
    print("[3/4] Trich dac trung TF-IDF + Security Features...")
    t0 = time.time()
    feature_union = FeatureUnion(
        [
            ("tfidf", TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=1)),
            ("security", SecurityFeatureExtractor()),
        ]
    )
    x_train_features = feature_union.fit_transform(x_train)
    x_test_features = feature_union.transform(x_test)
    print(
        f"      Features: {x_train_features.shape[1]:,} | "
        f"Train shape: {x_train_features.shape} ({time.time()-t0:.1f}s)"
    )

    # --- 4. Train + danh gia tung model ---
    print("[4/4] Train va danh gia cac model...")
    print()
    print("=" * 70)

    models = build_models()
    # Cho phep chay 1 model cu the: python scripts/compare_models.py "Logistic"
    if len(sys.argv) > 1:
        pick = sys.argv[1]
        models = {k: v for k, v in models.items() if pick.lower() in k.lower()}
        if not models:
            raise SystemExit(f"Khong tim thay model chua '{pick}'")
    results = []
    roc_data: dict = {}

    RESULTS_DIR.mkdir(exist_ok=True)

    for name, model in models.items():
        print(f"\n--- {name} ---")

        # TF-IDF + security features da la sparse va khong am
        # → dung truc tiep cho RF/MNB/XGB (tranh hap bo nho)
        # Rieng LR can scale de saga hoi tu tot tren ma tran thua
        if "Logistic" in name:
            from sklearn.preprocessing import MaxAbsScaler
            scaler = MaxAbsScaler()
            xtr = scaler.fit_transform(x_train_features)
            xte = scaler.transform(x_test_features)
        else:
            xtr = x_train_features
            xte = x_test_features

        # Train
        t0 = time.time()
        model.fit(xtr, y_train)
        train_time = time.time() - t0

        # Predict
        t0 = time.time()
        y_pred = model.predict(xte)
        predict_time = time.time() - t0

        # Xac suat + ROC/AUC (dung cho bieu do ROC va ma tran nham lan)
        class_idx = list(model.classes_).index(1)
        y_proba = model.predict_proba(xte)[:, class_idx]
        fpr_curve, tpr_curve, _ = roc_curve(y_test, y_proba)
        auc_value = roc_auc_score(y_test, y_proba)
        roc_data[name] = (fpr_curve, tpr_curve, auc_value)

        # Metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average="weighted")
        rec = recall_score(y_test, y_pred, average="weighted")
        f1 = f1_score(y_test, y_pred, average="weighted")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn)
        fnr = fn / (fn + tp)
        specificity = tn / (tn + fp)

        # Luu anh ma tran nham lan (app doc truc tiep file nay)
        cm_path = save_confusion_matrix_png(CM_KEYS.get(name, "rf"), cm, y_test, y_pred)
        print(f"      Anh ma tran nham lan: {cm_path.name}")

        results.append(
            {
                "Model": name,
                "Accuracy": f"{acc*100:.2f}%",
                "Precision (weighted)": f"{prec*100:.2f}%",
                "Recall (weighted)": f"{rec*100:.2f}%",
                "F1 (weighted)": f"{f1*100:.2f}%",
                "ROC AUC": f"{auc_value:.4f}",
                "FPR": f"{fpr*100:.2f}%",
                "FNR": f"{fnr*100:.2f}%",
                "Specificity": f"{specificity*100:.2f}%",
                "Train time": f"{train_time:.1f}s",
                "Predict time": f"{predict_time:.2f}s",
                "TP": int(tp),
                "FP": int(fp),
                "TN": int(tn),
                "FN": int(fn),
            }
        )

        print(f"      Accuracy:  {acc*100:.2f}%")
        print(f"      Precision: {prec*100:.2f}%")
        print(f"      Recall:    {rec*100:.2f}%")
        print(f"      F1:        {f1*100:.2f}%")
        print(f"      ROC AUC:   {auc_value:.4f}")
        print(f"      FPR:       {fpr*100:.2f}% | FNR: {fnr*100:.2f}%")
        print(f"      Train: {train_time:.1f}s | Predict: {predict_time:.2f}s")

    # --- Bieu do ROC so sanh cac model ---
    if len(roc_data) >= 1:
        roc_path = save_roc_png(roc_data)
        print()
        print(f"Bieu do ROC da luu: {roc_path}")

    # --- Luu ket qua ---
    RESULTS_DIR.mkdir(exist_ok=True)
    results_df = pd.DataFrame(results)
    results_df.to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")

    # --- In bang tong hop ---
    print()
    print("=" * 70)
    print("BANG TONG HOP KET QUA")
    print("=" * 70)
    display_cols = [
        "Model", "Accuracy", "Precision (weighted)", "Recall (weighted)",
        "F1 (weighted)", "ROC AUC", "FPR", "FNR", "Train time", "Predict time",
    ]
    print(results_df[display_cols].to_string(index=False))

    # --- Xep hang theo F1 ---
    print()
    print("=" * 70)
    print("XEP HANG THEO F1-SCORE (giam dan)")
    print("=" * 70)
    results_df_sorted = results_df.sort_values(
        by="F1 (weighted)", ascending=False
    )
    for i, (_, row) in enumerate(results_df_sorted.iterrows(), 1):
        print(f"  {i}. {row['Model']:<30} F1={row['F1 (weighted)']} | Acc={row['Accuracy']}")

    print()
    print(f"Da luu ket qua: {RESULTS_CSV}")


if __name__ == "__main__":
    main()
