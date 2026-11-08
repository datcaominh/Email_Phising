"""Tao OpenAI fine-tuning job tu file JSONL da chuan bi.

Bien moi truong can co:
    OPENAI_API_KEY=...

Cach chay:
    python scripts/fine_tune_llm.py
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING_FILE = PROJECT_ROOT / "data_train" / "ceas_llm_dataset.jsonl"
BASE_MODEL = os.getenv("OPENAI_FINE_TUNE_BASE_MODEL", "gpt-4o-mini")


def main() -> None:
    """Upload JSONL len OpenAI va tao fine-tuning job."""
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("Thieu OPENAI_API_KEY trong .env hoac bien moi truong.")
    if not TRAINING_FILE.exists():
        raise FileNotFoundError("Hay chay scripts/prepare_llm_data.py truoc.")

    client = OpenAI()

    with TRAINING_FILE.open("rb") as file:
        uploaded_file = client.files.create(file=file, purpose="fine-tune")

    job = client.fine_tuning.jobs.create(
        training_file=uploaded_file.id,
        model=BASE_MODEL,
    )

    print(f"File ID: {uploaded_file.id}")
    print(f"Fine-tuning Job ID: {job.id}")
    print(f"Base model: {BASE_MODEL}")


if __name__ == "__main__":
    main()
