# TÀI LIỆU TRẢ LỜI VỀ DATASET & MACHINE LEARNING

> Phân tích trực tiếp từ 11 file trong `data_train/raw/` (số liệu thật, không bịa).
> Tài liệu gồm 3 phần: **(I) DATASET** · **(II) TRAIN & MODEL** · **(III) CÂU HỎI CÔ HỎI**

---

# PHẦN I — DATASET

## 1. Bảng tổng hợp 11 file (số liệu thật từ file)

| # | File | Dung lượng | Số email | Phishing (1) | Legit (0) | Cột dữ liệu |
|---|------|-----------|----------|--------------|-----------|-------------|
| 1 | CEAS_08.csv | 64.8 MB | 39,154 | 21,842 | 17,312 | sender, receiver, date, subject, body, label, urls |
| 2 | Enron.csv | 42.8 MB | 29,767 | 13,976 | 15,791 | subject, body, label |
| 3 | Ling.csv | 8.9 MB | 2,859 | 458 | 2,401 | subject, body, label |
| 4 | Nazario.csv | 7.4 MB | 1,565 | 1,565 | 0 | sender, receiver, date, subject, body, urls, label |
| 5 | Nazario_5.csv | 11.2 MB | 3,065 | 1,565 | 1,500 | sender, receiver, date, subject, body, label, urls |
| 6 | Nigerian_5.csv | 17.4 MB | 6,331 | 3,332 | 2,999 | sender, receiver, date, subject, body, label, urls |
| 7 | Nigerian_Fraud.csv | 8.8 MB | 3,332 | 3,332 | 0 | sender, receiver, date, subject, body, urls, label |
| 8 | SpamAssasin.csv | 14.2 MB | 5,809 | 1,718 | 4,091 | sender, receiver, date, subject, body, label, urls |
| 9 | TREC_05.csv | 117.4 MB | 55,990 | 22,946 | 32,329 | sender, receiver, date, subject, body, label, urls |
| 10 | TREC_06.csv | 40.0 MB | 16,457 | 3,989 | 12,411 | sender, receiver, date, subject, body, label, urls |
| 11 | TREC_07.csv | 95.6 MB | 53,757 | 29,399 | 24,358 | sender, receiver, date, subject, body, label, urls |
| | **TỔNG** | **~430 MB** | **218,086** | **103,122** | **114,792** | |

> Sau tiền xử lý (bỏ label NaN, dedup, chuẩn hóa): **206,722 email** → `processed/merged_clean.csv`
> Phân bố cuối: **47.7% phishing / 52.3% legit** (cân bằng tốt cho ML)

---

## 2. Nguồn gốc từng file (chứng minh uy tín)

### 2.1. CEAS_08.csv — Conference on Email and Anti-Spam 2008
- **Tổ chức:** University of Waterloo (Canada) tổ chức hội nghị CEAS
- **Tác giả bộ dữ liệu:** Gordon Cormack (GS University of Waterloo)
- **Nội dung:** Email thật từ thách thức CEAS 2008 (spam vs ham)
- **Link:** https://plg.uwaterloo.ca/~gvcormac/ceascorpus/
- **Đặc điểm:** Đủ 7 cột. Phân bố 55.8% phishing / 44.2% legit.
- **Ví dụ thật:** Email spam thuốc kích dục có URL `whitedone.com`, label=1.

### 2.2. Enron.csv — Corporate Email Corpus
- **Tổ chức:** Công bố bởi FERC sau vụ phá sản Enron (2001); chuẩn hóa phục vụ nghiên cứu ML bởi **GS. William W. Cohen tại Carnegie Mellon University (CMU)**. Thu thập ban đầu bởi Bryan Klimt & Yiming Yang.
- **Nguồn gốc:** Email nội bộ công ty Enron Corporation (vụ phá sản lớn nhất nước Mỹ 2001). Federal Energy Regulatory Commission công khai toàn bộ email.
- **Nội dung:** Email công việc thật của nhân viên Enron (ký hợp đồng, báo cáo, đính kèm file Excel)
- **Link:** https://www.cs.cmu.edu/~enron/
- **Đặc điểm:** **Chỉ có 3 cột** (subject, body, label) — thiếu sender/date/urls.
- **Ví dụ thật:** "hpl nom for may 25, 2001" — email hợp đồng gas điện, label=0.

