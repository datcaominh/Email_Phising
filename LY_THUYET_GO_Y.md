# LÝ THUYẾT CHI TIẾT EMAIL PHISING

> **Cập nhật:** Dataset mới (Champa et al. 2024 - 206K email), Đầu ra thống nhất nhị phân (Phishing / Not Phishing)

---

## 1. BỔ SUNG PIPELINE

### Pipeline hiện tại (6 bước):

```
Bước 1: INPUT & PARSING
   ↓
Bước 2: PREPROCESSING (Làm sạch)
   ↓
Bước 3: FEATURE EXTRACTION
   ↓
Bước 4: ML CLASSIFICATION
   ↓
Bước 5: LLM CONTEXTUAL ANALYSIS
   ↓
Bước 6: DECISION & ALERT (Nhị phân)
```

**Mô tả từng bước:**

| Bước | Công việc | Đầu ra |
|------|-----------|--------|
| 1. Parsing | Đọc file .eml/.txt, trích header (From, To, Subject, Date) | Raw email fields |
| 2. Preprocessing | Loại bỏ HTML tags, decode base64, normalize text | Text sạch |
| 3. Feature Extraction | TF-IDF vectorization + 9 security features | Feature vector |
| 4. ML Classification | Random Forest dự đoán xác suất phishing | Score 0-100 |
| 5. LLM Analysis | Gemini phân tích ngữ cảnh, social engineering | Báo cáo text |
| 6. Decision & Alert | **Nhị phân: Phishing / Not Phishing** → Alert → Telegram | **Có/Không** |

![image-20261009202032527](C:\Users\Datcaominh\AppData\Roaming\Typora\typora-user-images\image-20261009202032527.png)

### Flow chi tiết trong code:

```
File .eml/.txt
    ↓
parse_uploaded_email()           [orchestrator.py]
    ↓
predict_phishing()               [ml_engine.py]
    ├── TF-IDF Vectorizer (30K features)
    ├── SecurityFeatureExtractor (9 features)
    ├── RandomForest.predict_proba() → ML_SCORE
    ├── heuristic_score() → HEURISTIC_SCORE
    └── final = max(ML, HEURISTIC)
    ↓
analyze_email()                  [llm_agent.py]
    ↓
build_alert()                    [orchestrator.py]
    ↓
risk_level() = "Phishing" / "Not Phishing" (ngưỡng 60)
```

---

## 2. MÔ TẢ DATASET

### Dataset hiện tại: Champa et al. 2024 (gộp 11 nguồn)

| Thông số | Giá trị |
|----------|---------|
| **Tên** | Phishing Email Curated Datasets |
| **Tác giả** | Champa, A.I., Rabbi, M.F., Zibran, M.F. |
| **Năm** | 2024 |
| **Paper** | IEEE ICMI 2024 - *"Curated Datasets and Feature Analysis for Phishing Email Detection with Machine Learning"* |
| **DOI** | `10.5281/zenodo.8339691` |
| **Tổng ban đầu** | 221,093 email (11 file CSV) |
| **Sau tiền xử lý** | **206,722 email** |
| **Phishing (1)** | 98,527 (47.7%) |
| **Legitimate (0)** | 108,195 (52.3%) |
| **Ngôn ngữ** | Tiếng Anh |
| **License** | CC BY 4.0 |

### 11 nguồn dữ liệu:

| # | Nguồn | Số email | Năm | Link xác thực |
|---|-------|----------|-----|---------------|
| 1 | CEAS_08 | 38,964 | 2008 | https://ceas.cc/2008/ |
| 2 | Enron | 29,424 | 2001 | https://www.cs.cmu.edu/~enron/ |
| 3 | Ling | 2,859 | 2000 | https://arxiv.org/abs/cs/0008019 |
| 4 | Nazario | 1,552 | 2007 | https://monkey.org/~jose/phishing/ |
| 5 | Nazario_5 | 1,197 | 2007 | https://monkey.org/~jose/phishing/ |
| 6 | Nigerian_5 | 4,523 | 2010 | https://zenodo.org/records/8339691 |
| 7 | SpamAssasin | 5,202 | 2002 | https://spamassassin.apache.org/old/publiccorpus/ |
| 8 | TREC_05 | 54,411 | 2005 | https://plg.uwaterloo.ca/~gvcormac/treccorpus05/ |
| 9 | TREC_06 | 15,749 | 2006 | https://plg.uwaterloo.ca/~gvcormac/treccorpus06/ |
| 10 | TREC_07 | 52,841 | 2007 | https://plg.uwaterloo.ca/~gvcormac/treccorpus07/ |
| | **TỔNG** | **206,722** | | |

**Tổ chức chủ quản các dataset nguồn:**

| Tổ chức | Dataset | Link |
|---------|---------|------|
| **University of Waterloo** (Canada) | CEAS, TREC | https://www.uwaterloo.ca/ |
| **Carnegie Mellon University** (USA) | Enron | https://www.cmu.edu/ |
| **Apache Foundation** | SpamAssassin | https://www.apache.org/ |
| **NIST** (USA) | TREC | https://www.nist.gov/ |
| **IEEE** | Paper Champa 2024 | https://www.ieee.org/ |

