"""ML Engine: tai model Random Forest va du doan rui ro phishing.

Module nay co 2 che do:
1. Neu ton tai file app/models/phishing_rf.pkl, he thong se dung model da train.
2. Neu chua train model, he thong dung heuristic fallback de MVP van chay duoc.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "app" / "models" / "phishing_rf.pkl"


SUSPICIOUS_KEYWORDS = [
    "urgent",
    "verify",
    "password",
    "login",
    "suspended",
    "bank",
    "invoice",
    "payment",
    "wire transfer",
    "gift card",
    "reset",
    "security alert",
    "khẩn cấp",
    "xac minh",
    "xác minh",
    "mat khau",
    "mật khẩu",
    "dang nhap",
    "đăng nhập",
    "thanh toán",
    "tai khoan",
    "tài khoản",
]


def build_text_features(email_data: Dict[str, Any]) -> str:
    """Gop cac truong quan trong thanh mot chuoi dau vao cho TF-IDF."""
    sender = email_data.get("sender", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")
    urls = " ".join(email_data.get("urls") or [])
    return f"Sender: {sender}\nSubject: {subject}\nURLs: {urls}\nBody:\n{body}".strip()


def load_model(model_path: Path = DEFAULT_MODEL_PATH):
    """Tai pipeline da train; tra ve None neu chua co file model."""
    if not model_path.exists():
        return None
    return joblib.load(model_path)


def heuristic_score(text: str, urls: Iterable[str]) -> Dict[str, Any]:
    """Tinh diem fallback khi chua co model ML.

    Day khong phai model thay the training, chi giup giao dien demo duoc ngay.
    """
    lower_text = text.lower()
    matched_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lower_text]
    url_list = list(urls or [])
    suspicious_url_count = sum(
        1
        for url in url_list
        if re.search(r"(@|bit\.ly|tinyurl|login|verify|secure|account|\.ru|\.zip)", url, re.I)
    )

    score = 8
    score += min(len(matched_keywords) * 8, 48)
    score += min(len(url_list) * 8, 24)
    score += min(suspicious_url_count * 15, 30)
    score = max(0, min(score, 95))

    return {
        "score": float(score),
        "label": int(score >= 60),
        "source": "heuristic_fallback",
        "signals": {
            "matched_keywords": matched_keywords[:10],
            "url_count": len(url_list),
            "suspicious_url_count": suspicious_url_count,
        },
    }


def predict_phishing(email_data: Dict[str, Any], model_path: Path = DEFAULT_MODEL_PATH) -> Dict[str, Any]:
    """Du doan xac suat phishing bang Random Forest hoac heuristic fallback."""
    text = build_text_features(email_data)
    model = load_model(model_path)

    if model is None:
        return heuristic_score(text, email_data.get("urls") or [])

    probabilities = model.predict_proba([text])[0]
    phishing_class_index = list(model.classes_).index(1)
    model_probability = float(probabilities[phishing_class_index] * 100)
    heuristic_result = heuristic_score(text, email_data.get("urls") or [])
    heuristic_probability = float(heuristic_result["score"])

    # Guardrail hybrid: neu model hoc theo dataset cu nhung email co dau hieu
    # credential/urgency/URL ro rang, heuristic duoc phep nang diem rui ro.
    final_probability = max(model_probability, heuristic_probability)

    return {
        "score": round(final_probability, 2),
        "label": int(final_probability >= 60),
        "source": "random_forest_tfidf+heuristic_guardrails",
        "signals": {
            "model_path": str(model_path),
            "classes": [int(cls) for cls in model.classes_],
            "model_score": round(model_probability, 2),
            "heuristic_score": round(heuristic_probability, 2),
            "heuristic_signals": heuristic_result.get("signals", {}),
        },
    }