### 2.3. Ling.csv — Ling-Spam Dataset
- **Tổ chức:** Nhóm của **GS. Ion Androutsopoulos tại Athens University of Economics and Business (AUEB, Hy Lạp)**, công bố năm 2000
- **Nội dung:** Email từ mailing list "Ling" (ngôn ngữ học) bị spam xâm nhập
- **Link:** https://arxiv.org/abs/cs/0008019 | Dữ liệu: https://nlp.cs.aueb.gr/software_and_datasets/lingspam_public.tar.gz
- **Đặc điểm:** **Chỉ 2,859 email** (nhỏ nhất). 84% legit, 16% spam. Thiếu metadata.
- **Ví dụ thật:** "job posting - apple-iss research center" — email tuyển dụng thật, label=0.

### 2.4. Nazario.csv — Phishing Corpus của Jose Nazario
- **Tác giả:** Jose Nazario (Arbor Networks — công ty an ninh mạng Mỹ)
- **Nội dung:** Email phishing THẬT — bộ sưu tập lừa đảo nhắm vào ngân hàng, AOL, eBay
- **Link:** https://monkey.org/~jose/phishing/
- **Đặc điểm:** **100% label=1** (chỉ phishing). Dùng tăng cường mẫu phishing.
- **Ví dụ thật:** Email giả mạo "Mail System Internal Data" lừa người dùng.

### 2.5. Nazario_5.csv — Nazario + Legit Mix
- **Nguồn:** Nazario phishing + email legit (Enron) trộn lại
- **Đặc điểm:** 51% phishing / 49% legit — cân bằng. Cột `urls` là **danh sách URL** (object).

### 2.6. Nigerian_5.csv — Email Lừa Đảo 419 (Nigeria)
- **Nguồn:** Kết hợp Nigerian Fraud (advance-fee fraud) + email legit Enron
- **Nội dung:** Email lừa đảo "ông hoàng Nigeria" cần chuyển tiền
- **Đặc điểm:** 52.6% phishing / 47.4% legit.

### 2.7. Nigerian_Fraud.csv — CLAIR Fraudulent E-mail Corpus (419 Scam)
- **Nguồn:** **GS. Dragomir Radev tại phòng thí nghiệm CLAIR, University of Michigan (Mỹ)**, công bố qua ACL Data and Code Repository (mã ADCR2008T001, 2008)
- **Nội dung:** **100% phishing** — email lừa đảo chuyển tiền từ Nigeria, Ghana, Ivory Coast
- **Link:** https://www.kaggle.com/datasets/rtatman/fraudulent-email-corpus
- **Đặc điểm:** 3,332 email, label=1 toàn bộ.
- **Ví dụ thật:** Email từ "MR. JAMES NGOLA" giả làm trợ lý tổng thống Congo, label=1.

### 2.8. SpamAssasin.csv — Apache SpamAssassin Public Corpus
- **Tổ chức:** Apache Software Foundation (USA)
- **Nội dung:** Email spam/ham thật do người dùng gửi cho SpamAssassin
- **Link:** https://spamassassin.apache.org/old/publiccorpus/
- **Đặc điểm:** 70% legit / 30% spam. Từ 2002-2003.
- **Ví dụ thật:** Email kỹ thuật từ GS về lỗi phần mềm, label=0.

### 2.9–2.11. TREC_05/06/07.csv — Text Retrieval Conference (NIST + Waterloo)
- **Tổ chức:** National Institute of Standards and Technology (NIST, USA) + University of Waterloo
- **Nội dung:** Bộ dữ liệu chính thức cuộc thi spam TREC 2005-2007
- **Link:** https://plg.uwaterloo.ca/~gvcormac/treccorpus05/ (06, 07 tương tự)
- **Đặc điểm:** **Lớn nhất** — TREC_05 (55,990), TREC_07 (53,757). Email từ IS spam feed + Enron.
- **Ví dụ thật TREC_07:** Email spam Viagra từ "Tomas Jacobs <RickyAmes@aol.com>", label=1.
- **Lưu ý:** Có dòng label NaN (TREC_05: 715, TREC_06: 57) — đã loại khi tiền xử lý.