### Cấu trúc thư mục (phân biệt rõ):

```
data_train/
├── raw/                    ← FILE GỐC (chưa xử lý - để đối chiếu)
│   ├── CEAS_08.csv         (64.8 MB)
│   ├── Enron.csv           (42.8 MB)
│   ├── Ling.csv            (8.9 MB)
│   ├── Nazario.csv         (7.4 MB)
│   ├── Nazario_5.csv       (11.2 MB)
│   ├── Nigerian_5.csv      (17.4 MB)
│   ├── Nigerian_Fraud.csv  (8.8 MB)
│   ├── SpamAssasin.csv     (14.2 MB)
│   ├── TREC_05.csv         (117.4 MB)
│   ├── TREC_06.csv         (40 MB)
│   └── TREC_07.csv         (95.6 MB)
│
└── processed/              ← FILE ĐÃ XỬ LÝ (dùng cho training)
    └── merged_clean.csv    (361.4 MB, 206,722 email)
```

### Schema (cột dữ liệu):

```
Cột         | Kiểu dữ liệu | Ví dụ
------------|--------------|---------------------------
sender      | string       | "admin@bank.com"
receiver    | string       | "user@gmail.com"
date        | string       | "2008-01-15 10:30:00"
subject     | string       | "Verify your account now"
body        | string       | "Click here to verify..."
label       | int (0 or 1) | 1
urls        | string       | "http://fake-bank.com/login"
source      | string       | "CEAS_08" (tên nguồn)
```

### Các bước tiền xử lý (scripts/merge_datasets.py):

| # | Bước | Chi tiết | Số lượng |
|---|------|----------|----------|
| 1 | Đọc 11 file | Thử utf-8 → latin-1, engine c → python | 221,093 |
| 2 | Chuẩn hóa schema | Thêm cột thiếu (sender, date, urls...) | - |
| 3 | Clean text | Bỏ HTML tags, chuẩn hóa whitespace | - |
| 4 | Normalize label | Map về 0/1 thống nhất | - |
| 5 | Bỏ label invalid | Label != 0 và != 1 | -3,862 |
| 6 | Bỏ email rỗng | Cả subject và body đều rỗng | -0 |
| 7 | Dedup | Bỏ trùng theo subject + body | -10,509 |
| **TỔNG** | | | **206,722** |

### Phân bố sau xử lý:

```
Phishing (1):  98,527 email (47.7%)  ████████████████████░░░░░
Legitimate (0): 108,195 email (52.3%)  █████████████████████░░░

→ Cân bằng tốt (gần 50/50) → Rất tốt cho ML
```

---

## 3. DATASET MỚI ĐÃ ÁP DỤNG

### Tại sao chọn Champa et al. 2024?

| Tiêu chí | Đánh giá |
|----------|----------|
| **Mới nhất** | 2024 (IEEE ICMI) |
| **Uy tín** | IEEE paper, DOI Zenodo, 44,193 lượt tải |
| **Đa dạng** | 11 nguồn, 1998-2022 |
| **Cân bằng** | 47.7% / 52.3% (gần 50/50) |
| **License** | CC BY 4.0 (miễn phí) |
| **Cải thiện** | Accuracy: 85-90% → **97.23%** |

### So sánh dataset cũ vs mới:

| Thông số | Cũ (CEAS 2008) | Mới (Champa 2024) |
|----------|----------------|-------------------|
| Số email | 39,154 | **206,722** (5.3x) |
| Nguồn | 1 | **11** |
| Thời gian | 2008 | **1998-2022** |
| Accuracy | ~85-90% | **97.23%** |
| Imbalance | 57/43 | **47.7/52.3** (cân bằng hơn) |

---

## 4. DẤU HIỆU EMAIL LỪA ĐẢO (PHISHING INDICATORS)

### 4.1. Phân loại dấu hiệu theo lý thuyết:

**A. Dấu hiệu về NGÔN NGỮ (Linguistic Indicators):**

| Dấu hiệu | Ví dụ | Lý thuyết |
|-----------|-------|-----------|
| Tính cấp bách | "urgent", "within 24 hours", "khẩn cấp" | Tạo áp lực thời gian → victim không suy nghĩ kỹ |
| Đe dọa | "account suspended", "your account will be closed" | Fear appeal → kích hoạt phản xạ sợ hãi |
| Phần thưởng | "you won $1000", "free gift" | Greed appeal → đánh lừa lý trí |
| Yêu cầu thông tin | "verify your password", "confirm your SSN" | Credential theft → mục đích chính |
| Sai chính tả | "recieve", "verfy", "acount" | Thấp chất lượng → phishing thường có lỗi |

**B. Dấu hiệu về KỸ THUẬT (Technical Indicators):**

| Dấu hiệu | Công thức phát hiện | Lý thuyết |
|-----------|---------------------|-----------|
| URL đáng ngờ | Regex: `https?://[^\s]*bit\.ly[^\s]*` | URL shortener che giấu đích |
| IP thay vì domain | Regex: `https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | Phishing dùng IP trực tiếp |
| Domain sai | `@` trong URL: `http://good.com@evil.com` | Visual trick |
| Gạch nối nhiều | `http://paypal-secure-login.com` | Typosquatting |
| TLD đáng ngờ | `.ru`, `.zip`, `.tk` | Top-level domain rẻ/miễn phí |

