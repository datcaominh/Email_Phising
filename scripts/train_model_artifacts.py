"""Train and save the four ML model pipelines for runtime selection.

Fits preprocessing on the complete cleaned corpus, then stores one artifact per
classifier under app/models. This is for final deployment artifacts, not an
unbiased evaluation; use compare_models.py for held-out metrics.
"""
from __future__ import annotations

import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import MaxAbsScaler
from xgboost import XGBClassifier
from app.features import SecurityFeatureExtractor

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_train" / "processed" / "merged_clean.csv"
OUT = ROOT / "app" / "models"

def combine_text(row: pd.Series) -> str:
    return (f"Sender: {row.get('sender', '')}\n"
            f"Receiver: {row.get('receiver', '')}\n"
            f"Subject: {row.get('subject', '')}\n"
            f"URLs: {row.get('urls', '')}\n\n"
            f"Body:\n{row.get('body', '')}").strip()

def main() -> None:
    df = pd.read_csv(DATA, low_memory=False).dropna(subset=["subject", "body", "label"]).copy()
    df["label"] = df["label"].astype(int)
    texts = df.apply(combine_text, axis=1).tolist()
    labels = df["label"].to_numpy()
    print(f"Fitting shared feature pipeline on {len(df):,} emails", flush=True)
    features = FeatureUnion([
        ("tfidf", TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=1)),
        ("security", SecurityFeatureExtractor()),
    ])
    X = features.fit_transform(texts)
    print(f"Feature matrix: {X.shape}; nnz={X.nnz:,}", flush=True)
    models = [
        ("rf", RandomForestClassifier(n_estimators=200, max_depth=40, class_weight="balanced", random_state=42, n_jobs=-1), None),
        ("lr", LogisticRegression(max_iter=5000, random_state=42, solver="saga", tol=1e-4, C=1.0), MaxAbsScaler()),
        ("mnb", MultinomialNB(alpha=0.01), None),
        ("xgb", XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.2, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1, eval_metric="logloss", verbosity=0), None),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    for key, clf, scaler in models:
        start = time.time()
        X_fit = scaler.fit_transform(X) if scaler is not None else X
        clf.fit(X_fit, labels)
        artifact = {"name": key, "features": features, "scaler": scaler, "classifier": clf, "training_rows": len(df)}
        target = OUT / f"phishing_{key}.pkl"
        joblib.dump(artifact, target, compress=3)
        print(f"Saved {target.name} ({target.stat().st_size / 1024 / 1024:.1f} MB) in {time.time()-start:.1f}s", flush=True)
        del artifact, X_fit, clf

if __name__ == "__main__":
    main()