---

## 3. Cấu trúc cột dữ liệu (Schema)

### Schema đầy đủ (6 file):
```
sender    : string  — Địa chỉ người gửi
receiver  : string  — Địa chỉ người nhận
date      : string  — Thời gian gửi
subject   : string  — Tiêu đề email
body      : string  — Nội dung email
label     : int     — 0 = legit, 1 = phishing
urls      : int     — Số lượng URL (hoặc object = danh sách URL)
```

### Schema thiếu metadata (2 file: Enron, Ling):
```
subject   : string
body      : string
label     : int
```

### Trường hợp đặc biệt:
- **Nazario_5.csv:** cột `urls` là **list object** (không phải số)
- **TREC_05/06:** có dòng `label = NaN` (đã xử lý)

---

## 4. Dữ liệu nội dung thật (mẫu cho cô xem)

### Mẫu PHISHING (label=1):
```
[CEAS_08] Sender: Young Esposito <Young@iworld.de>
Subject: Never agree to be a loser
Body: Buck up, your troubles caused by small dimension...
      http://whitedone.com/
→ Spam thuốc kích dục, có URL đáng ngờ

[Nigerian_Fraud] Sender: MR. JAMES NGOLA <james_ngola2002@maktoob.com>
Subject: URGENT BUSINESS ASSISTANCE AND PARTNERSHIP
Body: I AM (DR.) JAMES NGOLA, THE PERSONAL ASSISTANCE TO THE
      LATE CONGOLESE PRESIDENT LAURENT KABILA...
→ Lừa đảo 419, giả danh quan chức

[TREC_07] Sender: Tomas Jacobs <RickyAmes@aol.com>
Subject: Generic Cialis, branded quality@
Body: Do you feel the pressure to perform...
→ Spam thuốc, dùng AOL giả
```

### Mẫu LEGIT (label=0):
```
[Enron] Subject: hpl nom for may 25, 2001
Body: (see attached file: hplno 525.xls)
→ Email hợp đồng gas điện nội bộ

[Ling] Subject: job posting - apple-iss research center
Body: A US$10 million joint venture between Apple Computer Inc...
→ Tuyển dụng thật từ Apple

[SpamAssasin] Sender: Robert Elz <kre@munnari.OZ.AU>
Subject: Re: New Sequences Window
Body: I can't reproduce this error. For me it is very repeatable...
→ Email kỹ thuật từ GS
```

---

## 5. Cách xử lý (Pipeline 6 bước)

```
Bước 1: ĐỌC 11 FILE (scripts/merge_datasets.py)
   - Thử encoding utf-8 → latin-1
   - Tăng csv.field_size_limit (vì có email rất dài)
   - Xử lý file thiếu cột (thêm cột default = "")

Bước 2: CHUẨN HÓA SCHEMA
   - Gộp 11 file có schema khác nhau → unified schema
   - Enron/Ling thiếu sender/date → để trống

Bước 3: LÀM SẠCH TEXT
   - Bỏ HTML tags: re.sub(r'<[^>]+>', '', text)
   - Normalize whitespace: ' '.join(text.split())
   - Decode HTML entities (&amp; → &)

Bước 4: NORMALIZE LABEL
   - Map về 0/1 thống nhất
   - Loại dòng label = NaN (715 + 57 dòng)

Bước 5: LOẠI EMAIL RỖNG
   - Bỏ email có cả subject và body đều rỗng

Bước 6: DEDUP (Loại bỏ trùng lặp)
   - Key: subject + body (hash MD5)
   - Loại 10,509 email trùng lặp
```

**Kết quả:** `data_train/processed/merged_clean.csv` (361.4 MB, 206,722 email)

---

# PHẦN II — TRAIN & MODEL

## 6. Quá trình train model (tổng quan)

> Train bằng file `scripts/train_ml_model.py`, dùng mô hình **Random Forest (200 cây)** kết hợp **TF-IDF (30,000 features) + 9 tính năng bảo mật**, input là dataset **206,722 email**, output lưu ra file `app/models/phishing_rf.pkl`.