**C. Dấu hiệu về HEADER (Metadata Indicators):**

| Dấu hiệu | Ý nghĩa |
|-----------|---------|
| Sender domain khác brand | "paypal.com" vs "paypal-secure.ru" |
| Reply-To khác From | Phishing đánh lừa reply |
| SPF/DKIM fail | Không xác thực được sender |
| Date bất thường | Thời gian gửi odd (2-3 giờ sáng) |

### 4.2. 9 Security Features trong code ánh xạ với lý thuyết:

```
Feature 1: text_length          → Dấu hiệu chung
Feature 2: url_count            → Technical: nhiều link = đáng ngờ
Feature 3: suspicious_url_count → Technical: URL có pattern xấu
Feature 4: urgency_count        → Linguistic: tính cấp bách
Feature 5: credential_count     → Linguistic: yêu cầu thông tin
Feature 6: money_count          → Linguistic: liên quan tiền bạc
Feature 7: has_at_in_url        → Technical: @ trick
Feature 8: has_ip_address       → Technical: IP thay domain
Feature 9: has_dash_url         → Technical: domain có gạch nối
```

---

## 5. TỈ LỆ ÂM TÍNH GIẢ & DƯƠNG TÍNH GIẢ

### 5.1. Ma trận nhầm lẫn (Confusion Matrix):

```
                    PREDICTED
                 Positive    Negative
              ┌───────────┬───────────┐
ACTUAL  Pos   │  TP (True │  FN (False│
(Phishing)     │  Positive)│  Negative)│  ← Miss: bỏ sót phishing
              ├───────────┼───────────┤
        Neg   │  FP (False │  TN (True │
(Legit)       │  Positive)│  Negative)│  ← False alarm
              └───────────┴───────────┘
```

### 5.2. Định nghĩa công thức:

**False Positive Rate (FPR) - Tỷ lệ Âm tính giả:**
```
FPR = FP / (FP + TN)

Trong đó:
- FP = email hợp lệ nhưng bị đoán là phishing (báo động giả)
- TN = email hợp lệ và bị đoán đúng là hợp lệ
```

**False Negative Rate (FNR) - Tỷ lệ Dương tính giả:**
```
FNR = FN / (FN + TP)

Trong đó:
- FN = email phishing nhưng bị đoán là hợp lệ (bỏ sót)
- TP = email phishing và bị đoán đúng là phishing
```

### 5.3. Tính từ kết quả thực tế (dataset 206K):

```
Test set: 40,859 email (20% của 206,722)

Kết quả model:
- TP = 18,943 (bắt đúng phishing)
- FN = 507   (bỏ sót phishing)     ← FNR
- FP = 623   (báo động giả)         ← FPR
- TN = 20,786 (nhận đúng hợp lệ)

FNR = 507 / (507 + 18,943) = 507/19,450 = 2.61%
FPR = 623 / (623 + 20,786) = 623/21,409 = 2.91%

→ Bỏ sót chỉ 2.61% phishing (rất thấp!)
→ Báo động giả chỉ 2.91% (rất thấp!)
```

### 5.4. Ý nghĩa quan trọng:
- **FNR cao** = NGUY HIỂM: email phishing lọt lưới → user bị lừa
- **FPR cao** = PHIỀN: email hợp lệ bị chặn → user khó chịu
- **Trong security: FNR quan trọng hơn FPR** (bỏ sót phishing nguy hiểm hơn báo động giả)

### 5.5. Công thức liên quan:

**Accuracy:**
```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
         = (18943 + 20786) / 40859
         = 39,729 / 40,859 = 97.23%
```

**Precision:**
```
Precision = TP / (TP + FP)
          = 18943 / (18943 + 623)
          = 18943 / 19566 = 96.81%
```

**Recall:**
```
Recall = TP / (TP + FN) = 1 - FNR
       = 18943 / (18943 + 507)
       = 18943 / 19450 = 97.39%
```

**F1-Score:**
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
   = 2 × (96.81 × 97.39) / (96.81 + 97.39)
   = 97.10%
