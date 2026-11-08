"""Orchestrator: dieu phoi multi-agent pipeline tu .pi den UI.

Pipeline:
1. Parse email tu file .eml/.txt.
2. Goi ML Skill de tinh % phishing.
3. Goi LLM Agent de phan tich ngu canh.
4. Chuan hoa canh bao theo .pi/data/sample_alert.json.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.llm_agent import analyze_email, chat_about_email
from app.ml_engine import predict_phishing


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PI_ROOT = PROJECT_ROOT / ".pi"
SAMPLE_ALERT_PATH = PI_ROOT / "data" / "sample_alert.json"
LOG_DIR = PROJECT_ROOT / "logs"
PIPELINE_LOG_PATH = LOG_DIR / "pipeline.log"


def make_log(step: str, status: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Tao mot log event co timestamp de UI hien thi theo tung buoc .pi."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "status": status,
        "message": message,
        "details": details or {},
    }


def append_log(logs: List[Dict[str, Any]], step: str, status: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Them log vao memory va ghi ra logs/pipeline.log dang JSONL."""
    event = make_log(step, status, message, details)
    logs.append(event)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with PIPELINE_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_pi_markdown(relative_path: str) -> str:
    """Doc file markdown trong .pi de UI/orchestrator co the hien thi cau hinh."""
    path = PI_ROOT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_text_body(message) -> str:
    """Lay text/plain; neu email chi co HTML thi bo tag HTML co ban."""
    text_parts: List[str] = []
    html_parts: List[str] = []

    if message.is_multipart():
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                continue

            try:
                content = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                content = payload.decode(charset, errors="replace")

            if part.get_content_type() == "text/plain":
                text_parts.append(str(content))
            elif part.get_content_type() == "text/html":
                html_parts.append(str(content))
    else:
        try:
            content = message.get_content()
        except Exception:
            payload = message.get_payload(decode=True) or b""
            charset = message.get_content_charset() or "utf-8"
            content = payload.decode(charset, errors="replace")

        if message.get_content_type() == "text/html":
            html_parts.append(str(content))
        else:
            text_parts.append(str(content))

    if text_parts:
        return "\n\n".join(part.strip() for part in text_parts if part.strip())

    html_text = "\n\n".join(html_parts)
    html_text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html_text)
    html_text = re.sub(r"(?s)<[^>]+>", " ", html_text)
    return re.sub(r"\s+", " ", html_text).strip()


def extract_urls(text: str) -> List[str]:
    """Trich xuat URL duy nhat tu noi dung email."""
    pattern = r"https?://[^\s<>\]\)\"']+|www\.[^\s<>\]\)\"']+"
    urls = re.findall(pattern, text or "", flags=re.IGNORECASE)
    cleaned_urls: List[str] = []
    for url in urls:
        cleaned = url.rstrip(".,;:!?)]}'\"")
        if cleaned not in cleaned_urls:
            cleaned_urls.append(cleaned)
    return cleaned_urls


def parse_uploaded_email(uploaded_file) -> Dict[str, Any]:
    """Parse file upload tu Streamlit thanh dict chuan cho pipeline."""
    raw_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        body = raw_bytes.decode("utf-8", errors="replace")
        return {
            "filename": uploaded_file.name,
            "sender": "Khong co header",
            "receiver": "Khong co header",
            "subject": uploaded_file.name,
            "date": "Khong co header",
            "body": body.strip(),
            "urls": extract_urls(body),
        }

    message = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    body = extract_text_body(message)
    return {
        "filename": uploaded_file.name,
        "sender": message.get("From", "Khong ro"),
        "receiver": message.get("To", "Khong ro"),
        "subject": message.get("Subject", "Khong co tieu de"),
        "date": message.get("Date", "Khong ro"),
        "body": body,
        "urls": extract_urls(body),
    }


def risk_level(score: float) -> str:
    """Thong nhat dau ra nhi phan: Phishing (1) hoac Not Phishing (0).

    Nguong: score >= 60 => Phishing, score < 60 => Not Phishing.
    """
    return "Phishing" if score >= 60 else "Not Phishing"