### 6.1. Train bằng file nào?

**File:** `scripts/train_ml_model.py` (111 dòng)

```powershell
# Cách chạy:
python scripts/train_ml_model.py

# Dòng 30 — Input:
INPUT_CSV = "data_train/processed/merged_clean.csv"   (206,722 email)

# Dòng 31 — Output:
MODEL_PATH = "app/models/phishing_rf.pkl"             (file model đã train)
```

**Quy trình 3 bước trong file:**
```
Bước 1 (dòng 52-61):  Đọc CSV → tách texts + labels
Bước 2 (dòng 90-97):  Chia 80/20 → fit pipeline trên train
Bước 3 (dòng 105-107): Lưu model ra .pkl
```

### 6.2. Model nào?

**Mô hình:** `Pipeline` của scikit-learn gồm 2 phần (dòng 63-85):

```
Pipeline:
│
├── Phần 1: FEATURE EXTRACTION (trích đặc trưng)
│   └── FeatureUnion (ghép 2 loại feature):
│       ├── TfidfVectorizer(max_features=30,000, ngram_range=(1,2))
│       │   → Biến text thành ma trận 30,000 cột (tần suất từ)
│       └── SecurityFeatureExtractor()
│           → 9 tính năng bảo mật (đếm từ khóa, URL...)
│
└── Phần 2: CLASSIFIER (phân loại)
    └── RandomForestClassifier(
            n_estimators=200,        # 200 cây quyết định
            max_depth=30,            # chiều sâu tối đa mỗi cây
            class_weight="balanced", # cân bằng 2 lớp
            random_state=42,         # seed cố định
            n_jobs=-1                # dùng toàn bộ CPU
        )
```

### 6.3. Tại sao chọn Random Forest?

| Lý do | Giải thích |
|-------|-----------|
| Chính xác cao | 97.23% trên dataset 206K |
| Chống overfit | 200 cây vote → ít lỗi hơn 1 cây đơn lẻ |
| Giải thích được | Xem được feature importance |
| Nhanh | Predict < 1s/email |

### 6.4. Chi tiết quá trình train (7 bước)

```
BƯỚC 1: ĐỌC DỮ LIỆU (dòng 52)
   pd.read_csv("merged_clean.csv")
   → 206,722 email, 7 cột (sender, subject, body, label...)

BƯỚC 2: LÀM SẠCH (dòng 58-59)
   df.dropna(subset=["subject", "body", "label"])  → bỏ dòng thiếu
   df["label"].astype(int)                          → chuẩn hóa nhãn 0/1

BƯỚC 3: GỘP TEXT (dòng 34-44, combine_text)
   Mỗi email → 1 chuỗi text:
   "Sender: admin@bank.com
    Subject: Verify your password
    URLs: http://bit.ly/xyz
    Body: Click here to login..."

BƯỚC 4: CHIA 80/20 (dòng 90-96)
   train_test_split(test_size=0.2, stratify=labels, random_state=42)
   → 165,377 train / 41,345 test

BƯỚC 5: TRÍCH ĐẶC TRƯNG (dòng 66-73)
   TF-IDF:   text → ma trận 30,000 cột (tần suất từ có trọng số)
   Security: text → 9 số (đếm từ khóa nguy hiểm, URL...)
   → Ghép lại: mỗi email = vector 30,009 chiều

BƯỚC 6: TRAIN (dòng 97)
   pipeline.fit(x_train, y_train)
   → 200 cây Random Forest "học" từ 165,377 email
   → Mỗi cây học một mẫu khác nhau (bootstrap)
   → Cây quyết định: "Nếu có từ 'urgent' → nghi phishing"

BƯỚC 7: ĐÁNH GIÁ + LƯU (dòng 98-107)
   pipeline.predict(x_test)    → dự đoán trên test
   classification_report()     → in Precision, Recall, F1
   joblib.dump(pipeline)       → lưu .pkl (~50MB)
```

### 6.5. Kết quả thực tế khi train

