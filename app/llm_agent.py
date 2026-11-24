"""LLM Agent: goi Gemini de phan tich ngu canh email.

Runtime hien tai giu Gemini theo yeu cau vi API key cua ban da call duoc.
Script fine-tune OpenAI nam rieng trong scripts/fine_tune_llm.py.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM_PROMPT_PATH = PROJECT_ROOT / ".pi" / "prompts" / "system_prompt.md"


def read_system_prompt() -> str:
    """Doc prompt goc tu .pi; fallback neu file bi thieu."""
    if DEFAULT_SYSTEM_PROMPT_PATH.exists():
        return DEFAULT_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return "Ban la Phishing Analyst Agent. Hay phan tich email bang tieng Viet."


def format_email_context(email_data: Dict[str, Any], ml_result: Optional[Dict[str, Any]] = None) -> str:
    """Tao context co cau truc de dua vao LLM."""
    urls = email_data.get("urls") or []
    url_text = "\n".join(f"- {url}" for url in urls) if urls else "Khong phat hien URL."
    ml_text = "Chua co diem ML."
    if ml_result:
        score = max(0, min(int(float(ml_result.get("score", 0))), 100))
        verdict = "PHISHING" if score >= 60 else "NOT PHISHING"
        ml_text = (
            f"Diem rui ro tong hop: {score}%\n"
            f"Ket luan he thong co dinh (nguong 60%): {verdict}. Khong duoc tu y doi ket luan nay.\n"
            f"Nguon ML: {ml_result.get('source')}\n"
            f"Tin hieu ML: {ml_result.get('signals')}"
        )

    return f"""
Sender: {email_data.get("sender")}
Subject: {email_data.get("subject")}
Date: {email_data.get("date")}

URLs:
{url_text}

{ml_text}

Body:
{email_data.get("body")}
""".strip()


def call_gemini(
    api_key: str,
    model_name: str,
    system_instruction: str,
    user_input: str,
) -> str:
    """Goi Gemini Interactions API bang SDK google-genai hien tai."""
    from google import genai

    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=model_name,
        system_instruction=system_instruction,
        input=user_input,
        generation_config={"temperature": 0.2},
    )
    return interaction.output_text or "AI khong tra ve noi dung."


def _pin_report_verdict(text: str, score: int, verdict: str) -> str:
    """Keep the report's headline aligned with the system's threshold decision."""
    lines = [
        line for line in text.splitlines()
        if not re.match(
            r"^\s*(?:\d+[.)]\s*)?(?:kết luận|ket luan|điểm rủi ro|diem rui ro)\s*:",
            line,
            re.IGNORECASE,
        )
    ]
    details = "\n".join(lines).strip()
    headline = f"Kết luận hệ thống: {verdict} ({score}%)"
    return f"{headline}\n\n{details}" if details else headline


def analyze_email(
    email_data: Dict[str, Any],
    ml_result: Dict[str, Any],
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.6-flash",
) -> str:
    """Tao bao cao dau tien cua tac nhan AI dua tren email va diem ML."""
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Vui long nhap GEMINI_API_KEY trong sidebar hoac file .env."

    system_prompt = read_system_prompt()
    context = format_email_context(email_data, ml_result)
    score = max(0, min(int(float(ml_result.get("score", 0))), 100))
    verdict = "PHISHING" if score >= 60 else "NOT PHISHING"
    user_input = f"""
Hay phan tich email sau theo vai tro Phishing Analyst Agent.
Ket hop diem rui ro voi bang chung trong noi dung email. Ket luan he thong da duoc chot la {verdict} voi diem {score}% theo nguong 60%; phai giu nguyen ket luan va diem nay. Chi giai thich bang chung, do tin cay va hanh dong; khong tu tao ket luan/diem khac.

Bat dau bang dong: "Ket luan he thong: {verdict} ({score}%)". Sau do neu bang chung chinh, gioi han cua ket qua va hanh dong khuyen nghi cho SecOps/nguoi dung. Neu bang chung noi dung co ve mau thuan voi ket luan, hay mo ta su mau thuan nhu mot han che can xac minh, khong tu doi nhan.

{context}
""".strip()
    response = call_gemini(api_key, model_name, system_prompt, user_input)
    return _pin_report_verdict(response, score, verdict)


def chat_about_email(
    email_data: Dict[str, Any],
    ml_result: Dict[str, Any],
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.6-flash",
) -> str:
    """Tra loi chat tiep theo, giu boi canh email va lich su hoi dap."""
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Vui long nhap GEMINI_API_KEY trong sidebar hoac file .env."

    system_prompt = read_system_prompt()
    context = format_email_context(email_data, ml_result)
    history = []
    for message in messages:
        role = "Nguoi dung" if message["role"] == "user" else "Phishing Analyst Agent"
        history.append(f"{role}: {message['content']}")

    user_input = f"""
Email context:
{context}

Lich su trao doi:
{chr(10).join(history)}

Hay tra loi cau hoi moi nhat mot cach ngan gon, thuc chien va bang tieng Viet.
""".strip()
    return call_gemini(api_key, model_name, system_prompt, user_input)
