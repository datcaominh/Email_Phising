"""Feature engineering cho email phishing.

Transformer nay duoc dung ca luc train va luc inference, nen dat trong package app
de joblib co the unpickle model on dinh.
"""

from __future__ import annotations

import re
from typing import Iterable, List

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


URGENCY_TERMS = [
    "urgent",
    "immediately",
    "within 24 hours",
    "suspended",
    "limited time",
    "act now",
    "khẩn cấp",
    "ngay lập tức",
]

CREDENTIAL_TERMS = [
    "password",
    "login",
    "sign in",
    "verify",
    "account",
    "credential",
    "mật khẩu",
    "đăng nhập",
    "xác minh",
    "tài khoản",
]

MONEY_TERMS = [
    "payment",
    "invoice",
    "wire transfer",
    "bank",
    "refund",
    "gift card",
    "thanh toán",
    "chuyển khoản",
    "ngân hàng",
]

SUSPICIOUS_URL_TERMS = [
    "login",
    "verify",
    "secure",
    "account",
    "password",
    "bit.ly",
    "tinyurl",
    ".ru",
    ".zip",
]


def count_terms(text: str, terms: Iterable[str]) -> int:
    """Dem so term xuat hien trong text, khong phan biet hoa thuong."""
    lower_text = text.lower()
    return sum(1 for term in terms if term in lower_text)


class SecurityFeatureExtractor(BaseEstimator, TransformerMixin):
    """Tao dac trung so hoc bo sung cho TF-IDF.

    Dau vao la list chuoi text da gop metadata + body.
    Dau ra la ma tran numpy shape (n_samples, n_features).
    """

    def fit(self, x, y=None):
        return self

    def transform(self, x: List[str]):
        rows = []
        for value in x:
            text = str(value)
            lower_text = text.lower()
            urls = re.findall(r"https?://[^\s<>\]\)\"']+|www\.[^\s<>\]\)\"']+", text, flags=re.I)
            suspicious_urls = [
                url for url in urls if any(term in url.lower() for term in SUSPICIOUS_URL_TERMS)
            ]
            rows.append(
                [
                    len(text),
                    len(urls),
                    len(suspicious_urls),
                    count_terms(lower_text, URGENCY_TERMS),
                    count_terms(lower_text, CREDENTIAL_TERMS),
                    count_terms(lower_text, MONEY_TERMS),
                    int("@" in " ".join(urls)),
                    int(bool(re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text))),
                    int(bool(re.search(r"https?://[^/\s]*-[^/\s]*", text, flags=re.I))),
                ]
            )
        return np.asarray(rows, dtype=float)