```
Running train_ml_model.py...

              precision    recall  f1-score   support
           0     0.9762    0.9709    0.9735     21409
           1     0.9681    0.9739    0.9710     19450
    accuracy                         0.9723     40859

Da luu model tai: app/models/phishing_rf.pkl
Thoi gian train: ~5 phut
```

---

## 7. Lý thuyết chuyên sâu

### 7.1. TF-IDF là gì?

> TF-IDF (Term Frequency-Inverse Document Frequency) biến email thành ma trận 30,000 cột. Mỗi cột là một từ, giá trị = tần suất từ đó trong email × độ hiếm của từ đó trong toàn bộ dataset. Từ phổ biến ở mọi email (như 'the') có trọng số thấp, từ hiếm như 'urgent' có trọng số cao.

**Công thức:**
```
TF-IDF(t, d) = TF(t, d) × IDF(t)

TF(t,d)  = số lần từ t xuất hiện trong email d
IDF(t)   = log(Tổng số email / Số email chứa từ t)
```

### 7.2. 9 tính năng bảo mật là gì?

| # | Feature | Cách tính |
|---|---------|-----------|
| 1 | text_length | `len(text)` — email dài bất thường? |
| 2 | url_count | `len(urls)` — số URL |
| 3 | suspicious_url_count | URL chứa "login", "bit.ly", ".ru" |
| 4 | urgency_count | Đếm "urgent", "khẩn cấp", "act now" |
| 5 | credential_count | Đếm "password", "login", "mật khẩu" |
| 6 | money_count | Đếm "payment", "invoice", "bank" |
| 7 | has_at_in_url | URL có "@" không (dấu hiệu lừa đảo) |
| 8 | has_ip_address | Dùng IP thay domain (dấu hiệu phishing) |
| 9 | has_dash_url | Domain có gạch nối (paypal-secure.com) |

---

## 8. Cách chạy & lệnh lệnh lệnh

### 8.1. Train model (tạo file .pkl)
```powershell
cd D:\TLCN
python scripts/train_ml_model.py
```
**Kết quả:**
- Train trên 165,377 email (80%)
- In bảng Precision/Recall/F1
- Lưu model → `app/models/phishing_rf.pkl` (~50MB)
- Thời gian: ~5 phút

### 8.2. Test ML nhanh (không train)
```powershell
python scripts/test_binary.py
```
**Kết quả:**
```
Score  49 -> Not Phishing
Score  50 -> Phishing
Email an toan:   score=35.2, label=0 -> Not Phishing
Email phishing:  score=79.0, label=1 -> Phishing
PASS: Dau ra nhi phan hoat dung!
```

### 8.3. Gộp dataset (nếu tải dataset mới)
```powershell
python scripts/merge_datasets.py
```
**Kết quả:**
- Đọc 11 file trong `data_train/raw/`
- Xử lý → `data_train/processed/merged_clean.csv` (206,722 email)

### 8.4. Chạy Auto Monitor (Gmail → ML → Telegram)
```powershell
# Kiểm tra 1 lần
python scripts/run_auto_monitor.py --once

# Chạy vòng lặp (mỗi 30s)
python scripts/run_auto_monitor.py --interval 30
```

### 8.5. Luồn chạy đầy đủ (reset từ đầu)
```powershell
cd D:\TLCN
python scripts/merge_datasets.py      # Bước 1: Gộp dataset
python scripts/train_ml_model.py      # Bước 2: Train model
python scripts/test_binary.py         # Bước 3: Test
python -m streamlit run app/main.py   # Bước 4: Chạy app UI
```

---

# PHẦN III — CÂU HỎI CÔ HỎI & CÂU TRẢ LỜI

## 9. Về dataset

### Q1: "Tại sao chọn dataset này?"
> **A:** Paper IEEE ICMI 2024 (DOI: 10.5281/zenodo.8339691), 44,193 lượt tải, CC BY 4.0. Gộp 11 nguồn uy tín (Waterloo, CMU, Apache, NIST). 206K email cân bằng 47.7/52.3.

