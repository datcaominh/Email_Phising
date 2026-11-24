"""Reproducible, validation-only hyperparameter experiments for the report.

The untouched 20% outer test split is deliberately excluded from parameter
selection. A fixed stratified 25k/5k subset is drawn from the outer training
partition for a practical one-factor-at-a-time parameter screen.
"""
from __future__ import annotations

import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, log_loss,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import MaxAbsScaler

from app.features import SecurityFeatureExtractor

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_train" / "processed" / "merged_clean.csv"
OUT = ROOT / "results" / "hyperparameter_search.csv"
LR_TRACE_OUT = ROOT / "results" / "lr_convergence_trace.csv"
SEED = 42
TUNE_TRAIN_SIZE = 25_000
TUNE_VALID_SIZE = 5_000
XGB_TRAIN_SIZE = 10_000


def make_text(row: pd.Series) -> str:
    return (f"Sender: {row.get('sender', '')}\n"
            f"Receiver: {row.get('receiver', '')}\n"
            f"Subject: {row.get('subject', '')}\n"
            f"URLs: {row.get('urls', '')}\n\n"
            f"Body:\n{row.get('body', '')}").strip()


def score(name: str, params: dict, model, xtr, ytr, xv, yv,
          fit_seconds: float, warning: bool = False) -> dict:
    pval = model.predict_proba(xv)[:, list(model.classes_).index(1)]
    pred = (pval >= 0.5).astype(int)
    return {
        "model": name,
        "params": repr(params),
        "n_train": len(ytr),
        "n_validation": len(yv),
        "sample_protocol": f"{len(ytr)} train / {len(yv)} validation",
        "accuracy": accuracy_score(yv, pred),
        "precision_phishing": precision_score(yv, pred, zero_division=0),
        "recall_phishing": recall_score(yv, pred, zero_division=0),
        "f1_phishing": f1_score(yv, pred, zero_division=0),
        "roc_auc": roc_auc_score(yv, pval),
        "validation_logloss": log_loss(yv, pval),
        "fit_seconds": fit_seconds,
        "n_iter": int(model.n_iter_[0]) if hasattr(model, "n_iter_") else "",
        "convergence_warning": warning,
    }


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(DATA)
    print("Reading cleaned corpus...", flush=True)
    df = pd.read_csv(DATA, low_memory=False)
    df = df.dropna(subset=["subject", "body", "label"]).copy()
    df["label"] = df["label"].astype(int)
    labels = df["label"].to_numpy()

    all_idx = np.arange(len(df))
    outer_train, outer_test = train_test_split(
        all_idx, test_size=0.2, random_state=SEED, stratify=labels
    )
    # The 20% outer test set is never loaded into the feature transformer/model.
    tune_train, tune_valid = train_test_split(
        outer_train, train_size=TUNE_TRAIN_SIZE, test_size=TUNE_VALID_SIZE,
        random_state=SEED + 1, stratify=labels[outer_train]
    )
    print(f"rows={len(df):,}; tune_train={len(tune_train):,}; "
          f"validation={len(tune_valid):,}; untouched_outer_test={len(outer_test):,}",
          flush=True)

    text = df.apply(make_text, axis=1)
    train_text = text.iloc[tune_train]
    valid_text = text.iloc[tune_valid]
    ytr = labels[tune_train]
    yv = labels[tune_valid]

    union = FeatureUnion([
        ("tfidf", TfidfVectorizer(max_features=30_000,
                                  ngram_range=(1, 2), min_df=1)),
        ("security", SecurityFeatureExtractor()),
    ])
    started = time.time()
    xtr = union.fit_transform(train_text)
    xv = union.transform(valid_text)
    print(f"features={xtr.shape[1]:,}; transform_seconds={time.time()-started:.1f}",
          flush=True)

    rows: list[dict] = []
    # LR trace: warm-started SAGA chunks record the training objective and
    # coefficient changes. This is diagnostic; it does not choose parameters
    # from the untouched outer test split.
    scaler = MaxAbsScaler()
    xtr_lr = scaler.fit_transform(xtr)
    xv_lr = scaler.transform(xv)
    rng = np.random.RandomState(SEED)
    lr = LogisticRegression(max_iter=50, random_state=rng, solver="saga",
                            tol=1e-4, C=1.0, warm_start=True)
    trace_rows = []
    prev_coef = None
    cumulative = 0
    for chunk in range(1, 101):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            start = time.time()
            lr.fit(xtr_lr, ytr)
            chunk_seconds = time.time() - start
        warn = any(issubclass(w.category, ConvergenceWarning) for w in caught)
        used = int(lr.n_iter_[0])
        cumulative += used
        coef = lr.coef_.copy()
        delta = float(np.linalg.norm(coef - prev_coef)) if prev_coef is not None else np.nan
        prev_coef = coef
        train_p = lr.predict_proba(xtr_lr)[:, 1]
        valid_p = lr.predict_proba(xv_lr)[:, 1]
        train_loss = log_loss(ytr, train_p)
        valid_pred = (valid_p >= 0.5).astype(int)
        trace_rows.append({
            "cumulative_iterations": cumulative,
            "chunk_iterations": used,
            "train_logloss": train_loss,
            "validation_logloss": log_loss(yv, valid_p),
            "validation_accuracy": accuracy_score(yv, valid_pred),
            "validation_f1_phishing": f1_score(yv, valid_pred),
            "coefficient_l2_norm": float(np.linalg.norm(coef)),
            "coefficient_delta_l2": delta,
            "convergence_warning": warn,
            "chunk_fit_seconds": chunk_seconds,
        })
        print(f"LR trace: total_iter={cumulative}; train_logloss={train_loss:.6f}; "
              f"valid_logloss={trace_rows[-1]['validation_logloss']:.6f}; "
              f"warning={warn}", flush=True)
        if used < 50 and not warn:
            break
    LR_TRACE_OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(trace_rows).to_csv(LR_TRACE_OUT, index=False, encoding="utf-8-sig")

    # Baseline LR C=1 uses the final warm-started checkpoint from above.
    lr_result = score("Logistic Regression", {"C": 1.0, "solver": "saga",
                         "tol": 1e-4, "max_iter": 5000,
                         "diagnostic_fit": "warm-start chunks of at most 50"}, lr,
                      xtr_lr, ytr, xv_lr, yv,
                      sum(r["chunk_fit_seconds"] for r in trace_rows),
                      bool(trace_rows[-1]["convergence_warning"]))
    # n_iter_ after the last warm-start fit is only the final chunk length;
    # report the cumulative iteration count from the trace instead.
    lr_result["n_iter"] = cumulative
    rows.append(lr_result)
    # C is not explicitly set in compare_models.py; it remains the sklearn
    # default 1.0 and is documented as such rather than represented as tuned.

    # RF one-factor-at-a-time candidates around the current baseline.
    rf_configs = []
    for n in (100, 200, 300):
        rf_configs.append({"n_estimators": n, "max_depth": 30,
                           "class_weight": "balanced"})
    for depth in (20, 30, 40):
        rf_configs.append({"n_estimators": 200, "max_depth": depth,
                           "class_weight": "balanced"})
    for weight in (None, "balanced"):
        rf_configs.append({"n_estimators": 200, "max_depth": 30,
                           "class_weight": weight})
    seen = set()
    for params in rf_configs:
        key = tuple(sorted(params.items()))
        if key in seen: continue
        seen.add(key)
        model = RandomForestClassifier(**params, random_state=SEED, n_jobs=-1)
        start = time.time(); model.fit(xtr, ytr); elapsed = time.time()-start
        rows.append(score("Random Forest", params, model, xtr, ytr, xv, yv, elapsed))
        print(f"RF {params}: F1={rows[-1]['f1_phishing']:.4f}; "
              f"AUC={rows[-1]['roc_auc']:.4f}; seconds={elapsed:.1f}", flush=True)

    # MNB alpha candidates; alpha=1 is the current code value.
    for alpha in (0.01, 0.1, 0.5, 1.0, 2.0, 10.0):
        params = {"alpha": alpha}
        model = MultinomialNB(**params)
        start = time.time(); model.fit(xtr, ytr); elapsed = time.time()-start
        rows.append(score("Multinomial Naive Bayes", params, model,
                          xtr, ytr, xv, yv, elapsed))
        print(f"MNB {params}: F1={rows[-1]['f1_phishing']:.4f}; "
              f"AUC={rows[-1]['roc_auc']:.4f}", flush=True)

    if XGBClassifier is not None:
        xgb_configs = []
        for n in (100, 200, 300):
            xgb_configs.append({"n_estimators": n, "max_depth": 6,
                                "learning_rate": 0.1, "subsample": 0.8,
                                "colsample_bytree": 0.8})
        for depth in (3, 6, 9):
            xgb_configs.append({"n_estimators": 200, "max_depth": depth,
                                "learning_rate": 0.1, "subsample": 0.8,
                                "colsample_bytree": 0.8})
        for rate in (0.05, 0.1, 0.2):
            xgb_configs.append({"n_estimators": 200, "max_depth": 6,
                                "learning_rate": rate, "subsample": 0.8,
                                "colsample_bytree": 0.8})
        for sub in (0.6, 0.8, 1.0):
            xgb_configs.append({"n_estimators": 200, "max_depth": 6,
                                "learning_rate": 0.1, "subsample": sub,
                                "colsample_bytree": 0.8})
        for col in (0.6, 0.8, 1.0):
            xgb_configs.append({"n_estimators": 200, "max_depth": 6,
                                "learning_rate": 0.1, "subsample": 0.8,
                                "colsample_bytree": col})
        seen = set()
        for params in xgb_configs:
            key = tuple(sorted(params.items()))
            if key in seen: continue
            seen.add(key)
            # XGBoost has much higher peak memory on sparse 30k-dimensional
            # input. Keep a fixed stratified 10k subset for every XGB candidate.
            xgb_train_idx, _ = train_test_split(
                np.arange(len(ytr)), train_size=XGB_TRAIN_SIZE,
                random_state=SEED + 2, stratify=ytr
            )
            xtr_xgb = xtr[xgb_train_idx]
            ytr_xgb = ytr[xgb_train_idx]
            model = XGBClassifier(**params, random_state=SEED, n_jobs=-1,
                                  eval_metric="logloss", verbosity=0)
            start = time.time(); model.fit(xtr_xgb, ytr_xgb); elapsed = time.time()-start
            rows.append(score("XGBoost", params, model, xtr_xgb, ytr_xgb,
                              xv, yv, elapsed))
            pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")
            print(f"XGB {params}: F1={rows[-1]['f1_phishing']:.4f}; "
                  f"AUC={rows[-1]['roc_auc']:.4f}; seconds={elapsed:.1f}", flush=True)
    else:
        print("XGBoost package not installed; skipped.", flush=True)

    result = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"Saved {OUT}", flush=True)
    print("Best validation result per model/parameter family (F1 primary; AUC tie-break):")
    for model_name, group in result.groupby("model"):
        print(model_name)
        print(group.sort_values(["f1_phishing", "roc_auc"], ascending=False)
              [["params", "f1_phishing", "roc_auc", "validation_logloss", "fit_seconds"]]
              .head(12).to_string(index=False, float_format=lambda x: f"{x:.4f}"))


if __name__ == "__main__":
    main()
