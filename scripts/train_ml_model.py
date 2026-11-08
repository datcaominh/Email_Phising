"""Train RandomForestClassifier + TfidfVectorizer cho email phishing.

Input:
    data_train/processed/merged_clean.csv (206K email - Champa et al. 2024)
    Hoac: data_train/CEAS_08.csv (dataset cu 39K)

Output:
    app/models/phishing_rf.pkl

Cach chay:
    python scripts/train_ml_model.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from app.features import SecurityFeatureExtractor
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data_train" / "processed" / "merged_clean.csv"
MODEL_PATH = PROJECT_ROOT / "app" / "models" / "phishing_rf.pkl"


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


def main() -> None:
    """Doc CSV, train/test split, train pipeline va luu file .pkl."""
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Khong tim thay dataset: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, low_memory=False)
    required_columns = {"sender", "receiver", "subject", "body", "label", "urls"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Dataset thieu cot: {sorted(missing)}")

    df = df.dropna(subset=["subject", "body", "label"]).copy()
    df["label"] = df["label"].astype(int)
    texts = df.apply(combine_text, axis=1)
    labels = df["label"]

    pipeline = Pipeline(
        steps=[
            (
                "features",
                FeatureUnion(
                    [
                        ("tfidf", TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=1)),
                        ("security", SecurityFeatureExtractor()),
                    ]
                ),
            ),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                    max_depth=30,
                ),
            ),
        ]
    )

    class_counts = labels.value_counts()
    can_split = len(df) >= 10 and class_counts.min() >= 2
    if can_split:
        x_train, x_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=0.2,
            random_state=42,
            stratify=labels,
        )
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        print(classification_report(y_test, predictions, digits=4))
    else:
        # Dataset mau trong repo rat nho; train tren toan bo du lieu de tao .pkl demo.
        print("Dataset qua nho de chia train/test stratified; train demo tren toan bo du lieu.")
        pipeline.fit(texts, labels)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Da luu model tai: {MODEL_PATH}")


if __name__ == "__main__":
    main()
