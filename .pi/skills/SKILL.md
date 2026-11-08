# Allowed AI/ML Skills

## ML API
- `predict_phishing(email_data)`: goi `app/ml_engine.py`, tra ve `score`, `label`, `source`, `signals`.

## LLM API
- `analyze_email(email_data, ml_result)`: goi `app/llm_agent.py` bang Gemini runtime.
- `chat_about_email(email_data, ml_result, messages)`: tiep tuc hoi dap dua tren context email.

## Gioi han
- Tac nhan khong duoc tu y gui email ra ngoai.
- Tac nhan khong duoc click URL.
- Tac nhan khong duoc ghi API key vao log hoac alert.