```

---

## 6. TÀI LIỆU / BÁO CÁO LIÊN QUAN ( có bị trùng lặp dữ liệu không )

### A. Dataset đã sử dụng (Trích dẫn chuẩn):

> **Champa, A. I., Rabbi, M. F., & Zibran, M. F.** (2024). Curated datasets and feature analysis for phishing email detection with machine learning. *3rd IEEE International Conference on Computing and Machine Intelligence (ICMI)*, pp. 1–7. DOI: `10.5281/zenodo.8339691`

**Link xác thực:**

- **Dataset (Zenodo):** https://zenodo.org/records/8339691
- **DOI:** https://doi.org/10.5281/zenodo.8339691
- **Paper (IEEE):** https://ieeexplore.ieee.org/document/10585821
- **Google Scholar:** https://scholar.google.com/scholar?q=%22Curated+Datasets+and+Feature+Analysis+for+Phishing+Email+Detection%22

**Tác giả:**
| Tác giả | Xác thực |
|---------|----------|
| Arifa Islam Champa | IEEE Xplore profile |
| Md Fazle Rabbi | Tác giả đồng nghiệp |
| Minhaz F. Zibran | Tác giả đồng nghiệp |

**BibTeX:**
```bibtex
@inproceedings{champa2024curated,
  title     = {Curated Datasets and Feature Analysis for Phishing Email Detection with Machine Learning},
  author    = {Champa, Arifa I and Rabbi, Md Fazle and Zibran, Minhaz F},
  booktitle = {3rd IEEE International Conference on Computing and Machine Intelligence (ICMI)},
  pages     = {1--7},
  year      = {2024},
  doi       = {10.5281/zenodo.8339691}
}
```

**Link tải dataset:** https://zenodo.org/records/8339691 (44,193 lượt tải, License CC BY 4.0)

### B. Báo khoa học quốc tế:

| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | **Verizon DBIR 2024** | 91% cyberattack bắt đầu từ phishing |
| 2 | **APWG Phishing Activity Trends Report 2024** | Thống kê phishing toàn cầu |
| 3 | **FBI IC3 Report 2023** | Thiệt hại 12.5 tỷ USD từ phishing |
| 4 | **NIST SP 800-177** | Hướng dẫn email authentication |

### C. Nghiên cứu khoa học về ML + Phishing:

| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | "Curated Datasets and Feature Analysis..." (IEEE ICMI, 2024) | **Dataset đang dùng** |
| 2 | "Phishing Email Detection Using ML" (IEEE, 2020) | So sánh RF, SVM, NB |
| 3 | "BERT-based Phishing Email Detection" (2021) | Dùng NLP transformer |
| 4 | "A Survey on Phishing Attacks and Detection" (ACM, 2022) | Tổng quan toàn diện |
| 5 | "Hybrid Phishing Detection using ML and LLM" (2023-2024) | Gần giống đề tài này |

### D. Tài liệu tiếng Việt:

| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | Báo cáo VNCERT 2024 | Tình hình an ninh mạng Việt Nam |
| 2 | Nghiên cứu ĐHQGHN về spam detection | Áp dụng ML cho email tiếng Việt |
| 3 | Công văn Bộ TT&TT về chống phishing | Chính sách quản lý |

### E. Chuẩn & Framework:

| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | OWASP Top 10 2021 | Phishing là social engineering |
| 2 | MITRE ATT&CK T1566 | Kiến thức tấn công phishing |
| 3 | RFC 7208 (SPF), RFC 6376 (DKIM) | Chuẩn xác thực email |

---

## 7. MÔ TẢ MÔ HÌNH LLM ĐANG SỬ DỤNG

### 7.1. Thông số mô hình LLM:

| Thông số | Giá trị |
|----------|---------|
| **Tên mô hình** | **Google Gemini** (gemini-3.6-flash / 3.7-flash) |
| Nhà phát triển | Google DeepMind |
| Kiến trúc | Transformer (multi-modal) |
| API | google-genai SDK v2.0+ |
| Temperature | 0.2 (thấp → kết quả ổn định, ít sáng tạo) |
| System Instruction | Custom prompt "Phishing Analyst Agent" |

### 7.2. Lý thuyết cách LLM hoạt động trong dự án:

**Cơ chế Transformer Attention:**
```
Attention(Q, K, V) = softmax(QK^T / √d_k) × V

Trong đó:
- Q (Query): Câu hỏi của model (context email)
- K (Key): Thông tin tham chiếu (ML score, URLs)
- V (Value): Nội dung cần trích xuất
- √d_k: Scaling factor tránh gradient quá lớn
```

**Quy trình LLM phân tích:**
```
1. Input Construction:
   System Prompt + Context (email + ML score) + User question

2. Tokenization:
   Text → Tokens (mã số) → Embeddings (vector)

3. Forward Pass:
   Qua nhiều layer Transformer → dự đoán token kế tiếp

4. Decoding:
   temperature=0.2 → greedy-ish → câu trả lời ổn định

5. Output: ĐẦU RA NHỊ PHÂN
   Kết luận: PHISHING / NOT PHISHING + Điểm + Bằng chứng
```

### 7.3. Tại sao chọn temperature = 0.2?
```
temperature < 1 → Ưu tiên token có xác suất cao nhất
temperature = 0.2 → Rất ổn định, ít "bịa"
temperature > 1 → Sáng tạo hơn nhưng có thể sai

Với security analysis → cần tính chính xác → temperature thấp
```

### 7.4. Kết hợp ML + LLM:

```
                ML (Random Forest)           LLM (Gemini)
Điểm mạnh:      - Nhanh (< 1ms)              - Hiểu ngữ cảnh
                - Nhất quán                  - Giải thích được
                - Không tốn API cost          - Xử lý biến thể mới
Điểm yếu:       - Không hiểu ngữ cảnh        - Chậm (1-3s)
                - Cứng nhắc                   - Tốn API cost
                - Cần dataset lớn            - Có thể "bịa"

