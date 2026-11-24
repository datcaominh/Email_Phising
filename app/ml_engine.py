"""ML Engine: tai model Random Forest va du doan rui ro phishing.

Module nay co 2 che do:
1. Neu ton tai file app/models/phishing_rf.pkl, he thong se dung model da train.
2. Neu chua train model, he thong dung heuristic fallback de MVP van chay duoc.
"""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List
from email.utils import parseaddr

import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "app" / "models" / "phishing_rf.pkl"
MODEL_DIR = PROJECT_ROOT / "app" / "models"
ACTIVE_MODEL_PATH = PROJECT_ROOT / "config" / "active_model.json"
TRUSTED_SENDERS_PATH = PROJECT_ROOT / "config" / "trusted_senders.json"
TRUSTED_SENDER_SCORE = 5.0
MODEL_FILES = {
    "rf": MODEL_DIR / "phishing_rf.pkl",
    "lr": MODEL_DIR / "phishing_lr.pkl",
    "mnb": MODEL_DIR / "phishing_mnb.pkl",
    "xgb": MODEL_DIR / "phishing_xgb.pkl",
}
MODEL_LABELS = {
    "rf": "Random Forest",
    "lr": "Logistic Regression",
    "mnb": "Multinomial Naive Bayes",
    "xgb": "XGBoost",
}


def get_available_models() -> list[str]:
    return [key for key, path in MODEL_FILES.items() if path.exists()]


def get_active_model_key() -> str:
    try:
        import json
        key = json.loads(ACTIVE_MODEL_PATH.read_text(encoding="utf-8")).get("model", "rf")
        return key if key in MODEL_FILES else "rf"
    except (OSError, ValueError, AttributeError):
        return "rf"


def set_active_model_key(key: str) -> None:
    import json
    if key not in MODEL_FILES:
        raise ValueError(f"Unknown model key: {key}")
    ACTIVE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_MODEL_PATH.write_text(json.dumps({"model": key}, indent=2), encoding="utf-8")


def _trusted_sender_addresses() -> set[str]:
    try:
        data = json.loads(TRUSTED_SENDERS_PATH.read_text(encoding="utf-8"))
        return {str(address).strip().casefold() for address in data.get("senders", []) if str(address).strip()}
    except (OSError, ValueError, AttributeError, TypeError):
        return set()


def _apply_trusted_sender_policy(result: Dict[str, Any], email_data: Dict[str, Any]) -> Dict[str, Any]:
    sender_address = parseaddr(str(email_data.get("sender", "")))[1].strip().casefold()
    if not sender_address or sender_address not in _trusted_sender_addresses():
        return result

    adjusted = dict(result)
    signals = dict(result.get("signals") or {})
    signals["trusted_sender_override"] = {
        "matched_sender": sender_address,
        "original_score": result.get("score"),
        "policy_score": TRUSTED_SENDER_SCORE,
    }
    adjusted.update(
        score=TRUSTED_SENDER_SCORE,
        label=0,
        source=f"{result.get('source', 'model')}+trusted_sender_allowlist",
        signals=signals,
    )
    return adjusted


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
    receiver = email_data.get("receiver", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")
    urls = " ".join(email_data.get("urls") or [])
    return f"Sender: {sender}\nReceiver: {receiver}\nSubject: {subject}\nURLs: {urls}\nBody:\n{body}".strip()


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


def predict_phishing(email_data: Dict[str, Any], model_path: Path | None = None) -> Dict[str, Any]:
    """Predict with the selected saved model and apply the shared heuristic guardrail."""
    text = build_text_features(email_data)
    if model_path is None:
        selected_key = get_active_model_key()
        model_path = MODEL_FILES[selected_key]
    else:
        selected_key = next((key for key, path in MODEL_FILES.items() if path == model_path), "rf")
    model = load_model(model_path)

    if model is None:
        result = heuristic_score(text, email_data.get("urls") or [])
        return _apply_trusted_sender_policy(result, email_data)

    if isinstance(model, dict) and {"features", "classifier"}.issubset(model):
        X = model["features"].transform([text])
        if model.get("scaler") is not None:
            X = model["scaler"].transform(X)
        classifier = model["classifier"]
        probabilities = classifier.predict_proba(X)[0]
    else:
        # Backward compatibility for the original saved sklearn Pipeline.
        classifier = model
        probabilities = classifier.predict_proba([text])[0]
    phishing_class_index = list(classifier.classes_).index(1)
    model_probability = float(probabilities[phishing_class_index] * 100)
    heuristic_result = heuristic_score(text, email_data.get("urls") or [])
    heuristic_probability = float(heuristic_result["score"])

    # Guardrail hybrid: neu model hoc theo dataset cu nhung email co dau hieu
    # credential/urgency/URL ro rang, heuristic duoc phep nang diem rui ro.
    final_probability = max(model_probability, heuristic_probability)

    result = {
        "score": round(final_probability, 2),
        "label": int(final_probability >= 60),
        "source": f"{MODEL_LABELS.get(selected_key, selected_key)}+heuristic_guardrails",
        "signals": {
            "model_path": str(model_path),
            "model": selected_key,
            "classes": [int(cls) for cls in classifier.classes_],
            "model_score": round(model_probability, 2),
            "heuristic_score": round(heuristic_probability, 2),
            "heuristic_signals": heuristic_result.get("signals", {}),
        },
    }
    return _apply_trusted_sender_policy(result, email_data)
