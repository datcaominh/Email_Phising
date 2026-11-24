"""Compare single models and probability ensembles on leakage-aware splits.

Runs two evaluations on merged_clean.csv:
1. Content-group split: identical normalized bodies stay on one side.
2. Source holdout: CEAS_08 is held out from training.

This experiment does not modify the production model. Results are written to
results/ensemble_robustness.csv for review before any deployment decision.
"""
from __future__ import annotations

import hashlib
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
    brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import MaxAbsScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.features import SecurityFeatureExtractor

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_train" / "processed" / "merged_clean.csv"
OUT = ROOT / "results" / "ensemble_robustness.csv"


def text_of(row: pd.Series) -> str:
    return (f"Sender: {row.get('sender', '')}\nReceiver: {row.get('receiver', '')}"
            f"\nSubject: {row.get('subject', '')}\nURLs: {row.get('urls', '')}"
            f"\nBody:\n{row.get('body', '')}")


def content_group(body: object) -> str:
    value = re.sub(r"\s+", " ", str(body or "").lower()).strip()
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def build_models() -> dict:
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=200, class_weight="balanced",
            random_state=42, n_jobs=-1, max_depth=30),
        "Logistic Regression": LogisticRegression(max_iter=5000, random_state=42,
            solver="saga", tol=1e-4),
        "Multinomial Naive Bayes": MultinomialNB(alpha=1.0),
    }
    if XGBClassifier is not None:
        models["XGBoost"] = XGBClassifier(n_estimators=200, max_depth=6,
            learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, eval_metric="logloss", verbosity=0)
    return models


def score_row(split: str, name: str, y: np.ndarray, p: np.ndarray,
              fit_seconds: float) -> dict:
    pred = (p >= 0.5).astype(int)
    return {
        "split": split, "model": name, "n_test": int(len(y)),
        "accuracy": accuracy_score(y, pred),
        "precision_phishing": precision_score(y, pred, zero_division=0),
        "recall_phishing": recall_score(y, pred, zero_division=0),
        "f1_phishing": f1_score(y, pred, zero_division=0),
        "f1_macro": f1_score(y, pred, average="macro", zero_division=0),
        "roc_auc": roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan,
        "average_precision": average_precision_score(y, p),
        "brier": brier_score_loss(y, p), "fit_seconds": fit_seconds,
    }


def evaluate(df: pd.DataFrame, split: str, train_idx: np.ndarray,
             test_idx: np.ndarray) -> list[dict]:
    train = df.iloc[train_idx]
    test = df.iloc[test_idx]
    y_train = train.label.to_numpy()
    y_test = test.label.to_numpy()
    print(f"\n[{split}] train={len(train):,}, test={len(test):,}; "
          f"test classes={dict(pd.Series(y_test).value_counts().sort_index())}", flush=True)
    union = FeatureUnion([
        ("tfidf", TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=1)),
        ("security", SecurityFeatureExtractor()),
    ])
    t = time.time()
    x_train = union.fit_transform(train.text)
    x_test = union.transform(test.text)
    print(f"features={x_train.shape[1]:,}; transform={time.time()-t:.1f}s", flush=True)

    models = build_models()
    probabilities = {}
    rows = []
    for name, model in models.items():
        if name == "Logistic Regression":
            scaler = MaxAbsScaler()
            xtr = scaler.fit_transform(x_train)
            xte = scaler.transform(x_test)
        else:
            xtr, xte = x_train, x_test
        t = time.time()
        model.fit(xtr, y_train)
        elapsed = time.time() - t
        classes = list(model.classes_)
        probs = model.predict_proba(xte)[:, classes.index(1)]
        probabilities[name] = probs
        row = score_row(split, name, y_test, probs, elapsed)
        rows.append(row)
        print(f"{name}: acc={row['accuracy']:.4f}, F1={row['f1_phishing']:.4f}, "
              f"AUC={row['roc_auc']:.4f}, fit={elapsed:.1f}s", flush=True)

    # Predeclared equal-weight soft-voting candidates; no test-based weight tuning.
    candidates = [
        ("Soft vote LR+RF", ["Logistic Regression", "Random Forest"]),
        ("Soft vote LR+XGB", ["Logistic Regression", "XGBoost"]),
        ("Soft vote RF+XGB", ["Random Forest", "XGBoost"]),
        ("Soft vote LR+RF+XGB", ["Logistic Regression", "Random Forest", "XGBoost"]),
    ]
    for name, members in candidates:
        if all(m in probabilities for m in members):
            row = score_row(split, name, y_test,
                np.mean([probabilities[m] for m in members], axis=0), 0.0)
            rows.append(row)
            print(f"{name}: acc={row['accuracy']:.4f}, F1={row['f1_phishing']:.4f}, "
                  f"AUC={row['roc_auc']:.4f}", flush=True)
    return rows


def main() -> None:
    df = pd.read_csv(DATA, low_memory=False)
    df = df.dropna(subset=["subject", "body", "label", "source"]).copy()
    df["label"] = df.label.astype(int)
    df["text"] = df.apply(text_of, axis=1)
    df["body_group"] = df.body.map(content_group)
    print(f"rows={len(df):,}; sources={df.source.nunique()}; "
          f"repeated bodies={df.body.duplicated().sum():,}; "
          f"label mix={df.label.value_counts(normalize=True).round(4).to_dict()}", flush=True)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_g, test_g = next(splitter.split(df, df.label, groups=df.body_group))
    rows = evaluate(df, "body_group_holdout", train_g, test_g)

    heldout = "CEAS_08"
    test_mask = df.source.eq(heldout).to_numpy()
    train_s = np.flatnonzero(~test_mask)
    test_s = np.flatnonzero(test_mask)
    if len(test_s) and df.iloc[train_s].label.nunique() == 2 and df.iloc[test_s].label.nunique() == 2:
        rows += evaluate(df, f"source_holdout_{heldout}", train_s, test_s)
    else:
        print(f"Skipping source holdout {heldout}: missing class in train or test", flush=True)

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")
    print("\nSummary (sorted by F1):")
    print(result.sort_values(["split", "f1_phishing"], ascending=[True, False])[
        ["split", "model", "n_test", "accuracy", "precision_phishing",
         "recall_phishing", "f1_phishing", "f1_macro", "roc_auc", "brier"]
    ].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print(f"\nSaved {OUT}")


if __name__ == "__main__":
    main()
