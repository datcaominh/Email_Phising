# Email_Phising

Hybrid Phishing Email Analyzer

Ung dung Streamlit phan tich email phishing theo pipeline hybrid:

1. Parse file `.eml` hoac `.txt`.
2. ML Engine tinh xac suat phishing bang Random Forest + TF-IDF (nguong 60%).
3. LLM Agent phan tich ngu canh email (runtime hien tich hop Google Gemini).
4. Orchestrator tao alert JSON chuan hoa cho SecOps.
5. Tab "Danh gia mo hinh" hien thi bang chi so, ROC curve, ma tran nham lan 4 mo hinh.

## Cai dat

```powershell
cd D:\TLCN
python -m pip install -e .
```

Hoac cai truc tiep:

```powershell
python -m pip install streamlit pandas scikit-learn joblib openai python-dotenv google-genai xgboost matplotlib
```

## Cau hinh API key

Tao file `.env` tu `.env.example`:

```text
LLM_PROVIDER=google_gemini
LLM_MODEL=gemini-3.6-flash
LLM_API_KEY=your_llm_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Chay ung dung

```powershell
python -m streamlit run app/main.py
```

Wrapper cu van hoat dong:

```powershell
python -m streamlit run app.py
```

## Du lieu huan luyen

Dataset: 206.722 email da gop tu 6 nguồn (IEEE ICMI/ISDFS 2024 - Champa, Rabbi & Zibran, Idaho State University; CEAS; Enron; Ling; Nazario; Radev), da loai bo trung lap va null.

```text
data_train/processed/merged_clean.csv
```

Schema: `sender, receiver, date, subject, body, urls, label`

- **Features**: TF-IDF 30.000 + 9 Security Features = 30.009 chieu
- **Train/Test**: 80/20 stratified, seed 42 → 163.435 / 40.859 email
- **Nhan**: 0 = Not Phishing, 1 = Phishing
- **Nguong quyet dinh**: 60% (xem Master_Theory.md, muc E7)

## Train ML model

```powershell
python scripts/train_ml_model.py
```

Model RF se duoc luu tai `app/models/phishing_rf.pkl`. De train va luu ca bon model co the chon trong UI:

```powershell
python scripts/train_model_artifacts.py
```

Script nay fit preprocessing va classifier tren toan bo tap da loc (204.294 email), sau do tao cac artifact:

```text
app/models/phishing_rf.pkl
app/models/phishing_lr.pkl
app/models/phishing_xgb.pkl
app/models/phishing_mnb.pkl
```

UI co selectbox **Model ML dang dung** o sidebar. Lua chon duoc luu trong `config/active_model.json` va dung cho ca phan tich email thu cong va Auto Monitor. `compare_models.py` van danh gia tren holdout; artifact train toan bo corpus khong nen dung de tinh chi so test.

## So sanh 4 mo hinh (LR, XGBoost, RF, MNB)

Chay toan bo (khoang 20 phut, XGBoost cham nhat):

```powershell
python scripts/compare_models.py
```

Ket qua duoc luu tai:

```text
results/model_comparison.csv            # bang chi so day du (Accuracy, F1, AUC, FPR, FNR, TP/FP/TN/FN, thoi gian)
results/roc_comparison.png              # bieu do ROC so sanh 4 model
results/confusion_matrix_rf.png         # ma tran nham lan (heatmap) tung model
results/confusion_matrix_lr.png
results/confusion_matrix_mnb.png
results/confusion_matrix_xgb.png
```

Mo app → tab "Danh gia mo hinh" de xem truc tiep; chup man hinh chen vao bao cao.

## Thí nghiem chon nguong 60%

```powershell
python scripts/threshold_analysis.py
```

Output: `results/threshold_analysis.csv` (FPR/FNR tai 4 nguong, co/khong guardrail).

## Chuan bi du lieu fine-tuning

```powershell
python scripts/prepare_llm_data.py
```

## Tao OpenAI fine-tuning job

```powershell
python scripts/fine_tune_llm.py
```

Runtime app hien dung provider Google Gemini; provider, model va API key duoc quan ly qua cau hinh LLM. OpenAI fine-tune la script rieng cho pipeline huan luyen.

## Xem log pipeline .pi

Sau khi bam `Chay Multi-agent Pipeline`, mo expander `Pipeline Logs (.pi)` trong cot trai de xem tung buoc:

```text
.pi/chains/parse
.pi/skills/ml
.pi/agents/llm
.pi/data/alert
```

Log cung duoc ghi dang JSONL tai:

```text
logs/pipeline.log
```
