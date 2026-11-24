"""Streamlit UI cho he thong Hybrid Phishing Analysis + Auto Monitor Dashboard.

Cach chay:
    streamlit run app/main.py
"""

from __future__ import annotations

import json
from html import escape
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
MONITOR_LOG = LOG_DIR / "monitor_history.jsonl"
SEEN_IDS_FILE = LOG_DIR / "seen_email_ids.txt"
RESULTS_DIR = PROJECT_ROOT / "results"
ENV_FILE = PROJECT_ROOT / ".env"

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.orchestrator import continue_chat, read_pi_markdown, run_pipeline
from app.email_fetcher import fetch_and_analyze
from app.ml_engine import get_active_model_key, get_available_models, MODEL_LABELS, set_active_model_key

st.set_page_config(
    page_title="Hybrid Phishing Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        :root {
            --canvas: #f3f6f9;
            --surface: #ffffff;
            --line: #e4eaf0;
            --ink: #172536;
            --muted: #69788a;
            --accent: #2f7180;
            --nav: #172637;
            --nav-muted: #aab8c8;
        }
        [data-testid="stAppViewContainer"] { background: var(--canvas); }
        [data-testid="stAppViewContainer"], [data-testid="stSidebar"] { font-family: Inter, "Segoe UI", sans-serif; }
        [data-testid="stHeader"] { background: transparent; }
        .main .block-container { max-width: 1540px; padding: 1.45rem 2.35rem 3.2rem; }
        [data-testid="stSidebar"] { background: var(--nav); border-right: 1px solid #26394b; }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: #e8eef5; }
        [data-testid="stSidebar"] hr { border-color: #344659; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: var(--nav-muted); }
        [data-testid="stSidebar"] [data-testid="stAlert"] { background: #22364a; border: 1px solid #344a60; }
        [data-testid="stSidebar"] [data-testid="stAlert"] p { color: #d7e2ed; }
        .brand-lockup { display: flex; align-items: center; gap: 0.7rem; padding: 0.65rem 0 0.7rem; }
        .brand-mark { display: grid; place-items: center; width: 2.45rem; height: 2.45rem; flex: 0 0 auto; border: 1px solid rgba(157, 209, 213, 0.45); border-radius: 10px; color: #e5f5f5; background: linear-gradient(145deg, #367e8a, #245465); font-size: 0.77rem; font-weight: 800; letter-spacing: 0.04em; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18); }
        .sidebar-brand { font-size: 0.95rem; font-weight: 760; letter-spacing: 0.025em; color: #f5f8fb; line-height: 1.25; }
        .sidebar-caption { color: var(--nav-muted); font-size: 0.7rem; margin-top: 0.2rem; }
        .brand-status { display: flex; align-items: center; gap: 0.4rem; padding: 0.45rem 0.55rem; margin: 0 0 0.85rem; border: 1px solid #304559; border-radius: 7px; background: rgba(255, 255, 255, 0.035); color: #aebfcd; font-size: 0.61rem; font-weight: 700; letter-spacing: 0.1em; }
        .brand-status-dot { width: 6px; height: 6px; border-radius: 50%; background: #59c29b; box-shadow: 0 0 8px rgba(89, 194, 155, 0.55); }
        .sidebar-section { color: #8fa3b8; font-size: 0.67rem; font-weight: 700; letter-spacing: 0.14em; margin: 1rem 0 0.45rem; text-transform: uppercase; }
        .page-heading { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 0.1rem 0 0.4rem; }
        .eyebrow { color: var(--accent); font-size: 0.7rem; font-weight: 750; letter-spacing: 0.15em; margin-bottom: 0.45rem; }
        .app-title { color: var(--ink); font-size: 1.95rem; font-weight: 760; letter-spacing: -0.04em; line-height: 1.16; margin-bottom: 0.38rem; }
        .app-subtitle { color: var(--muted); font-size: 0.92rem; margin-bottom: 0.35rem; }
        .live-pill { display: inline-flex; align-items: center; gap: 0.45rem; white-space: nowrap; color: #506173; background: #fff; border: 1px solid var(--line); border-radius: 999px; padding: 0.48rem 0.72rem; font-size: 0.76rem; font-weight: 650; }
        .live-dot { color: #8996a5; font-size: 0.8rem; }
        .live-dot.is-active { color: #2d9a75; }
        .section-kicker { color: #7a8999; font-size: 0.69rem; font-weight: 700; letter-spacing: 0.13em; text-transform: uppercase; margin: 0.15rem 0 0.45rem; }
        [data-testid="stTabs"] { margin-top: 0.7rem; }
        [data-testid="stTabs"] [role="tablist"] { gap: 0.45rem; border-bottom: 1px solid var(--line); }
        button[data-baseweb="tab"] { color: var(--muted); font-weight: 650; padding: 0.72rem 1rem; }
        button[data-baseweb="tab"][aria-selected="true"] { color: var(--accent); }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--accent); }
        div[data-testid="stMetric"] {
            background: var(--surface); border: 1px solid var(--line);
            border-radius: 11px; padding: 0.78rem 0.95rem; box-shadow: 0 2px 7px rgba(23, 37, 54, 0.035);
        }
        [data-testid="stMetricLabel"] { color: var(--muted); font-size: 0.76rem; font-weight: 600; }
        [data-testid="stMetricValue"] { color: var(--ink); font-size: 1.45rem; font-weight: 730; }
        .signal-box {
            border: 1px solid var(--line); border-radius: 9px;
            padding: 0.75rem 0.85rem; background: var(--surface);
            margin-bottom: 0.5rem; word-break: break-word;
        }
        .email-meta-card { min-height: 82px; padding: 0.72rem 0.8rem; border: 1px solid var(--line); border-radius: 10px; background: #fff; box-shadow: 0 2px 7px rgba(23, 37, 54, 0.035); }
        .email-meta-label { color: #7b8998; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.38rem; }
        .email-meta-value { color: #26384b; font-size: 0.86rem; font-weight: 560; line-height: 1.45; overflow-wrap: anywhere; }
        .email-subject-card { padding: 0.8rem 0.9rem; border: 1px solid #dfe7ed; border-left: 3px solid var(--accent); border-radius: 9px; background: #fff; color: #34465a; font-size: 0.9rem; line-height: 1.5; overflow-wrap: anywhere; }
        .email-subject-label { display: block; color: #7b8998; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.3rem; }
        .email-url-card { display: grid; grid-template-columns: 2.7rem minmax(0, 1fr); gap: 0.65rem; align-items: start; padding: 0.65rem 0.75rem; margin: 0.35rem 0; border: 1px solid #eadfca; border-radius: 8px; background: #fffaf1; }
        .email-url-index { color: #99743a; font-size: 0.68rem; font-weight: 700; }
        .email-url-value { color: #34465a; font-family: ui-monospace, Consolas, monospace; font-size: 0.76rem; line-height: 1.5; overflow-wrap: anywhere; word-break: break-word; }
        [data-testid="stExpander"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
        [data-testid="stChatMessage"] { display: flex; gap: 0.55rem; padding: 0.85rem 0.9rem; background: var(--surface); border: 1px solid var(--line); border-radius: 11px; }
        [data-testid="stChatMessage"] > div:first-child { flex: 0 0 1.65rem; width: 1.65rem; }
        [data-testid="stChatMessage"] > div:last-child { flex: 1 1 auto; min-width: 0; width: 100%; }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { max-width: none; overflow-wrap: anywhere; }
        [data-testid="stFileUploader"] section { background: var(--surface); border: 1px dashed #bdcbd7; border-radius: 11px; }
        [data-testid="stAlert"] { border-radius: 9px; }
        div.stButton > button { border-radius: 8px; font-weight: 620; min-height: 2.4rem; transition: all 140ms ease; }
        div.stButton > button[kind="primary"] { background: var(--accent); border-color: var(--accent); }
        div.stButton > button[kind="primary"]:hover { background: #285e6b; border-color: #285e6b; }
        [data-testid="stSidebar"] div.stButton > button { justify-content: flex-start; text-align: left; border: 1px solid transparent; color: #bfccda; background: transparent; }
        [data-testid="stSidebar"] div.stButton > button:hover { background: #24384c; color: #fff; border-color: #344a60; }
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] { color: #fff; background: #2f7180; border-color: #2f7180; }
        [data-testid="stSidebar"] div.stButton { margin-bottom: -0.4rem; }
        [data-testid="stSidebar"] div.stButton > button { min-height: 2.25rem; padding: 0.2rem 0.75rem; font-size: 0.86rem; }
        [data-testid="stSidebar"] div.stButton > button div { justify-content: flex-start !important; width: 100%; }
        [data-testid="stSidebar"] div.stButton > button p { text-align: left; width: 100%; }
        [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
        [data-testid="stMetric"] { transition: transform 150ms ease, box-shadow 150ms ease; }
        [data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 7px 18px rgba(23, 37, 54, 0.08); }
        .dashboard-hero { position: relative; isolation: isolate; overflow: hidden; margin: 0.3rem 0 1.35rem; padding: 1.75rem 1.9rem; border: 1px solid #2c465c; border-radius: 16px; color: #f6f9fc; background: linear-gradient(112deg, #172738 0%, #203b50 62%, #2d6875 125%); box-shadow: 0 12px 28px rgba(23, 37, 54, 0.13); }
        .dashboard-hero:before { content: ""; position: absolute; z-index: -1; width: 300px; height: 300px; top: -165px; right: 8%; border: 1px solid rgba(219, 239, 241, 0.15); border-radius: 50%; box-shadow: 0 0 0 32px rgba(219, 239, 241, 0.035), 0 0 0 66px rgba(219, 239, 241, 0.025); }
        .dashboard-hero:after { content: ""; position: absolute; z-index: -1; width: 150px; height: 150px; right: 21%; bottom: -115px; border: 1px solid rgba(219, 239, 241, 0.18); border-radius: 50%; }
        .hero-layout { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; }
        .hero-copy { max-width: 680px; }
        .hero-eyebrow { color: #9cc8ce; font-size: 0.68rem; font-weight: 750; letter-spacing: 0.17em; margin-bottom: 0.6rem; }
        .hero-title { color: #fff; font-size: 1.8rem; line-height: 1.18; font-weight: 760; letter-spacing: -0.035em; margin-bottom: 0.55rem; }
        .hero-description { color: #c7d4df; font-size: 0.9rem; line-height: 1.6; max-width: 610px; }
        .hero-chips { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 1rem; }
        .hero-chip { color: #e4eef4; border: 1px solid rgba(223, 239, 243, 0.22); background: rgba(255, 255, 255, 0.07); border-radius: 999px; padding: 0.3rem 0.6rem; font-size: 0.67rem; font-weight: 650; letter-spacing: 0.03em; }
        .hero-flow { flex: 0 0 auto; display: flex; align-items: center; gap: 0.45rem; padding: 0.85rem; border: 1px solid rgba(226, 241, 245, 0.18); border-radius: 12px; background: rgba(11, 25, 38, 0.2); }
        .flow-node { min-width: 54px; padding: 0.55rem 0.45rem; text-align: center; color: #eaf4f5; border: 1px solid rgba(226, 241, 245, 0.2); border-radius: 8px; background: rgba(255, 255, 255, 0.06); font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em; }
        .flow-link { width: 17px; height: 1px; background: #78aeb5; position: relative; }
        .flow-link:after { content: ""; position: absolute; right: 0; top: -3px; width: 6px; height: 6px; border-top: 1px solid #9dd1d5; border-right: 1px solid #9dd1d5; transform: rotate(45deg); }
        .section-kicker { display: flex; align-items: center; gap: 0.65rem; color: #748496; font-size: 0.68rem; font-weight: 750; letter-spacing: 0.14em; text-transform: uppercase; margin: 1rem 0 0.7rem; }
        .section-kicker:after { content: ""; height: 1px; flex: 1; background: linear-gradient(90deg, #d6dfe7, transparent); }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--line); border-radius: 12px; background: #fff; box-shadow: 0 3px 11px rgba(23, 37, 54, 0.035); }
        .rf-matrix { width: 100%; border-collapse: separate; border-spacing: 0.4rem; margin: 0.1rem 0 0.65rem; text-align: center; }
        .rf-matrix th { color: #718196; padding: 0.35rem; font-size: 0.68rem; font-weight: 700; }
        .rf-matrix td { width: 33%; height: 82px; border: 1px solid #e3eaf0; border-radius: 10px; color: #243448; background: #f7f9fb; }
        .rf-matrix td.good { background: #eaf5f1; border-color: #d4e9e0; }
        .rf-matrix td.miss { background: #fff2ef; border-color: #f4ddd7; }
        .matrix-value { display: block; color: #1f3445; font-size: 1.35rem; font-weight: 750; }
        .matrix-label { display: block; margin-top: 0.2rem; color: #718196; font-size: 0.67rem; }
        .risk-summary { margin: 0.3rem 0 0.8rem; padding: 0.95rem 1rem; border: 1px solid #c9dce1; border-radius: 12px; background: #eaf2f4; color: #1c3a46; }
        .risk-summary.is-phishing { border-color: #e6c9a4; background: #fff4e7; color: #68421c; }
        .risk-summary-title { font-size: 1rem; font-weight: 750; }
        .risk-summary-meta { margin-top: 0.2rem; color: #627585; font-size: 0.82rem; }
        .risk-track { height: 7px; margin-top: 0.7rem; overflow: hidden; border-radius: 8px; background: #dce5e9; }
        .risk-fill { height: 100%; border-radius: 8px; background: #438293; }
        .risk-summary.is-phishing .risk-fill { background: #bd8750; }
        @media (max-width: 800px) {
            .main .block-container { padding: 1rem 1rem 2rem; }
            .page-heading { align-items: flex-start; flex-direction: column; }
            .app-title { font-size: 1.6rem; }
            .dashboard-hero { padding: 1.35rem; }
            .hero-layout { align-items: flex-start; flex-direction: column; }
            .hero-flow { max-width: 100%; gap: 0.3rem; }
            .flow-node { min-width: 45px; font-size: 0.58rem; }
            .flow-link { width: 10px; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state() -> None:
    defaults: Dict[str, Any] = {
        "pipeline_result": None,
        "messages": [],
        "uploaded_filename": None,
        "monitor_running": False,
        "monitor_thread": None,
        "last_results": [],
        "total_checked": 0,
        "total_alerted": 0,
        "active_page": "Dashboard",
        "llm_provider_value": os.getenv("LLM_PROVIDER", "google_gemini"),
        "llm_model_value": os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.6-flash")),
        "llm_api_key_value": os.getenv("LLM_API_KEY", os.getenv("GEMINI_API_KEY", "")),
        "gmail_address_value": os.getenv("GMAIL_ADDRESS", ""),
        "gmail_app_password_value": os.getenv("GMAIL_APP_PASSWORD", ""),
        "telegram_bot_token_value": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id_value": os.getenv("TELEGRAM_CHAT_ID", ""),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_env_values(values: Dict[str, str]) -> None:
    """Persist configuration values in the ignored project .env and this process."""
    from dotenv import set_key

    for key, value in values.items():
        set_key(str(ENV_FILE), key, value, quote_mode="always")
        os.environ[key] = value


def show_risk(score: float) -> None:
    normalized = max(0, min(int(score), 100))
    verdict = "PHISHING" if normalized >= 60 else "NOT PHISHING"
    style = "is-phishing" if normalized >= 60 else ""
    st.markdown(
        f'<div class="risk-summary {style}"><div class="risk-summary-title">Kết luận hệ thống: {verdict}</div>'
        f'<div class="risk-summary-meta">Điểm rủi ro tổng hợp từ ML và heuristic · {normalized}%</div>'
        f'<div class="risk-track"><div class="risk-fill" style="width:{normalized}%"></div></div></div>',
        unsafe_allow_html=True,
    )


def render_pipeline_logs(result: Dict[str, Any]) -> None:
    logs = result.get("pipeline_logs") or []
    if not logs:
        st.info("Chua co log pipeline.")
        return
    st.caption(f"File log: {result.get('log_file')}")
    for event in logs:
        label = f"{event.get('step')} - {event.get('message')}"
        status = event.get("status")
        if status == "success":
            st.success(label)
        elif status == "warning":
            st.warning(label)
        elif status == "error":
            st.error(label)
        else:
            st.info(label)
        details = event.get("details") or {}
        if details:
            st.code(json.dumps(details, ensure_ascii=False, indent=2), language="json")


def load_monitor_history() -> List[Dict[str, Any]]:
    if not MONITOR_LOG.exists():
        return []
    history = []
    for line in MONITOR_LOG.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                history.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return history[-50:]


def append_monitor_history(entry: Dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(MONITOR_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_monitor_once(min_score: float) -> tuple[int, int]:
    results = fetch_and_analyze(min_risk_score=min_score)
    checked = len(results)
    alerted = sum(1 for r in results if r.get("notified"))
    st.session_state.total_checked += checked
    st.session_state.total_alerted += alerted
    st.session_state.last_results = results
    for r in results:
        append_monitor_history({
            "timestamp": datetime.now().isoformat(),
            "subject": r["email_data"].get("subject", "")[:80],
            "sender": r["email_data"].get("sender", ""),
            "score": r["ml_result"].get("score", 0),
            "notified": r.get("notified", False),
        })
    return checked, alerted


def monitor_loop(min_score: float, interval: int):
    """Kiem tra email va tu dong rerun de cap nhat UI."""
    pass


init_session_state()

with st.sidebar:
    st.markdown(
        '<div class="brand-lockup"><div class="brand-mark">ES</div>'
        '<div><div class="sidebar-brand">Email Security</div>'
        '<div class="sidebar-caption">Threat monitoring workspace</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="brand-status"><span class="brand-status-dot"></span>SECURITY OPERATIONS CONSOLE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Workspace</div>', unsafe_allow_html=True)
    pages = [
        "Dashboard",
        "Phân tích email",
        "Auto Monitor",
        "Đánh giá mô hình",
        "Cấu hình model",
        "Multi-Agent Pipeline",
        "Cấu hình LLM",
        "Cấu hình Gmail",
        "Cấu hình Telegram",
    ]
    for page in pages:
        is_active = st.session_state.active_page == page
        if st.button(
            page,
            key=f"nav_{page}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_page = page
            st.rerun()

llm_model = st.session_state.llm_model_value
llm_api_key = st.session_state.llm_api_key_value
active_page = st.session_state.active_page
provider_names = {"google_gemini": "Google Gemini"}
llm_provider_name = provider_names.get(st.session_state.llm_provider_value, st.session_state.llm_provider_value)
monitor_status = "Running" if st.session_state.monitor_running else "Paused"
monitor_dot_class = "is-active" if st.session_state.monitor_running else ""
page_headings = {
    "Dashboard": ("Dashboard tổng quan", "Tổng quan đề tài, mô hình triển khai và kết quả benchmark."),
    "Phân tích email": ("Phân tích email", "Kiểm tra email, bằng chứng rủi ro và trao đổi với analyst AI."),
    "Auto Monitor": ("Auto Monitor", "Theo dõi hộp thư Gmail và quản lý cảnh báo tự động."),
    "Đánh giá mô hình": ("Đánh giá mô hình", "So sánh các chỉ số trên tập dữ liệu kiểm tra."),
    "Cấu hình model": ("Cấu hình model", "Chọn model ML dùng cho phân tích email và Auto Monitor."),
    "Multi-Agent Pipeline": ("Multi-Agent Pipeline", "Luồng xử lý email từ bước parse đến cảnh báo SecOps."),
    "Cấu hình LLM": ("Cấu hình LLM", "Quản lý nhà cung cấp, model và API key dùng cho phân tích email."),
    "Cấu hình Gmail": ("Cấu hình Gmail", "Nhập tài khoản và App Password để Auto Monitor đọc hộp thư."),
    "Cấu hình Telegram": ("Cấu hình Telegram", "Thiết lập Bot Token và Chat ID để nhận cảnh báo."),
}
page_title, page_description = page_headings.get(active_page, page_headings["Dashboard"])
active_model_key = get_active_model_key()
active_model_label = MODEL_LABELS.get(active_model_key, active_model_key)
MODEL_BENCHMARK_NAMES = {
    "rf": "Random Forest (200 cay)",
    "lr": "Logistic Regression",
    "mnb": "Multinomial Naive Bayes",
    "xgb": "XGBoost",
}
MODEL_CONFIG_SUMMARY = {
    "rf": "Random Forest · 200 cây · max_depth=40 · balanced",
    "lr": "Logistic Regression · SAGA · MaxAbsScaler · C=1.0",
    "mnb": "Multinomial Naive Bayes · alpha=0.01",
    "xgb": "XGBoost · 200 vòng · depth=6 · learning_rate=0.2",
}

st.markdown(
    f"""
    <div class="page-heading">
        <div>
            <div class="eyebrow">EMAIL SECURITY OPERATIONS</div>
            <div class="app-title">{page_title}</div>
            <div class="app-subtitle">{page_description}</div>
        </div>
        <div class="live-pill"><span class="live-dot {monitor_dot_class}">●</span>Auto Monitor {monitor_status}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


if active_page == "Dashboard":
    st.markdown(
        f"""
        <section class="dashboard-hero">
          <div class="hero-layout">
            <div class="hero-copy">
              <div class="hero-eyebrow">EMAIL SECURITY · PROJECT OVERVIEW</div>
              <div class="hero-title">Hybrid Phishing<br>Email Analyzer</div>
              <div class="hero-description">Hệ thống hỗ trợ phát hiện email lừa đảo bằng cách kết hợp Machine Learning, phân tích ngữ cảnh bằng mô hình ngôn ngữ lớn và cảnh báo cho SecOps.</div>
              <div class="hero-chips">
                <span class="hero-chip">{active_model_label.upper()}</span>
                <span class="hero-chip">TF-IDF + SECURITY FEATURES</span>
                <span class="hero-chip">LLM ANALYST</span>
              </div>
            </div>
            <div class="hero-flow" aria-label="Email analysis flow">
              <span class="flow-node">EMAIL</span><span class="flow-link"></span>
              <span class="flow-node">ML</span><span class="flow-link"></span>
              <span class="flow-node">LLM</span><span class="flow-link"></span>
              <span class="flow-node">ALERT</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    project_col, runtime_col = st.columns([1.4, 1], gap="large")
    with project_col:
        with st.container(border=True):
            st.markdown("#### Đề tài")
            st.write(
                "**Xây dựng hệ thống phát hiện email phishing theo kiến trúc Hybrid Multi-Agent.** "
                "Hệ thống đọc email `.eml`/`.txt`, trích xuất metadata và URL, đánh giá rủi ro, "
                "sau đó tạo phân tích và khuyến nghị xử lý."
            )
            st.caption("Luồng chính: Parse email → ML scoring → LLM analyst → SecOps alert")
    with runtime_col:
        with st.container(border=True):
            st.markdown("#### Mô hình đang dùng trong ứng dụng")
            st.markdown(
                f"- **ML:** {active_model_label} + TF-IDF, kết hợp heuristic guardrails\n"
                f"- **Cấu hình:** {MODEL_CONFIG_SUMMARY.get(active_model_key, 'Không rõ')}\n"
                f"- **LLM:** {llm_provider_name} · `{llm_model}`\n"
                "- **Ngưỡng kết luận:** 60% trở lên → Phishing\n"
                "- **Tích hợp monitor:** Gmail IMAP → Telegram"
            )

    overview = st.columns(4, gap="medium")
    with overview[0]:
        st.metric("Email monitor đã kiểm tra", st.session_state.total_checked)
    with overview[1]:
        st.metric("Email đạt ngưỡng cảnh báo", st.session_state.total_alerted)
    with overview[2]:
        st.metric("Ngưỡng monitor hiện tại", f"{st.session_state.get('min_score', 60)}%")
    with overview[3]:
        st.metric("Monitor", "Đang chạy" if st.session_state.monitor_running else "Tạm dừng")

    st.divider()
    st.markdown(f'<div class="section-kicker">{active_model_label} · benchmark</div>', unsafe_allow_html=True)
    comparison_csv = RESULTS_DIR / "model_comparison.csv"
    if comparison_csv.exists():
        try:
            import pandas as pd
            benchmark_df = pd.read_csv(comparison_csv, encoding="utf-8-sig")
            selected_name = MODEL_BENCHMARK_NAMES.get(active_model_key, active_model_label)
            selected_rows = benchmark_df[benchmark_df["Model"].astype(str) == selected_name]
            if selected_rows.empty:
                raise ValueError(f"Không tìm thấy benchmark cho {active_model_label}.")
            model_row = selected_rows.iloc[0]
            metric_cols = st.columns(4, gap="medium")
            for column, (label, key) in zip(metric_cols, [
                ("Accuracy", "Accuracy"), ("Precision", "Precision (weighted)"),
                ("Recall", "Recall (weighted)"), ("F1 score", "F1 (weighted)"),
            ]):
                with column:
                    st.metric(label, model_row[key])
            matrix_col, details_col = st.columns([1.2, 1], gap="large")
            with matrix_col:
                st.markdown("#### Kết quả phân loại")
                st.caption(f"{active_model_label} · ngưỡng 0,5 · holdout benchmark")
                st.markdown(f"""
                    <table class="rf-matrix">
                      <thead><tr><th></th><th>Dự đoán an toàn</th><th>Dự đoán phishing</th></tr></thead>
                      <tbody>
                        <tr><th>Thực tế an toàn</th><td class="good"><span class="matrix-value">{int(model_row['TN']):,}</span><span class="matrix-label">Nhận diện đúng</span></td><td class="miss"><span class="matrix-value">{int(model_row['FP']):,}</span><span class="matrix-label">Báo nhầm</span></td></tr>
                        <tr><th>Thực tế phishing</th><td class="miss"><span class="matrix-value">{int(model_row['FN']):,}</span><span class="matrix-label">Bỏ sót</span></td><td class="good"><span class="matrix-value">{int(model_row['TP']):,}</span><span class="matrix-label">Phát hiện đúng</span></td></tr>
                      </tbody>
                    </table>
                """, unsafe_allow_html=True)
            with details_col:
                st.markdown("#### Model được chọn")
                with st.container(border=True):
                    st.markdown(
                        f"**{active_model_label}**\n\n"
                        f"- Cấu hình artifact: **{MODEL_CONFIG_SUMMARY.get(active_model_key, 'Không rõ')}**\n"
                        f"- Số mẫu benchmark: **{int(model_row['TP'] + model_row['FP'] + model_row['TN'] + model_row['FN']):,}**\n"
                        f"- AUC: **{model_row['ROC AUC']}** · FNR: **{model_row['FNR']}**"
                    )
                    st.caption("Các chỉ số đọc từ model_comparison.csv; benchmark được tạo trước lần train artifact đầy đủ và có thể dùng cấu hình cũ. Dùng tab Đánh giá mô hình để xem bảng so sánh.")
        except Exception as exc:
            st.warning(f"Không đọc được benchmark cho model đã chọn: {exc}")
    else:
        st.info("Chưa có model_comparison.csv. Chạy `python scripts/compare_models.py` để tạo benchmark.")

elif active_page == "Phân tích email":
    left_col, right_col = st.columns([0.9, 1.4], gap="large")

    with left_col:
        st.subheader("Email đầu vào và mức rủi ro")
        uploaded_file = st.file_uploader("Keo tha hoac chon file .eml/.txt", type=["eml", "txt"])

        if uploaded_file and uploaded_file.name != st.session_state.uploaded_filename:
            st.session_state.pipeline_result = None
            st.session_state.messages = []
            st.session_state.uploaded_filename = uploaded_file.name

        if st.button("Chay Multi-agent Pipeline", type="primary", use_container_width=True):
            if not uploaded_file:
                st.error("Vui long upload email truoc khi phan tich.")
            elif not llm_api_key:
                st.error("Vui lòng cấu hình API key trong mục Cấu hình LLM.")
            else:
                with st.spinner("Dang chay Parse -> ML -> LLM -> Alert..."):
                    result = run_pipeline(uploaded_file, api_key=llm_api_key, model_name=llm_model)
                st.session_state.pipeline_result = result
                st.session_state.messages = [{"role": "assistant", "content": result["llm_analysis"]}]
                st.success("Pipeline da hoan tat.")
                st.rerun()

        result = st.session_state.pipeline_result
        if result:
            email_data = result["email_data"]
            ml_result = result["ml_result"]
            show_risk(float(ml_result.get("score", 0)))
            st.caption(f"Nguồn chấm điểm: {ml_result.get('source')} · Ngưỡng kết luận: 60%")

            sender_text = escape(str(email_data.get("sender", "Không rõ")))
            date_text = escape(str(email_data.get("date", "Không rõ")))
            subject_text = escape(str(email_data.get("subject", "Không có tiêu đề")))
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    f'<div class="email-meta-card"><div class="email-meta-label">Người gửi</div><div class="email-meta-value">{sender_text}</div></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f'<div class="email-meta-card"><div class="email-meta-label">Ngày gửi</div><div class="email-meta-value">{date_text}</div></div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div class="email-subject-card"><span class="email-subject-label">Tiêu đề email</span>{subject_text}</div>',
                unsafe_allow_html=True,
            )
            urls = email_data.get("urls") or []
            if urls:
                st.markdown(f"**Liên kết trong email** · {len(urls)}")
                for idx, url in enumerate(urls, start=1):
                    safe_url = escape(str(url))
                    st.markdown(
                        f'<div class="email-url-card"><div class="email-url-index">URL {idx:02d}</div><div class="email-url-value">{safe_url}</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Không phát hiện liên kết trong nội dung email.")
            with st.expander("Nội dung email gốc", expanded=False):
                st.text_area(
                    "Nội dung email",
                    value=str(email_data.get("body", "")),
                    height=280,
                    disabled=True,
                    label_visibility="collapsed",
                )
        else:
            st.info("Upload email va chay pipeline de xem diem ML, URL va alert.")

    with right_col:
        st.subheader("Phân tích viên AI")
        if result:
            score = max(0, min(int(float(result["ml_result"].get("score", 0))), 100))
            verdict = "PHISHING" if score >= 60 else "NOT PHISHING"
            st.caption(f"Kết luận AI được ràng buộc theo kết quả hệ thống: **{verdict} · {score}%**. Phần dưới giải thích bằng chứng và khuyến nghị.")
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown("Hay upload email va bam **Chay Multi-agent Pipeline** de tao bao cao dau tien.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        prompt = st.chat_input("Hoi them ve email, URL, bang chung hoac huong xu ly...")
        if prompt:
            if not st.session_state.pipeline_result:
                st.warning("Can chay pipeline truoc khi chat voi tac nhan AI.")
                st.stop()
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Agent dang suy luan tren context email..."):
                    result = st.session_state.pipeline_result
                    answer = continue_chat(result["email_data"], result["ml_result"], st.session_state.messages, api_key=llm_api_key, model_name=llm_model)
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
elif active_page == "Auto Monitor":
    st.subheader("Theo dõi email tự động")
    st.caption("Lấy email từ Gmail, phân tích phishing và gửi cảnh báo Telegram.")

    if st.session_state.monitor_running:
        now = time.time()
        last = st.session_state.get("monitor_last_check", 0)
        interval = st.session_state.get("interval", 30)
        if now - last >= interval:
            st.session_state.monitor_last_check = now
            with st.spinner(f"Dang kiem tra... (moi {interval}s)"):
                run_monitor_once(st.session_state.get("min_score", 60))
            st.rerun()

    sc1, sc2, sc3 = st.columns([2, 1, 1])
    with sc1:
        if st.session_state.monitor_running:
            st.success("Trang thai: DANG CHAY")
            interval_val = st.session_state.get("interval", 30)
            st.components.v1.html(
                f"<script>setTimeout(function(){{window.parent.location.reload()}}, {interval_val * 1000})</script>",
                height=0,
            )
        else:
            st.error("Trang thai: DA DUNG")
    with sc2:
        st.metric("Email da kiem tra", st.session_state.total_checked)
    with sc3:
        st.metric("Email đạt ngưỡng cảnh báo", st.session_state.total_alerted)

    st.divider()

    cc1, cc2 = st.columns([1, 2])
    with cc1:
        st.subheader("Dieu khien")
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("Start", type="primary", use_container_width=True):
                st.session_state.monitor_running = True
                st.session_state.monitor_last_check = 0
                st.rerun()
        with bc2:
            if st.button("Stop", type="secondary", use_container_width=True):
                st.session_state.monitor_running = False
                st.session_state.monitor_thread = None
                st.rerun()

        if st.button("Kiem tra ngay (1 lan)", use_container_width=True):
            with st.spinner("Dang kiem tra..."):
                checked, alerted = run_monitor_once(st.session_state.get("min_score", 60))
            st.success(f"Kiem tra xong: {checked} email, {alerted} canh bao.")
            st.rerun()

        if st.button("Xoa lich su", use_container_width=True):
            if MONITOR_LOG.exists():
                MONITOR_LOG.unlink()
            st.session_state.total_checked = 0
            st.session_state.total_alerted = 0
            st.rerun()

    with cc2:
        st.subheader("Cau hinh")
        s1, s2 = st.columns(2)
        with s1:
            st.session_state["min_score"] = st.slider("Diem toi thieu de gui canh bao", 30, 95, 60, 5)
        with s2:
            st.session_state["interval"] = st.number_input("Thoi gian kiem tra (giay)", 10, 300, 30, 10)
        st.info(f"Gmail: {os.getenv('GMAIL_ADDRESS', 'Chua cau hinh')}")
        st.info(f"Telegram Chat ID: {os.getenv('TELEGRAM_CHAT_ID', 'Chua cau hinh')}")

    st.divider()

    st.subheader("Lich su kiem tra")
    history = load_monitor_history()
    if not history:
        st.info("Chua co lich su. Bam 'Kiem tra ngay' hoac 'Start' de bat dau.")
    else:
        rows = []
        for h in reversed(history):
            rows.append({
                "Thoi gian": h.get("timestamp", "")[:19],
                "Tieu de": h.get("subject", "")[:50],
                "Nguoi gui": h.get("sender", "")[:30],
                "Diem": h.get("score", 0),
                "Gui TB": "Co" if h.get("notified") else "Khong",
            })
        st.dataframe(rows, use_container_width=True, height=400)

    if st.session_state.last_results:
        st.divider()
        st.subheader("Ket qua moi nhat")
        for r in st.session_state.last_results[:5]:
            ed = r["email_data"]
            ml = r["ml_result"]
            sc = ml.get("score", 0)
            with st.expander(f"Diem {sc}% | {ed.get('subject', '')[:50]}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Nguoi gui:** {ed.get('sender', '')}")
                    st.write(f"**Ngay:** {ed.get('date', '')}")
                    st.write(f"**Gui TB:** {'Co' if r.get('notified') else 'Khong'}")
                with c2:
                    st.write(f"**Diem ML:** {sc}%")
                    st.write(f"**Nguon:** {ml.get('source', '')}")
                    urls = ed.get("urls", [])
                    if urls:
                        st.write(f"**URLs:** {len(urls)}")
                        for u in urls[:3]:
                            st.code(u)

elif active_page == "Đánh giá mô hình":
    st.subheader("Hiệu quả mô hình trên tập kiểm tra")
    st.markdown(
        "Ket qua do tren **40.859 email kiem thu** (20% ngau nhien tu merged_clean.csv, "
        "stratify, seed=42). Moi model duoc huan luyen tren 163.435 email con lai. "
        "Chay lai bang: `python scripts/compare_models.py`.",
    )

    eval_csv = RESULTS_DIR / "model_comparison.csv"
    roc_png = RESULTS_DIR / "roc_comparison.png"

    # --- Bang chi so ---
    if eval_csv.exists():
        st.subheader("Bang chi so so sanh 4 mo hinh")
        try:
            import pandas as pd
            _df_eval = pd.read_csv(eval_csv, encoding="utf-8-sig")
            st.dataframe(_df_eval, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"Khong doc duoc CSV: {exc}")
    else:
        st.info("Chua co file model_comparison.csv — chay `python scripts/compare_models.py` truoc.")

    # --- ROC curve ---
    st.divider()
    st.subheader("ROC Curve - AUC")
    if roc_png.exists():
        st.image(str(roc_png), use_container_width=True)
        st.caption(
            "Moi duong la ROC cua mot model: do cong len cang tot. AUC = 1.0 la hoan hao, "
            "0.5 la doan ngau nhien (duong cham)."
        )
    else:
        st.info("Chua co anh ROC — chay `python scripts/compare_models.py` truoc.")

    # --- Ma tran nham lan 4 model ---
    st.divider()
    st.subheader("Kết quả phân loại của 4 mô hình")
    st.caption(
        "Hàng là nhãn thực tế, cột là phân loại của mô hình. "
        "Xem email sạch bị báo nhầm và email lừa đảo bị bỏ sót để đánh giá rủi ro."
    )
    cm_files = {
        "Random Forest": "confusion_matrix_rf.png",
        "Logistic Regression": "confusion_matrix_lr.png",
        "Multinomial Naive Bayes": "confusion_matrix_mnb.png",
        "XGBoost": "confusion_matrix_xgb.png",
    }
    available_cm = {
        name: RESULTS_DIR / fname
        for name, fname in cm_files.items()
        if (RESULTS_DIR / fname).exists()
    }
    if available_cm:
        cols = st.columns(2)
        for i, (name, path) in enumerate(available_cm.items()):
            with cols[i % 2]:
                st.markdown(f"**{name}**")
                st.image(str(path), use_container_width=True)
    else:
        st.info(
            "Chua co anh ma tran nham lan — chay `python scripts/compare_models.py` "
            "(script se tu luu results/confusion_matrix_*.png)."
        )

elif active_page == "Cấu hình model":
    st.markdown('<div class="section-kicker">MODEL LIBRARY · RUNTIME SELECTION</div>', unsafe_allow_html=True)
    st.write("Chọn model ML mà ứng dụng và Auto Monitor sẽ dùng. Các lựa chọn bên dưới chỉ gồm những artifact đã được lưu.")
    available_models = get_available_models()
    active_model_key = get_active_model_key()
    model_descriptions = {
        "rf": "Rừng cây quyết định; mô hình đang được tích hợp ban đầu của đồ án.",
        "lr": "Mô hình tuyến tính dùng SAGA và MaxAbsScaler để xử lý đặc trưng có thang đo khác nhau.",
        "mnb": "Naive Bayes đa thức; thường phù hợp với đặc trưng văn bản không âm như TF-IDF.",
        "xgb": "Gradient boosting; các cây được xây nối tiếp để cải thiện dự đoán trước đó.",
    }
    if not available_models:
        st.warning("Chưa tìm thấy artifact model. Hãy chạy `python scripts/train_model_artifacts.py` trước.")
    else:
        for row_start in range(0, len(available_models), 2):
            card_cols = st.columns(2, gap="large")
            for col, model_key in zip(card_cols, available_models[row_start:row_start + 2]):
                model_label = MODEL_LABELS.get(model_key, model_key)
                is_active = model_key == active_model_key
                with col:
                    with st.container(border=True):
                        status = "ĐANG DÙNG" if is_active else "SẴN SÀNG"
                        st.markdown(f"#### {model_label}")
                        st.caption(status)
                        st.write(model_descriptions.get(model_key, "Model phân loại email."))
                        st.code(MODEL_CONFIG_SUMMARY.get(model_key, ""), language="text")
                        artifact_path = Path(__file__).resolve().parent / "models" / f"phishing_{model_key}.pkl"
                        st.caption(f"Artifact: `{artifact_path.name}` · {artifact_path.stat().st_size / (1024 * 1024):.1f} MB")
                        if is_active:
                            st.button("Đang được chọn", key=f"model_active_{model_key}", disabled=True, use_container_width=True)
                        elif st.button(f"Dùng {model_label}", key=f"model_activate_{model_key}", type="primary", use_container_width=True):
                            set_active_model_key(model_key)
                            st.toast(f"Đã chuyển sang {model_label}")
                            st.rerun()
        st.caption("Thay đổi được lưu vào `config/active_model.json` và áp dụng ngay cho phân tích email cùng Auto Monitor.")

elif active_page == "Multi-Agent Pipeline":
    st.markdown('<div class="section-kicker">Processing workflow</div>', unsafe_allow_html=True)
    st.markdown(read_pi_markdown("chains/chain.md") or "Chưa có mô tả pipeline.")
    st.divider()
    st.subheader("Pipeline run gần nhất")
    latest_result = st.session_state.pipeline_result
    if latest_result:
        st.caption(f"Email: {latest_result.get('email_data', {}).get('filename', 'Không rõ')}")
        render_pipeline_logs(latest_result)
        with st.expander("Alert JSON", expanded=False):
            st.json(latest_result.get("alert", {}))
    else:
        st.info("Chưa có lần chạy nào trong phiên này. Vào Phân tích email để chạy pipeline.")
    st.divider()
    st.caption("Training ML model: `python scripts/train_ml_model.py`")

elif active_page == "Cấu hình LLM":
    st.markdown('<div class="section-kicker">Language model configuration</div>', unsafe_allow_html=True)
    st.markdown(
        "Chọn nhà cung cấp, model và API key dùng cho **phân tích email** và **chat với Analyst Agent**. "
        "Thông tin cấu hình sẽ được lưu vào `.env` của dự án. Hiện tại backend đã tích hợp Google Gemini; "
        "cấu trúc trang này được thiết kế để bổ sung nhà cung cấp khác sau."
    )
    provider_values = {"Google Gemini": "google_gemini"}
    provider_labels = list(provider_values)
    current_provider = next(
        (label for label, value in provider_values.items() if value == st.session_state.llm_provider_value),
        provider_labels[0],
    )
    model_options = [
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
    ]
    if "llm_provider_input" not in st.session_state:
        st.session_state.llm_provider_input = current_provider
    if "llm_model_input" not in st.session_state:
        st.session_state.llm_model_input = st.session_state.llm_model_value
    if "llm_api_key_input" not in st.session_state:
        st.session_state.llm_api_key_input = st.session_state.llm_api_key_value

    with st.container(border=True):
        with st.form("llm_settings_form"):
            st.selectbox("Nhà cung cấp LLM", provider_labels, key="llm_provider_input")
            st.selectbox("Model", model_options, key="llm_model_input")
            st.text_input("API key", type="password", key="llm_api_key_input")
            save_settings = st.form_submit_button("Lưu cấu hình LLM", type="primary", use_container_width=True)

        if save_settings:
            saved_provider_label = st.session_state.llm_provider_input
            saved_provider = provider_values[saved_provider_label]
            saved_model = st.session_state.llm_model_input
            saved_key = st.session_state.llm_api_key_input.strip()
            try:
                save_env_values({
                    "LLM_PROVIDER": saved_provider,
                    "LLM_MODEL": saved_model,
                    "LLM_API_KEY": saved_key,
                    # Giữ alias để tương thích với adapter Gemini hiện tại.
                    "GEMINI_MODEL": saved_model,
                    "GEMINI_API_KEY": saved_key,
                })
                st.session_state.llm_provider_value = saved_provider
                st.session_state.llm_model_value = saved_model
                st.session_state.llm_api_key_value = saved_key
                st.success("Đã lưu cấu hình LLM vào .env.")
                st.rerun()
            except Exception as exc:
                st.error(f"Không thể lưu cấu hình vào .env: {exc}")

    st.divider()
    st.markdown("#### Trạng thái kết nối")
    configured = bool(st.session_state.llm_api_key_value)
    if configured:
        st.success(f"Đã cấu hình {llm_provider_name}: **{st.session_state.llm_model_value}**")
    else:
        st.warning("Chưa có API key. Nhập key để bật phân tích LLM và chat với Analyst Agent.")

elif active_page == "Cấu hình Gmail":
    st.markdown('<div class="section-kicker">Gmail IMAP connection</div>', unsafe_allow_html=True)
    st.markdown(
        "Nhập Gmail và **App Password** dùng riêng cho Auto Monitor. "
        "Thông tin sẽ được ghi vào `.env`, không đưa vào Git."
    )
    if "gmail_address_input" not in st.session_state:
        st.session_state.gmail_address_input = st.session_state.gmail_address_value
    if "gmail_app_password_input" not in st.session_state:
        st.session_state.gmail_app_password_input = st.session_state.gmail_app_password_value

    with st.container(border=True):
        with st.form("gmail_settings_form"):
            st.text_input("Địa chỉ Gmail", key="gmail_address_input", placeholder="name@gmail.com")
            st.text_input("Gmail App Password", key="gmail_app_password_input", type="password")
            save_gmail = st.form_submit_button("Lưu cấu hình Gmail", type="primary", use_container_width=True)
        if save_gmail:
            address = st.session_state.gmail_address_input.strip()
            password = st.session_state.gmail_app_password_input.strip()
            try:
                save_env_values({"GMAIL_ADDRESS": address, "GMAIL_APP_PASSWORD": password})
                st.session_state.gmail_address_value = address
                st.session_state.gmail_app_password_value = password
                st.success("Đã lưu cấu hình Gmail vào .env.")
                st.rerun()
            except Exception as exc:
                st.error(f"Không thể lưu cấu hình Gmail: {exc}")

    if st.session_state.gmail_address_value and st.session_state.gmail_app_password_value:
        st.success(f"Gmail đã được cấu hình: **{st.session_state.gmail_address_value}**")
    else:
        st.warning("Chưa cấu hình đầy đủ Gmail. Cần địa chỉ Gmail và App Password để dùng Auto Monitor.")

elif active_page == "Cấu hình Telegram":
    st.markdown('<div class="section-kicker">Telegram alert delivery</div>', unsafe_allow_html=True)
    st.markdown(
        "Nhập thông tin bot nhận cảnh báo phishing. Bot Token được che khi nhập và lưu vào `.env`."
    )
    if "telegram_bot_token_input" not in st.session_state:
        st.session_state.telegram_bot_token_input = st.session_state.telegram_bot_token_value
    if "telegram_chat_id_input" not in st.session_state:
        st.session_state.telegram_chat_id_input = st.session_state.telegram_chat_id_value

    with st.container(border=True):
        with st.form("telegram_settings_form"):
            st.text_input("Telegram Bot Token", key="telegram_bot_token_input", type="password")
            st.text_input("Telegram Chat ID", key="telegram_chat_id_input", placeholder="Ví dụ: 123456789")
            save_telegram = st.form_submit_button("Lưu cấu hình Telegram", type="primary", use_container_width=True)
        if save_telegram:
            token = st.session_state.telegram_bot_token_input.strip()
            chat_id = st.session_state.telegram_chat_id_input.strip()
            try:
                save_env_values({"TELEGRAM_BOT_TOKEN": token, "TELEGRAM_CHAT_ID": chat_id})
                st.session_state.telegram_bot_token_value = token
                st.session_state.telegram_chat_id_value = chat_id
                st.success("Đã lưu cấu hình Telegram vào .env.")
                st.rerun()
            except Exception as exc:
                st.error(f"Không thể lưu cấu hình Telegram: {exc}")

    if st.session_state.telegram_bot_token_value and st.session_state.telegram_chat_id_value:
        st.success("Telegram đã được cấu hình.")
    else:
        st.warning("Chưa cấu hình đầy đủ Telegram Bot Token và Chat ID.")