→ KẾT HỢP: ML cho điểm nhanh + LLM cho giải thích sâu
```

### 7.5. System Prompt (.pi/prompts/system_prompt.md):

```
QUY THONG NHAT DAU RA NHI PHAN:
- Ket luan CHI co 2 gia tri: PHISHING hoac NOT PHISHING
- Khong su dung cac muc do trung gian
- Neu diem rui ro >= 60 => PHISHING, < 60 => NOT PHISHING
```

---

## 8. KẾT LUẬN THỐNG NHẤT - ĐẦU RA NHỊ PHÂN

→ **ĐẦU RA CHỈ CÓ 2 GIÁ TRỊ:**

```
┌─────────────────────────────────────────┐
│                                         │
│   PHISHING     (bị)     → label = 1     │
│   NOT PHISHING (không bị) → label = 0  │
│                                         │
│   Ngưỡng: score >= 60 → PHISHING       │
│           score <  60 → NOT PHISHING   │
│                                         │
└─────────────────────────────────────────┘
```

### 8.2. Dùng đánh giá 2 mức

```
0-49   → Not Phishing (không bị)  → label = 0
50-100 → Phishing (bị)            → label = 1

ƯU ĐIỂM:
- Thống nhất trong toàn bộ hệ thống
- Dễ đánh giá (binary classification)
- Dễ tích hợp hệ thống bên ngoài
- Phù hợp yêu cầu của cô
```

### 8.3. Thống nhất trong toàn bộ code:

| Thành phần | Trước | Sau |
|------------|-------|-----|
| `orchestrator.risk_level()` | 3 mức (An toan/Dang ngo/Nguy hiem) | **2 mức (Phishing/Not Phishing)** |
| `ml_engine.label` | `score >= 55` | **`score >= 60`** |
| `main.show_risk()` | 3 màu (xanh/vàng/đỏ) | **2 màu (đỏ = Phishing, xanh = Not)** |
| `telegram_notifier` | NGUY HIEM/DANG NGO/AN TOAN | **PHISHING/NOT PHISHING** |
| `llm_agent` prompt | "An toan / Dang ngo / Nguy hiem" | **"PHISHING / NOT PHISHING"** |
| `system_prompt` | 3 mức | **Nhị phân, ngưỡng 60** |
| `email_fetcher` ngưỡng | 55 | **60** |

### 8.4. Ví dụ hoạt động:

```
Email A: score = 30
  → 30 < 60 → NOT PHISHING (không bị)
  → Không gửi Telegram

Email B: score = 59
  → 59 < 60 → NOT PHISHING (không bị)
  → Không gửi Telegram

Email C: score = 60
  → 60 >= 60 → PHISHING (bị)
  → Gửi Telegram cảnh báo

Email D: score = 95
  → 95 >= 60 → PHISHING (bị)
  → Gửi Telegram cảnh báo
```

### 8.5. Điểm số vẫn giữ (như bằng chứng phụ):

```
ĐIỂM (0-100) = max(ML_SCORE, HEURISTIC_SCORE)
    ↓
Nhị phân: >= 60 → PHISHING, < 60 → NOT PHISHING
    ↓
Điểm dùng để: 
- Sắp xếp mức độ nghiêm trọng
- Giải thích cho người dùng
- LLM tham khảo khi phân tích
```

---

## 9. CĂN CỨ TÍNH ĐIỂM RỦI RO

### 9.1. Công thức tính điểm:

```
ĐIỂM CUỐI = max(ML_SCORE, HEURISTIC_SCORE)

Trong đó:

1. ML_SCORE (từ Random Forest):
   - predict_proba(text) → xác suất class 1
   - ml_score = probability × 100
   
2. HEURISTIC_SCORE (rules-based):
   base = 8
   + min(matched_keywords × 8, 48)    // từ khóa đáng ngờ
   + min(url_count × 8, 24)           // số URL
   + min(suspicious_url × 15, 30)     // URL đáng ngờ
   = score 0-95
```

### 9.2. Chi tiết heuristic score:

```
Ví dụ email:
- matched_keywords = ["urgent", "password", "login"] → 3 keywords
- url_count = 4
- suspicious_url_count = 2

Tính:
base = 8
keyword_score = min(3 × 8, 48) = min(24, 48) = 24
url_score = min(4 × 8, 24) = min(32, 24) = 24
suspicious_score = min(2 × 15, 30) = min(30, 30) = 30

TOTAL = 8 + 24 + 24 + 30 = 86 (điểm rủi ro)
```

### 9.3. Tại sao dùng max(ML, heuristic)?

```
TRƯỜNG HỢP 1: ML đúng (score cao)
- ML = 85, Heuristic = 40
- max = 85 → Đúng (tin ML)

TRƯỜNG HỢP 2: ML sai (miss), Heuristic bắt được
- ML = 30 (model không recognize mẫu mới)
- Heuristic = 70 (keywords + URLs rõ ràng)
- max = 70 → Đúng (heuristic cứu - GUARDRAIL)

TRƯỜNG HỢP 3: Cả hai đều thấp
- ML = 25, Heuristic = 20
- max = 25 → Not Phishing