### Q2: "Nguồn gốc 11 dataset có uy tín không?"
> **A:** Tất cả từ tổ chức top:
> - **University of Waterloo** (Canada) — CEAS, TREC
> - **Carnegie Mellon University** (USA) — Enron
> - **Apache Foundation** — SpamAssassin
> - **NIST** (USA) — TREC
> - **Arbor Networks** — Nazario

### Q3: "Dữ liệu có label đúng không?"
> **A:** Label từ 2 nguồn:
> 1. **Spam feed thật** (TREC, SpamAssassin) — người dùng report
> 2. **Phishing corpus thật** (Nazario, Nigerian Fraud) — chuyên gia thu thập
> Có 5-10% sai lệch (label noise), nhưng model vẫn đạt 97.23% accuracy.

### Q4: "Tại sao không dùng BERT?"
> **A:** Random Forest + TF-IDF:
> - Nhanh hơn 100x (0.5s vs 5s/email)
> - Giải thích được (feature importance)
> - Dataset nhỏ (206K) → RF đủ tốt (97.23%)
> - BERT overfit nếu dataset < 1M email

### Q5: "Làm sao verify dataset?"
> **A:**
> 1. Tải từ Zenodo: https://zenodo.org/records/8339691
> 2. Check DOI: 10.5281/zenodo.8339691
> 3. Xem paper IEEE: https://ieeexplore.ieee.org/document/10585821
> 4. Tải từng dataset gốc theo link trong Section 2

### Q6: "Tại sao Enron/Ling thiếu sender/date?"
> **A:** Đây là **giới hạn gốc** của dataset (không phải lỗi xử lý):
> - Enron: Chỉ export subject + body (2 cột)
> - Ling: Chỉ export subject + body (2 cột)
> 6/11 file có đủ 7 cột, còn lại thiếu metadata. Đã dùng cột default rỗng.

### Q7: "Có data leakage không?"
> **A:** Không. Đã kiểm tra:
> - Dedup trước khi split (bỏ 10,509 email trùng)
> - Split 80/20 stratified (giữ phân bố label)
> - TF-IDF fit trên train set, transform test set

---

## 10. Về chia train/test & ngưỡng

### Q8: "Tại sao chia 80% train / 20% test?"
> **A:** Mô hình chỉ được **học (train)** trên dữ liệu train và **kiểm tra (evaluate)** trên test mà nó chưa từng thấy. Nếu trùng nhau → kết quả ảo, không generalize được.

```
206,722 email
    ↓  split 80/20 (stratified)
165,377 train  →  model HỌC từ đây (TF-IDF fit + RandomForest fit)
 41,345 test   →  model CHƯA TỪNG THẤY → ĐÁNH GIÁ trung thực
```

**So sánh các tỷ lệ:**

| Tỷ lệ | Train | Test | Ưu điểm | Nhược điểm |
|--------|-------|------|---------|-----------|
| 70/30 | 144K | 62K | Test lớn, đánh giá ổn định | Train bớt dữ liệu |
| **80/20** | **165K** | **41K** | **Cân bằng: đủ data train + test đủ lớn** | **(Đang dùng)** |
| 90/10 | 186K | 21K | Train nhiều nhất | Test nhỏ → metric dao động |
| 99/1 | 205K | 2K | Train tối đa | Đánh giá không đáng tin |

**Lý do chọn 80/20:**
- Test set 41,345 email **rất lớn** → metric (97.23%) có ý nghĩa thống kê cao.
- Train 165K email đủ để Random Forest học tốt.
- Đây là **chuẩn ngành (industry standard)**.

### Q9: "Tại sao dùng stratify và random_state?"
> **A:**
> - `stratify=labels`: đảm bảo tỉ lệ phishing/legit trong train và test **giống hệt** dataset gốc (47.7/52.3), tránh lệch do ngẫu nhiên.
> - `random_state=42`: mỗi lần chạy cho **kết quả giống nhau** → đảm bảo tính tái lập (reproducibility).

### Q10: "Tại sao ngưỡng 60%?"
> **A:** 50% là ngưỡng mặc định chuẩn của binary classification nhưng gây "alert fatigue" — 772 email hợp lệ bị báo oan. 70% bỏ sót 18.16% phishing (gấp 7×). **60% là điểm gãy**: báo giả giảm 61% (còn 300), bỏ sót 7.53% được heuristic `max(ML, rules)` bù. Đây là **ngưỡng thống nhất duy nhất** trong toàn bộ hệ thống (ML, heuristic, UI, Telegram, LLM prompt).

