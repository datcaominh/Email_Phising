"""LLM Agent: goi Gemini de phan tich ngu canh email.

Runtime hien tai giu Gemini theo yeu cau vi API key cua ban da call duoc.
Script fine-tune OpenAI nam rieng trong scripts/fine_tune_llm.py.
"""

from __future__ import annotations

import os
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
        ml_text = (
            f"Diem ML: {ml_result.get('score')}%\n"
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
    user_input = f"""
Hay phan tich email sau theo vai tro Phishing Analyst Agent.
Ket hop diem ML voi bang chung trong noi dung email.

Yeu cau dau ra (THONG NHAT NHI PHAN):
1. Ket luan: PHISHING hoac NOT PHISHING (chi chon 1)
2. Diem rui ro: 0-100
3. Bang chung chinh
4. Hanh dong khuyen nghi cho SecOps va nguoi dung

{context}
""".strip()
    return call_gemini(api_key, model_name, system_prompt, user_input)


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