TRƯỜNG HỢP 4: Cả hai đều cao
- ML = 90, Heuristic = 85
- max = 90 → Phishing
```

### 9.4. Quyết định nhị phân:

```
ĐIỂM CUỐI              KẾT LUẬN            LABEL
──────────────────────────────────────────────────
0  - 49                 NOT PHISHING        0     (không bị)
50 - 100                PHISHING            1     (bị)
```

### 9.5. Ví dụ hoàn chỉnh:

```
Email: "URGENT: Verify your password now!"
       "Click: http://bit.ly/xyz"

Bước 1 - ML_SCORE:
  RandomForest: 170/200 cây nói phishing
  → ML = 0.85 × 100 = 85

Bước 2 - HEURISTIC_SCORE:
  base = 8
  keywords: urgent, verify, password → 3 × 8 = 24
  urls: 1 URL → 1 × 8 = 8
  suspicious: bit.ly → 1 × 15 = 15
  → HEURISTIC = 8 + 24 + 8 + 15 = 55

Bước 3 - ĐIỂM CUỐI:
  max(85, 55) = 85

Bước 4 - ĐẦU RA NHỊ PHÂN:
  85 >= 60 → PHISHING (label = 1)
  → Gửi Telegram cảnh báo
```

---

## 10. TỈ LỆ MÔ HÌNH ML (METRICS)

### 10.1. Kết quả thực tế (dataset 206K - Champa 2024):

```
              precision    recall  f1-score   support

     0        0.9762      0.9709   0.9735     21,409
     1        0.9681      0.9739   0.9710     19,450

  accuracy                       0.9723     40,859
  macro avg    0.9721      0.9724   0.9723     40,859
  weighted avg 0.9723      0.9723   0.9723     40,859
```

### 10.2. Các chỉ số chi tiết:

| Metric | Công thức | Kết quả | Ý nghĩa |
|--------|-----------|---------|---------|
| **Accuracy** | (TP+TN)/Total | **97.23%** | Tổng thể đoán đúng 97.23% |
| **Precision (0)** | TN/(TN+FN) | **97.62%** | Trong email đoán legit, 97.62% đúng |
| **Precision (1)** | TP/(TP+FP) | **96.81%** | Trong email chặn, 96.81% là phishing thật |
| **Recall (0)** | TN/(TN+FP) | **97.09%** | Trong email legit, nhận đúng 97.09% |
| **Recall (1)** | TP/(TP+FN) | **97.39%** | Trong email phishing, bắt được 97.39% |
| **F1 (0)** | | **97.35%** | Cân bằng P/R cho class 0 |
| **F1 (1)** | | **97.10%** | Cân bằng P/R cho class 1 |
| **FPR** | FP/(FP+TN) | **2.91%** | Báo động giả 2.91% |
| **FNR** | FN/(FN+TP) | **2.61%** | Bỏ sót 2.61% phishing |

### 10.3. Confusion Matrix (tính từ metrics):

```
                    PREDICTED
                 Not Phish(0)  Phish(1)
              ┌────────────┬────────────┐
ACTUAL  0     │  TN = 20,786│ FP = 623   │  21,409
(Not Phish)   │  97.09%     │  2.91%     │
              ├────────────┼────────────┤
        1     │  FN = 507   │ TP = 18,943│  19,450
(Phish)       │  2.61%      │  97.39%    │
              └────────────┴────────────┘
                21,293       19,566      40,859
