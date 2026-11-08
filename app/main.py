"""Streamlit UI cho he thong Hybrid Phishing Analysis + Auto Monitor Dashboard.

Cach chay:
    streamlit run app/main.py
"""

from __future__ import annotations

import json
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

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.orchestrator import continue_chat, read_pi_markdown, run_pipeline
from app.email_fetcher import fetch_and_analyze

st.set_page_config(
    page_title="Hybrid Phishing Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main .block-container { padding-top: 1.6rem; padding-bottom: 2rem; }
        .app-title { font-size: 2rem; font-weight: 800; margin-bottom: 0.15rem; }
        .app-subtitle { color: #5f6b7a; font-size: 0.98rem; margin-bottom: 1rem; }
        .signal-box {
            border: 1px solid #e4e8ef; border-radius: 8px;
            padding: 0.75rem 0.85rem; background: #fbfcfe;
            margin-bottom: 0.5rem; word-break: break-word;
        }
        div[data-testid="stMetric"] {
            background: #ffffff; border: 1px solid #e6eaf0;
            border-radius: 8px; padding: 0.65rem 0.8rem;
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_risk(score: float) -> None:
    normalized = max(0, min(int(score), 100))
    if normalized >= 60:
        st.error(f"Ket luan: PHISHING (diem {normalized}%)")
    else:
        st.success(f"Ket luan: NOT PHISHING (diem {normalized}%)")
    st.progress(normalized / 100)


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
    st.title("Hybrid Phishing")
    st.caption("Multi-agent pipeline: Parse -> ML -> LLM -> Alert")
    gemini_model = st.selectbox(
        "Gemini model",
        ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"],
    )
    api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    st.divider()
    st.markdown("#### Pipeline")
    st.markdown(read_pi_markdown("chains/chain.md") or "Chua co cau hinh pipeline.")
    st.divider()
    st.info("Training ML: `python scripts/train_ml_model.py`")


tab_phish, tab_monitor, tab_eval = st.tabs(
    ["Phan tich Email", "Auto Monitor", "Danh gia mo hinh"]
)


with tab_phish:
    st.markdown('<div class="app-title">Hybrid Phishing Email Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Ket hop Random Forest, LLM Agent va canh bao chuan hoa cho SecOps.</div>',
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([0.95, 1.25], gap="large")

    with left_col:
        st.subheader("Email Input & ML Risk")
        uploaded_file = st.file_uploader("Keo tha hoac chon file .eml/.txt", type=["eml", "txt"])

        if uploaded_file and uploaded_file.name != st.session_state.uploaded_filename:
            st.session_state.pipeline_result = None
            st.session_state.messages = []
            st.session_state.uploaded_filename = uploaded_file.name

        if st.button("Chay Multi-agent Pipeline", type="primary", use_container_width=True):
            if not uploaded_file:
                st.error("Vui long upload email truoc khi phan tich.")
            elif not api_key:
                st.error("Vui long nhap Gemini API Key trong sidebar.")
            else:
                with st.spinner("Dang chay Parse -> ML -> LLM -> Alert..."):
                    result = run_pipeline(uploaded_file, api_key=api_key, model_name=gemini_model)
                st.session_state.pipeline_result = result
                st.session_state.messages = [{"role": "assistant", "content": result["llm_analysis"]}]
                st.success("Pipeline da hoan tat.")
                st.rerun()

        result = st.session_state.pipeline_result
        if result:
            email_data = result["email_data"]
            ml_result = result["ml_result"]
            show_risk(float(ml_result.get("score", 0)))
            st.caption(f"Nguon ML: {ml_result.get('source')}")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Nguoi gui", str(email_data.get("sender", "Khong ro"))[:70])
            with c2:
                st.metric("Ngay", str(email_data.get("date", "Khong ro"))[:70])
            st.info(f"**Tieu de:** {email_data.get('subject', 'Khong co tieu de')}")
            urls = email_data.get("urls") or []
            if urls:
                st.warning(f"Phat hien {len(urls)} URL.")
                for idx, url in enumerate(urls, start=1):
                    st.markdown(f'<div class="signal-box"><strong>URL {idx}</strong><br>{url}</div>', unsafe_allow_html=True)
            else:
                st.success("Khong phat hien URL trong body.")
            with st.expander("Alert JSON chuan hoa", expanded=False):
                st.json(result["alert"])
            with st.expander("Pipeline Logs (.pi)", expanded=True):
                render_pipeline_logs(result)
            with st.expander("Noi dung email goc", expanded=False):
                st.text_area("Body", value=str(email_data.get("body", "")), height=240, disabled=True, label_visibility="collapsed")
        else:
            st.info("Upload email va chay pipeline de xem diem ML, URL va alert.")

    with right_col:
        st.subheader("Phishing Analyst Agent")
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
                    answer = continue_chat(result["email_data"], result["ml_result"], st.session_state.messages, api_key=api_key, model_name=gemini_model)
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
        if st.session_state.pipeline_result:
            with st.expander("Raw alert", expanded=False):
                st.code(json.dumps(st.session_state.pipeline_result["alert"], ensure_ascii=False, indent=2), language="json")


with tab_monitor:
    st.title("Auto Email Monitor Dashboard")
    st.caption("Tu dong lay email tu Gmail, phan tich phishing, gui canh bao Telegram.")

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
        st.metric("Canh bao da gui", st.session_state.total_alerted)

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

with tab_eval:
    st.markdown(
        '<div class="app-title">Danh gia mo hinh tren test set</div>',
        unsafe_allow_html=True,
    )
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
    st.subheader("Ma tran nham lan (Confusion Matrix) cua 4 mo hinh")
    st.caption(
        "Hang = nhan thuc te, cot = du doan cua mo hinh. "
        "TN = dung khi noi dung sach, FP = bao oan email sach, "
        "FN = bo sót phishing (nguy hiem nhat), TP = dung khi bat duoc phishing."
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