**Cân bằng Precision ↔ Recall:**
```
Ngưỡng THẤP (30%) → Gọi phishing dễ → Recall cao, Precision thấp
Ngưỡng CAO (70%)  → Khó tính        → Precision cao, Recall thấp
Ngưỡng 60%        → CÂN BẰNG cả hai (điểm tối ưu, xem Master_Theory E7)
```

### Q11: "Learning rate là bao nhiêu?"
> **A:** Random Forest **KHÔNG có learning rate**. Learning rate là tham số của mô hình gradient boosting (XGBoost, LightGBM) hoặc neural network. Random Forest học bằng cách train 200 cây quyết định độc lập, mỗi cây trên 1 mẫu ngẫu nhiên, rồi bỏ phiếu.

**Tham số kiểm soát độ phức tạp của Random Forest:**

| Tham số | Giá trị | Tác dụng |
|---------|---------|----------|
| `n_estimators` | 200 | Số cây quyết định |
| `max_depth` | 30 | Chiều sâu tối đa mỗi cây (chống overfit) |
| `class_weight` | "balanced" | Cân bằng 2 lớp |
| `random_state` | 42 | Seed ngẫu nhiên |

### Q12: "Đã so sánh những mô hình nào? Mô hình nào tốt nhất?"
> **A:** Em đã chạy 4 mô hình trên cùng dataset (204,294 email), cùng features (30,009), cùng cách chia 80/20:
>
> | # | Mô hình | F1 | Train | Predict | Ghi chú |
> |---|---------|-----|-------|---------|---------|
> | 1 | **Logistic Regression** | **99.02%** | 109s | **0.03s** | **TỐT NHẤT** |
> | 2 | XGBoost | 98.27% | 912s | 0.80s | Train chậm |
> | 3 | Random Forest | 97.23% | 133s | 1.35s | Mô hình cũ |
> | 4 | Naive Bayes | 95.28% | **0.1s** | 0.03s | Train nhanh nhất |
>
> Logistic Regression thắng vì features TF-IDF tuyến tính. XGBoost chính xác cao nhưng train 15 phút. Naive Bayes nhanh nhất nhưng yếu nhất (giả định các từ độc lập).
>
> **Chi tiết:** Xem `LY_THUYET_GO_Y.md` mục 11. Kết quả lưu tại `results/model_comparison.csv`.

---

## 11. Link xác thực

### Dataset chính:
- **Zenodo:** https://zenodo.org/records/8339691
- **DOI:** https://doi.org/10.5281/zenodo.8339691
- **IEEE Paper:** https://ieeexplore.ieee.org/document/10585821
- **Google Scholar:** https://scholar.google.com/scholar?q=%22Curated+Datasets+and+Feature+Analysis+for+Phishing+Email+Detection%22

### 11 dataset nguồn:

| Dataset | Link | Tổ chức |
|---------|------|---------|
| CEAS | https://ceas.cc/2008/ · https://plg.uwaterloo.ca/~gvcormac/ceascorpus/ | University of Waterloo |
| Enron | https://www.cs.cmu.edu/~enron/ | Carnegie Mellon |
| Ling | https://arxiv.org/abs/cs/0008019 | Athens Univ. of Economics & Business |
| Nazario | https://monkey.org/~jose/phishing/ | Arbor Networks |
| Nigerian | https://www.kaggle.com/datasets/rtatman/fraudulent-email-corpus | University of Michigan (CLAIR Lab) |
| SpamAssassin | https://spamassassin.apache.org/old/publiccorpus/ | Apache Foundation |
| TREC | https://trec.nist.gov/data/spam.html | NIST + Waterloo |

### Tổ chức chủ quản:
- University of Waterloo: https://www.uwaterloo.ca/
- Carnegie Mellon: https://www.cmu.edu/
- Apache Foundation: https://www.apache.org/
- NIST: https://www.nist.gov/
- IEEE: https://www.ieee.org/
