# -*- coding: utf-8 -*-
"""Phan tich anh huong nguong quyet dinh 50% vs 70%.

Chay tren cung dataset/split/features nhu compare_models.py:
- RF (model dang deploy) + LR
- Moi model danh gia o nguong 50/60/70/80
- Ban ve (guardrail): final = max(diem_ML, diem_heuristic) cung cac nguong

Output: results/threshold_analysis.csv
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MaxAbsScaler
from scipy.sparse import hstack

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.features import SecurityFeatureExtractor  # noqa: E402
from app.ml_engine import heuristic_score  # noqa: E402

INPUT_CSV = PROJECT_ROOT / "data_train" / "processed" / "merged_clean.csv"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_CSV = RESULTS_DIR / "threshold_analysis.csv"

THRESHOLDS = [50, 60, 70, 80]
URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+|www\.[^\s<>\]\)\"']+", re.I)


def combine_text(row: pd.Series) -> str:
    return f"""
Sender: {row.get("sender", "")}
Receiver: {row.get("receiver", "")}
Subject: {row.get("subject", "")}
URLs: {row.get("urls", "")}

Body:
{row.get("body", "")}
""".strip()


def metrics_block(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "Accuracy": f"{accuracy_score(y_true, y_pred) * 100:.2f}%",
        "Precision": f"{precision_score(y_true, y_pred, zero_division=0) * 100:.2f}%",
        "Recall": f"{recall_score(y_true, y_pred, zero_division=0) * 100:.2f}%",
        "F1": f"{f1_score(y_true, y_pred, zero_division=0) * 100:.2f}%",
        "FPR": f"{fp / max(fp + tn, 1) * 100:.2f}%",
        "FNR": f"{fn / max(fn + tp, 1) * 100:.2f}%",
        "TP": int(tp),
        "FP": int(fp),
        "TN": int(tn),
        "FN": int(fn),
    }


def main() -> None:
    print("=" * 70)
    print("PHAN TICH NGUONG 50% vs 70%")
    print("=" * 70)

    print("[1/5] Doc dataset...")
    t0 = time.time()
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    df = df.dropna(subset=["subject", "body", "label"]).copy()
    df["label"] = df["label"].astype(int)
    texts = df.apply(combine_text, axis=1)
    labels = df["label"]
    print(f"      {len(df):,} email ({time.time() - t0:.1f}s)")

    print("[2/5] Chia train/test 80/20 (stratified, seed=42)...")
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    y_true = y_test.to_numpy()
    print(f"      Train: {len(x_train):,} | Test: {len(x_test):,}")

    print("[3/5] Trich dac trung TF-IDF + Security Features...")
    t0 = time.time()
    feature_union = FeatureUnion(
        [
            ("tfidf", TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=1)),
            ("security", SecurityFeatureExtractor()),
        ]
    )
    x_train_feat = feature_union.fit_transform(x_train)
    x_test_feat = feature_union.transform(x_test)
    print(f"      Features: {x_train_feat.shape[1]:,} ({time.time() - t0:.1f}s)")

    # LR can scaling (MaxAbs giu tinh thua cua ma tran TF-IDF)
    scaler = MaxAbsScaler()
    x_train_lr = scaler.fit_transform(x_train_feat)
    x_test_lr = scaler.transform(x_test_feat)

    print("[4/5] Train RF + Logistic Regression...")
    t0 = time.time()
    rf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        max_depth=30,
    )
    rf.fit(x_train_feat, y_train)
    print(f"      RF xong ({time.time() - t0:.1f}s)")
    t0 = time.time()
    lr = LogisticRegression(
        max_iter=5000, random_state=42, solver="saga", tol=1e-4, C=1.0
    )
    lr.fit(x_train_lr, y_train)
    print(f"      LR xong ({time.time() - t0:.1f}s)")

    proba_rf = rf.predict_proba(x_test_feat)[:, list(rf.classes_).index(1)] * 100
    proba_lr = lr.predict_proba(x_test_lr)[:, list(lr.classes_).index(1)] * 100

    print("[5/5] Tinh heuristic guardrail cho test set...")
    t0 = time.time()
    heur = np.array(
        [
            float(heuristic_score(t, URL_RE.findall(t))["score"])
            for t in x_test
        ]
    )
    print(f"      xong ({time.time() - t0:.1f}s)")

    rows = []
    for name, proba in [("RF", proba_rf), ("LR", proba_lr)]:
        for th in THRESHOLDS:
            # Model don le
            m = metrics_block(y_true, (proba >= th).astype(int))
            rows.append({"Setup": f"{name} (model don le)", "Threshold": f"{th}%", **m})
            # Co guardrail heuristic
            final = np.maximum(proba, heur)
            m2 = metrics_block(y_true, (final >= th).astype(int))
            rows.append({"Setup": f"{name} + guardrail heuristic", "Threshold": f"{th}%", **m2})

    out = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    out.to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")

    show = ["Setup", "Threshold", "Accuracy", "F1", "FPR", "FNR", "FP", "FN"]
    print()
    print("=" * 70)
    print("KET QUA (xep theo Setup, Threshold)")
    print("=" * 70)
    print(out[show].to_string(index=False))
    print()
    print(f"Da luu: {RESULTS_CSV}")


if __name__ == "__main__":
    main()