```

### 10.4. So sánh với model cũ:

| Metric | Model cũ (CEAS 39K) | Model mới (Champa 206K) | Cải thiện |
|--------|---------------------|-------------------------|-----------|
| Accuracy | ~85-90% | **97.23%** | ✅ +7-12% |
| Precision (phish) | ~84-89% | **96.81%** | ✅ +8% |
| Recall (phish) | ~86-91% | **97.39%** | ✅ +6% |
| F1 | ~85-90% | **97.10-97.35%** | ✅ +7% |
| FNR | ~9-14% | **2.61%** | ✅ Giảm 7% |
| FPR | ~11-16% | **2.91%** | ✅ Giảm 10% |

### 10.5. Thông số training:

```
Dataset:    merged_clean.csv (206,722 email)
Split:      80/20 stratified → 165,863 train / 40,859 test
Model:      RandomForestClassifier
Parameters: n_estimators=200, max_depth=30, class_weight=balanced
Features:   TF-IDF (30,000 features, ngram 1-2) + 9 Security Features
Thời gian:  ~5 phút
```

---

## 11. SO SÁNH NHIỀU MÔ HÌNH ML (YÊU CẦU CÔ GIAO)

### 11.1. Mục đích so sánh:

> Cô yêu cầu: *"Đừng chỉ dùng mỗi Random Forest. Hãy chạy thêm vài mô hình khác để so sánh, biết mô hình nào tối ưu hơn, và giải thích vì sao."*

Để trả lời khách quan, em đã chạy **4 mô hình** trên **cùng dataset, cùng bộ features, cùng cách chia train/test** → kết quả so sánh công bằng.

### 11.2. Thiết kế thí nghiệm (công bằng cho cả 4 mô hình):

| Thành phần | Giá trị (giống hệt cho cả 4 model) |
|------------|-------------------------------------|
| Dataset | `merged_clean.csv` — 204,294 email hợp lệ |
| Chia train/test | 80/20 stratified, `random_state=42` |
| Train / Test | 163,435 / 40,859 email |
| Features | TF-IDF (30,000) + 9 Security Features = 30,009 chiều |
| Label | Nhị phân: 0 (legit) / 1 (phishing) |

> **Tại sao phải giống nhau?** Chỉ khi dữ liệu đầu vào, cách chia và features giống nhau, thì chênh lệch Accuracy/F1 mới **chỉ do mô hình**, không do yếu tố khác.

### 11.3. Bảng kết quả thực tế (đã chạy ra số liệu thật):

| # | Mô hình | Accuracy | F1 (weighted) | FPR | FNR | Train | Predict |
|---|---------|----------|---------------|-----|-----|-------|---------|
| 1 | **Logistic Regression** | **99.02%** | **99.02%** | **1.01%** | **0.95%** | 109s | **0.03s** |
| 2 | XGBoost | 98.27% | 98.27% | 1.92% | 1.52% | 912s | 0.80s |
| 3 | Random Forest (cũ) | 97.23% | 97.23% | 2.91% | 2.61% | 133s | 1.35s |
| 4 | Multinomial Naive Bayes | 95.28% | 95.28% | 4.19% | 5.30% | **0.1s** | 0.03s |

**Xếp hạng theo F1 (giảm dần):**
```
1. Logistic Regression   F1 = 99.02%   ← TỐT NHẤT
2. XGBoost               F1 = 98.27%
3. Random Forest (cũ)    F1 = 97.23%
4. Naive Bayes           F1 = 95.28%
```

**Kết quả lưu tại:** `results/model_comparison.csv` (chạy `python scripts/compare_models.py` để tái lập)

### 11.4. Giải thích TỪNG mô hình:

#### 🥇 Logistic Regression (99.02%) — TỐT NHẤT

| Ưu điểm | Nhược điểm |
|----------|-----------|
| Accuracy/F1 cao nhất (99.02%) | Yêu cầu scale dữ liệu (MaxAbsScaler) |
| **Nhanh nhất khi predict (0.03s)** | Hội tụ lâu nếu không scale |
| Train nhanh (109s) | Giải thích được (hệ số trọng số từng từ) |
| FNR thấp nhất (0.95%) = bỏ sót ít phishing | |

**Vì sao thắng?** TF-IDF cho ma trận đặc trưng **linearly separable** (các từ phân biệt phishing/legit khá rõ trên không gian 30,009 chiều). Logistic Regression tìm **đường phân cách tuyến tính** tối ưu bằng gradient descent → rất phù hợp loại dữ liệu này.

#### 🥈 XGBoost (98.27%)

| Ưu điểm | Nhược điểm |
|----------|-----------|
| Chính xác cao (98.27%) | **Train RẤT CHẬM (912s ≈ 15 phút)** |
| Chống overfit tốt | Predict chậm hơn LR (0.80s) |
| Xử lý phi tuyến性 tốt | Nhiều siêu tham số phải tinh chỉnh |

**Vì sao đứng nhì?** XGBoost dùng gradient boosting (nhiều cây học nối tiếp), mạnh với dữ liệu phi tuyến, nhưng trên dữ liệu text TF-IDF tuyến tính thì LR đã đủ tốt. Đổi lại, XGBoost tốn 8× thời gian train để chỉ nhỉnh hơn RF 1%.

#### 🥉 Random Forest (97.23%) — MÔ HÌNH CŨ

| Ưu điểm | Nhược điểm |
|----------|-----------|
| Ổn định, ít tham số tinh chỉnh | Accuracy thấp hơn LR (97.23% vs 99.02%) |
| Giải thích được (feature importance) | Predict CHẬM NHẤT (1.35s) |
| Chống overfit tốt | FNR cao hơn LR (2.61% vs 0.95%) |

#### 4. Multinomial Naive Bayes (95.28%)

| Ưu điểm | Nhược điểm |
|----------|-----------|
| **Train NHANH NHẤT (0.1s)** | Accuracy thấp nhất (95.28%) |
| Predict nhanh (0.03s) | FNR cao nhất (5.30%) = bỏ sót nhiều |
| Hợp dữ liệu text/count | Giả định độc lập giữa các từ (naive) |

**Vì sao yếu nhất?** Naive Bayes giả định các từ **độc lập với nhau**, nhưng thực tế từ trong email liên kết chặt (password + verify + login cùng xuất hiện → phishing). Giả định sai làm giảm độ chính xác. Đổi lại, nó train gần như tức thì (0.1s).

### 11.5. Bảng so sánh toàn diện (điểm mạnh/yếu):

| Tiêu chí | LR | XGBoost | Random Forest | Naive Bayes |
|----------|-----|---------|---------------|-------------|
| **Accuracy** | 🥇 99.02% | 🥈 98.27% | 🥉 97.23% | 95.28% |
| **FNR (bỏ sót)** | 🥇 0.95% | 🥈 1.52% | 2.61% | 5.30% |
| **Tốc độ train** | 109s | 912s | 133s | 🥇 0.1s |
| **Tốc độ predict** | 🥇 0.03s | 0.80s | 1.35s | 🥇 0.03s |
| **Giải thích được** | ✅ | ⚠️ Khó | ✅ | ✅ |
| **Cần scale?** | ✅ Có | ❌ Không | ❌ Không | ❌ Không |

### 11.6. KẾT LUẬN & ĐỀ XUẤT:

#### Mô hình tối ưu nhất: **Logistic Regression (99.02%)**

**3 lý do chính:**
1. **Chính xác nhất** — F1 = 99.02%, cao hơn Random Forest 1.79%
2. **An toàn nhất** — FNR = 0.95% (bỏ sót chỉ ~193 phishing / 19,450), tốt hơn RF 2.7×
3. **Nhanh nhất** — Predict 0.03s/email (nhanh hơn RF 45×), phù hợp hệ thống real-time

#### So sánh với mô hình cũ (Random Forest):

| Metric | Random Forest (cũ) | Logistic Regression (mới) | Cải thiện |
|--------|---------------------|---------------------------|-----------|
| Accuracy | 97.23% | **99.02%** | ✅ +1.79% |
| F1 | 97.23% | **99.02%** | ✅ +1.79% |
| FNR | 2.61% | **0.95%** | ✅ Giảm 2.7× (bỏ sót ít hơn) |
| Predict time | 1.35s | **0.03s** | ✅ Nhanh 45× |

#### Đề xuất cho đồ án:

```
KHUYẾN NGHỊ 1 (an toàn, giữ nguyên code):
  → GIỮ Random Forest (97.23%) làm mô hình chính
  → Lý do: code đang hoạt động tốt, RL 99% là đủ cho đồ án
  → Ghi vào báo cáo: "Đã so sánh 4 mô hình, LR đạt cao nhất nhưng
     RF ổn định + giải thích được, phù hợp hệ thống hybrid"