def load_alert_template() -> Dict[str, Any]:
    """Doc sample alert JSON; fallback neu file template bi thieu."""
    if SAMPLE_ALERT_PATH.exists():
        return json.loads(SAMPLE_ALERT_PATH.read_text(encoding="utf-8"))
    return {
        "alert_id": "",
        "risk_score": 0,
        "risk_level": "",
        "email": {},
        "ml": {},
        "llm_analysis": "",
        "recommended_actions": [],
    }


def build_alert(email_data: Dict[str, Any], ml_result: Dict[str, Any], llm_analysis: str) -> Dict[str, Any]:
    """Dinh dang ket qua theo sample_alert.json."""
    score = float(ml_result.get("score", 0))
    alert = deepcopy(load_alert_template())
    alert.update(
        {
            "alert_id": f"PHISH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "risk_score": score,
            "risk_level": risk_level(score),
            "email": {
                "filename": email_data.get("filename"),
                "sender": email_data.get("sender"),
                "receiver": email_data.get("receiver"),
                "subject": email_data.get("subject"),
                "date": email_data.get("date"),
                "urls": email_data.get("urls") or [],
            },
            "ml": ml_result,
            "llm_analysis": llm_analysis,
            "recommended_actions": [
                "Khong bam link hoac mo file dinh kem khi chua xac minh.",
                "Kiem tra domain nguoi gui va header email neu can dieu tra sau.",
                "Bao cao email cho bo phan SecOps/IT neu diem rui ro cao.",
            ],
        }
    )
    return alert


def run_pipeline(uploaded_file, api_key: Optional[str], model_name: str) -> Dict[str, Any]:
    """Chay toan bo pipeline Parse -> ML -> LLM -> Alert."""
    logs: List[Dict[str, Any]] = []

    append_log(
        logs,
        ".pi/chains/parse",
        "running",
        "Bat dau parse email upload.",
        {"filename": getattr(uploaded_file, "name", "unknown")},
    )
    email_data = parse_uploaded_email(uploaded_file)
    append_log(
        logs,
        ".pi/chains/parse",
        "success",
        "Parse email thanh cong.",
        {
            "sender": email_data.get("sender"),
            "subject": email_data.get("subject"),
            "url_count": len(email_data.get("urls") or []),
            "body_chars": len(email_data.get("body") or ""),
        },
    )

    append_log(logs, ".pi/skills/ml", "running", "Goi ML Skill Random Forest/heuristic.")
    ml_result = predict_phishing(email_data)
    append_log(
        logs,
        ".pi/skills/ml",
        "success",
        "ML Skill tra ve diem rui ro.",
        {
            "score": ml_result.get("score"),
            "label": ml_result.get("label"),
            "source": ml_result.get("source"),
        },
    )

    append_log(
        logs,
        ".pi/agents/llm",
        "running",
        "Goi Phishing Analyst Agent bang Gemini.",
        {"model": model_name},
    )
    llm_analysis = analyze_email(email_data, ml_result, api_key=api_key, model_name=model_name)
    llm_status = "warning" if llm_analysis.startswith("Vui long") or llm_analysis.startswith("Khong the") else "success"
    append_log(
        logs,
        ".pi/agents/llm",
        llm_status,
        "LLM Agent da tra ve bao cao.",
        {"analysis_chars": len(llm_analysis)},
    )

    append_log(logs, ".pi/data/alert", "running", "Chuan hoa ket qua theo sample_alert.json.")
    alert = build_alert(email_data, ml_result, llm_analysis)
    append_log(
        logs,
        ".pi/data/alert",
        "success",
        "Alert JSON da duoc tao.",
        {
            "alert_id": alert.get("alert_id"),
            "risk_level": alert.get("risk_level"),
            "risk_score": alert.get("risk_score"),
        },
    )
    return {
        "email_data": email_data,
        "ml_result": ml_result,
        "llm_analysis": llm_analysis,
        "alert": alert,
        "pipeline_logs": logs,
        "log_file": str(PIPELINE_LOG_PATH),
    }


def continue_chat(
    email_data: Dict[str, Any],
    ml_result: Dict[str, Any],
    messages: List[Dict[str, str]],
    api_key: Optional[str],
    model_name: str,
) -> str:
    """Ham bao boc de UI chat voi LLM Agent."""
    return chat_about_email(email_data, ml_result, messages, api_key=api_key, model_name=model_name)
