# Multi-agent Pipeline

1. Parse Agent: doc file .eml/.txt, trich xuat sender, receiver, subject, date, body va URL.
2. ML Skill: dung RandomForestClassifier + TfidfVectorizer de tinh xac suat phishing.
3. LLM Analyst Agent: dung Gemini hien tai de phan tich ngu canh, social engineering va diem ML.
4. Alert Formatter: tao alert JSON theo mau .pi/data/sample_alert.json.
5. Response Coordinator: hien thi rui ro, bao cao AI va chat tuong tac trong Streamlit.