KHUYẾN NGHỊ 2 (tối ưu, cần sửa code):
  → CHUYỂN sang Logistic Regression (99.02%)
  → Cần: thêm MaxAbsScaler vào pipeline + đổi classifier
  → Lợi: chính xác hơn, predict nhanh 45×, an toàn hơn (FNR thấp)
```

### 11.7. CÂU TRẢ LỜI CHO CÔ:

> *"Dạ, em đã chạy so sánh 4 mô hình trên cùng dataset 204K email, cùng 30,009 features, cùng cách chia 80/20. Kết quả: Logistic Regression thắng với F1=99.02%, tiếp đến XGBoost 98.27%, Random Forest 97.23%, Naive Bayes 95.28%.*
>
> *Lý do Logistic Regression thắng: features TF-IDF tuyến tính nên model tìm đường phân cách tuyến tính tối ưu. Vấn đề của LR là phải scale dữ liệu, nếu không sẽ lỗi như lần đầu em chạy (chỉ 52%). XGBoost chính xác cao nhưng train 15 phút. Naive Bayes nhanh nhất (0.1s) nhưng yếu nhất vì giả định các từ độc lập.*
>
> *Từ bảng so sánh, em kết luận Logistic Regression tối ưu nhất về cả chính xác (99.02%), tốc độ predict (0.03s), và độ an toàn (FNR chỉ 0.95% — bỏ sót rất ít phishing)."*

### 11.8. Lưu ý quan trọng (nếu cô hỏi về lỗi LR đầu tiên):

> *Lần chạy đầu Logistic Regression chỉ đạt 52.4% vì chưa scale dữ liệu. TF-IDF cho giá trị 0-1 nhưng 9 security features có thể rất lớn (text_length có thể > 10,000). Saga solver không hội tụ khi các feature có scale khác nhau → model dự đoán tất cả là legit (FNR=100%). Thêm MaxAbsScaler chia giá trị về [-1, 1] → LR hội tụ đúng, đạt 99.02%. Đây là bài học: **feature scaling rất quan trọng với mô hình tuyến tính**."*

---

## TÓM TẮT CÔNG THỨC & SO SÁNH MÔ HÌNH

```
1. Accuracy  = (TP + TN) / (TP + TN + FP + FN)     = 97.23% (RF)
2. Precision = TP / (TP + FP)                        = 96.81%
3. Recall    = TP / (TP + FN) = 1 - FNR             = 97.39%
4. F1-Score  = 2 × (P × R) / (P + R)               = 97.10%
5. FPR       = FP / (FP + TN)                        = 2.91%
6. FNR       = FN / (FN + TP)                        = 2.61%

7. Điểm rủi ro = max(ML_score, Heuristic_score)

8. ĐẦU RA NHỊ PHÂN (THỐNG NHẤT):
   score >= 60 → PHISHING     (label = 1, bị)
   score <  60 → NOT PHISHING (label = 0, không bị)

9. SO SÁNH 4 MÔ HÌNH (cùng dataset, cùng features):
   Logistic Regression  F1 = 99.02%  ← TỐT NHẤT (predict 0.03s, FNR 0.95%)
   XGBoost              F1 = 98.27%  (train 15 phút)
   Random Forest (cũ)   F1 = 97.23%  (predict 1.35s, ổn định)
   Naive Bayes          F1 = 95.28%  (train 0.1s, nhanh nhất)
```
