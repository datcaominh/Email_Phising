"""Test dau ra nhi phan: Phishing / Not Phishing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.orchestrator import risk_level
from app.ml_engine import predict_phishing

print("=== TEST RISK LEVEL (NHI PHAN) ===")
for s in [0, 30, 49, 55, 59, 60, 65, 85, 100]:
    print(f"  Score {s:>3} -> {risk_level(s)}")

print()
print("=== TEST ML ENGINE ===")
email_safe = {
    "sender": "friend@gmail.com",
    "subject": "hello",
    "body": "How are you? Lets meet tomorrow.",
    "urls": [],
}
email_phish = {
    "sender": "bank@evil.com",
    "subject": "URGENT: verify your password now!",
    "body": "Click here to login and verify your password immediately. Your account will be suspended.",
    "urls": ["http://bit.ly/xyz"],
}

r1 = predict_phishing(email_safe)
r2 = predict_phishing(email_phish)

c1 = "Phishing" if r1["label"] else "Not Phishing"
c2 = "Phishing" if r2["label"] else "Not Phishing"

print(f"  Email an toan:   score={r1['score']}, label={r1['label']} -> {c1}")
print(f"  Email phishing:  score={r2['score']}, label={r2['label']} -> {c2}")

print()
print("=== TEST ALERT ===")
from app.orchestrator import build_alert

alert = build_alert(email_phish, r2, "Test analysis")
print(f"  risk_score: {alert['risk_score']}")
print(f"  risk_level: {alert['risk_level']}")

print()
if risk_level(60) == "Phishing" and risk_level(59) == "Not Phishing":
    print("PASS: Dau ra nhi phan hoat dung!")
else:
    print("FAIL: Dau ra chua dung!")
