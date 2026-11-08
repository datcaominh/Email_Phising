# MASTER THEORY — HỆ THỐNG PHÁT HIỆN EMAIL PHISHING

> **Tài liệu lý thuyết tổng hợp** cho đồ án *"Hệ thống phát hiện email phishing sử dụng Machine Learning và AI"*.
> Gộp nội dung `DATASET_GUIDE.md` + `LY_THUYET_GO_Y.md`, sắp xếp lại theo logic mạch lạc.
>
> **Cấu trúc tài liệu:**
> - **Phần A — DATASET** (tổng quan, nguồn gốc, schema, mẫu)
> - **Phần B — TIỀN XỬ LÝ DỮ LIỆU** (pipeline, kiểm tra trùng lặp, chia train/test)
> - **Phần C — TRÍCH XUẤT ĐẶC TRƯNG** (TF-IDF, 9 Security Features)
> - **Phần D — CÁC MÔ HÌNH MACHINE LEARNING** (RF, Logistic Regression, Naive Bayes, XGBoost + bảng chi tiết, ma trận nhầm lẫn, ROC)
> - **Phần E — ĐÁNH GIÁ MÔ HÌNH** (Confusion Matrix, Accuracy, FPR/FNR, ROC/AUC, ma trận nhầm lẫn trong chương trình, ngưỡng 60%)
> - **Phần F — HỆ THỐNG HYBRID & LLM** (pipeline 6 bước, max(ML, heuristic), Gemini)
> - **Phần G — DẤU HIỆU PHISHING & TÀI LIỆU THAM KHẢO**
> - **Phần H — CÂU HỎI CỦA CÔ** (Q&A — đặt ở cuối)

---

# PHẦN A — DATASET

## A1. Tổng quan dataset đang dùng

> **Lưu ý quan trọng:** Các kho dữ liệu thô ban đầu (Enron, TREC, SpamAssassin...) vốn ở định dạng email thô (mbox/raw text). Trong đề tài này, em sử dụng phiên bản **11 Curated Datasets** đã được chuẩn hóa cấu trúc 7 trường thông tin và làm sạch bởi nhóm nghiên cứu của **TS. Minhaz F. Zibran và Arifa I. Champa (Idaho State University, Mỹ)**.

| Thông số | Giá trị |
|----------|---------|
| **Tên** | Phishing Email Curated Datasets |
| **Tác giả** | Champa, A.I., Rabbi, M.F., Zibran, M.F. (Idaho State University, USA) |
| **Năm** | 2024 |
| **Bài báo IEEE #1** | IEEE ICMI 2024 — *"Curated Datasets and Feature Analysis for Phishing Email Detection with Machine Learning"* (7 datasets cơ bản) |
| **Bài báo IEEE #2** | IEEE ISDFS 2024 — *"Why Phishing Emails Escape Detection: A Closer Look at the Failure Points"* (mở rộng đủ 11 datasets) |
| **IEEE Xplore** | https://ieeexplore.ieee.org/document/10585821 |
| **Kho 7 Datasets (Figshare)** | `10.6084/m9.figshare.25432108` |
| **Kho 11 Datasets (Figshare)** | `10.6084/m9.figshare.24952503` |
| **Zenodo (bản tổng hợp lại)** | `10.5281/zenodo.8339691` |
| **Tổng ban đầu** | 221,093 email (11 file CSV) |
| **Sau tiền xử lý** | **206,722 email** |
| **Phishing (1)** | 98,527 (47.7%) |
| **Legitimate (0)** | 108,195 (52.3%) |
| **Ngôn ngữ** | Tiếng Anh |



Zenodo Doi : https://zenodo.org/records/8339691



> **Lưu ý về Kaggle:** Bản phổ biến trên Kaggle (https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset) là bản tổng hợp lại từ các file .csv đã tiền xử lý của nhóm Champa et al.



**Tại sao chọn dataset này?**

| Tiêu chí | Đánh giá |
|----------|----------|
| **Mới nhất** | 2024 (IEEE ICMI) |
| **Uy tín** | IEEE paper, DOI Zenodo, 44,193 lượt tải |
| **Đa dạng** | 11 nguồn, 1998–2022 |
| **Cân bằng** | 47.7% / 52.3% (gần 50/50) |
| **License** | CC BY 4.0 (miễn phí thương mại) |
| **Cải thiện** | Accuracy: 85–90% → **97.23%** |

## A2. Bảng tổng hợp 11 file (số liệu thật, đọc trực tiếp từ file)

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

### Bảng nguồn gốc tổ chức & link xác thực (dùng cho báo cáo)

| Tổ chức / Viện nghiên cứu | Bộ dữ liệu | Tác giả gốc / Người công bố | Link xác thực |
|---------------------------|-----------|------------------------------|---------------|
| **IEEE & Idaho State University** (USA) | Bộ 11 Curated Datasets (.csv) | A. I. Champa, M. F. Rabbi, M. F. Zibran (2024) | • IEEE: https://ieeexplore.ieee.org/document/10585821<br>• Kho 7 datasets: https://doi.org/10.6084/m9.figshare.25432108<br>• Kho 11 datasets: https://doi.org/10.6084/m9.figshare.24952503 |
| **NIST (USA) & University of Waterloo (Canada)** | TREC_05, TREC_06, TREC_07 | Gordon V. Cormack & Thomas R. Lynam | • https://trec.nist.gov/data/spam.html<br>• https://plg.uwaterloo.ca/~gvcormac/treccorpus/ |
| **CEAS & University of Waterloo (Canada)** | CEAS_08 | Gordon V. Cormack (CEAS 2008 Live Challenge) | • https://ceas.cc/2008/<br>• https://plg.uwaterloo.ca/~gvcormac/ceascorpus/ |
| **Carnegie Mellon University (USA)** | Enron | William W. Cohen (CMU) / Bryan Klimt & Yiming Yang | • https://www.cs.cmu.edu/~enron/ |
| **Apache Software Foundation (USA)** | SpamAssasin | Dự án Apache SpamAssassin | • https://spamassassin.apache.org/old/publiccorpus/ |
| **Athens University of Economics and Business (Greece)** | Ling (Ling-Spam) | Ion Androutsopoulos et al. (2000) | • https://nlp.cs.aueb.gr/software_and_datasets/lingspam_public.tar.gz<br>• Bài báo gốc: https://arxiv.org/abs/cs/0008019 |
| **Arbor Networks (USA)** | Nazario & Nazario_5 | Jose Nazario | • https://monkey.org/~jose/phishing/ |
| **University of Michigan - CLAIR Lab (USA)** | Nigerian_Fraud & Nigerian_5 | Dragomir Radev (CLAIR Collection, 2008) | • https://www.kaggle.com/datasets/rtatman/fraudulent-email-corpus |

> **Lưu ý:** Các file .csv trong `data_train/raw/` là sản phẩm chuẩn hóa của Champa et al. (Idaho State University) công bố trên Figshare. Các link "tác giả gốc" ở trên là nguồn dữ liệu thô ban đầu (mbox/raw text) mà nhóm tác giả đã trích xuất.

---

## A3. Nguồn gốc từng file (đã hiệu đính — chứng minh thuộc bài báo IEEE)

### CEAS_08.csv — Conference on Email and Anti-Spam 2008
- **Tổ chức & Tác giả gốc:** Hội nghị CEAS 2008, biên soạn bởi **GS. Gordon V. Cormack (University of Waterloo, Canada)**
- **Nguồn chuẩn hóa CSV:** Champa et al. (IEEE ICMI 2024) — Figshare DOI: 10.6084/m9.figshare.25432108
- **Nội dung:** Email thực tế từ cuộc thi lọc thư rác CEAS 2008 Challenge. Đủ 7 cột. Phân bố 55.8% phishing/spam, 44.2% legit.
- **Link xác thực:**
  - Hội nghị: https://ceas.cc/2008/
  - Corpus gốc: https://plg.uwaterloo.ca/~gvcormac/ceascorpus/
- **Ví dụ thật:** Email spam thuốc kích dục có URL `whitedone.com`, label=1.

### Enron.csv — Enron Corporate Email Corpus
- **Tổ chức & Tác giả gốc:** Công bố bởi Ủy ban Điều tiết Năng lượng Liên bang Mỹ (FERC) sau vụ phá sản Enron (2001); chuẩn hóa phục vụ nghiên cứu ML bởi **GS. William W. Cohen tại Carnegie Mellon University (CMU)**. Thu thập ban đầu bởi Bryan Klimt & Yiming Yang.
- **Link xác thực:** https://www.cs.cmu.edu/~enron/ (Bản CSV trích xuất bởi Champa et al., IEEE ICMI 2024)
- **Nội dung:** Email công việc nội bộ có thật (hợp đồng, báo cáo, lịch họp). Trong bản Champa (2024), chỉ trích xuất **3 cột** (subject, body, label) — thiếu sender, date, urls.
- **Ví dụ thật:** "hpl nom for may 25, 2001" — email hợp đồng gas điện, label=0.

### Ling.csv — Ling-Spam Dataset
- **Tổ chức & Tác giả gốc:** Nhóm của **GS. Ion Androutsopoulos tại Athens University of Economics and Business (AUEB, Hy Lạp)**, công bố năm 2000 — *"An Evaluation of Naive Bayesian Anti-Spam Filtering"*
- **Link xác thực:**
  - Bài báo gốc: https://arxiv.org/abs/cs/0008019
  - Dữ liệu: https://nlp.cs.aueb.gr/software_and_datasets/lingspam_public.tar.gz
  - Bản CSV: Figshare DOI: 10.6084/m9.figshare.25432108
- **Nội dung:** 2,859 email lấy từ mailing list chuyên ngành Ngôn ngữ học (Linguist List) trộn spam thực tế. ~84% legit, 16% spam. Chỉ gồm **3 cột** (subject, body, label).
- **Ví dụ thật:** "job posting - apple-iss research center" — email tuyển dụng thật, label=0.

### Nazario.csv & Nazario_5.csv — Jose Nazario Phishing Corpus
- **Tác giả gốc:** **TS. Jose Nazario** (cựu chuyên gia nghiên cứu bảo mật tại Arbor Networks, Mỹ)
- **Link xác thực:**
  - Kho gốc: https://monkey.org/~jose/phishing/
  - Bản CSV (cả 2 file): Champa et al. (IEEE ISDFS 2024) — Figshare DOI: 10.6084/m9.figshare.24952503
- **Nội dung:**
  - **Nazario.csv:** 100% email phishing thật (label=1) giả mạo tổ chức tài chính, ngân hàng, eBay, PayPal, AOL.
  - **Nazario_5.csv:** Do nhóm Champa et al. (2024) tạo bằng cách kết hợp phishing (kho Nazario đến 2015) với email hợp lệ Enron → bộ cân bằng (51% phishing / 49% legit), đầy đủ 7 cột.
- **Ví dụ thật:** Email giả mạo "Mail System Internal Data" lừa người dùng.

### Nigerian_Fraud.csv & Nigerian_5.csv — CLAIR Fraudulent E-mail Corpus (419 Scam)
- **Tổ chức & Tác giả gốc:** **GS. Dragomir Radev tại phòng thí nghiệm CLAIR, University of Michigan (Mỹ)**, công bố qua ACL Data and Code Repository (mã ADCR2008T001, năm 2008).
- **Link xác thực:**
  - Bản lưu trữ: https://www.kaggle.com/datasets/rtatman/fraudulent-email-corpus
  - Bản CSV (cả 2 file): Champa et al. (IEEE ISDFS 2024) — Figshare DOI: 10.6084/m9.figshare.24952503
- **Nội dung:**
  - **Nigerian_Fraud.csv:** 3,332 email lừa đảo trả phí trước (Advance-fee fraud / 419 Nigeria) thu thập 1998–2007, 100% label=1.
  - **Nigerian_5.csv:** Champa et al. (2024) kết hợp Nigerian Fraud + email hợp lệ → tập cân bằng (52.6% phishing / 47.4% legit).
- **Ví dụ thật:** Email từ "MR. JAMES NGOLA" giả làm trợ lý tổng thống Congo, label=1.

### SpamAssasin.csv — Apache SpamAssassin Public Corpus
- **Tổ chức:** Apache Software Foundation (Mỹ)
- **Link xác thực:**
  - Corpus: https://spamassassin.apache.org/old/publiccorpus/
  - Bản CSV: Figshare DOI: 10.6084/m9.figshare.25432108
- **Nội dung:** Email thật (~70% ham / 30% spam) thu thập 2002–2003 phục vụ kiểm thử bộ lọc SpamAssassin. Đủ 7 cột.
- **Ví dụ thật:** Email kỹ thuật từ GS về lỗi phần mềm, label=0.

### TREC_05/06/07.csv — Text Retrieval Conference Spam Track
- **Tổ chức & Tác giả gốc:** Viện Tiêu chuẩn và Công nghệ Quốc gia Mỹ (**NIST**) phối hợp cùng **GS. Gordon V. Cormack (University of Waterloo, Canada)** — Corpus của Thomas R. Lynam & Gordon V. Cormack.
- **Link xác thực:**
  - NIST: https://trec.nist.gov/data/spam.html
  - Waterloo: https://plg.uwaterloo.ca/~gvcormac/treccorpus07/ (05, 06: /treccorpus05/, /treccorpus06/)
  - Bản CSV: Figshare DOI: 10.6084/m9.figshare.25432108
- **Nội dung:** Bộ dữ liệu chuẩn quy mô lớn nhất từ cuộc thi TREC Spam Track 2005–2007 (TREC_05: ~55,990 mẫu, TREC_07: ~53,757 mẫu). Email từ IS spam feed + Enron.
- **Ví dụ thật TREC_07:** Email spam Viagra từ "Tomas Jacobs <RickyAmes@aol.com>", label=1.
- **Lưu ý:** Có dòng label NaN (TREC_05: 715, TREC_06: 57) — đã loại khi tiền xử lý.

**Bảng tóm tắt tổ chức chủ quản:**

| Tổ chức | Dataset | Link xác thực |
|---------|---------|---------------|
| **IEEE & Idaho State University** | 11 Curated Datasets (.csv) | https://ieeexplore.ieee.org/document/10585821 |
| **NIST (USA) & University of Waterloo** | TREC_05/06/07 | https://trec.nist.gov/data/spam.html |
| **CEAS & University of Waterloo** | CEAS_08 | https://ceas.cc/2008/ |
| **Carnegie Mellon University** | Enron | https://www.cs.cmu.edu/~enron/ |
| **Apache Foundation** | SpamAssasin | https://spamassassin.apache.org/old/publiccorpus/ |
| **Athens Univ. of Economics & Business** | Ling | https://arxiv.org/abs/cs/0008019 |
| **Arbor Networks** | Nazario | https://monkey.org/~jose/phishing/ |
| **University of Michigan - CLAIR Lab** | Nigerian Fraud | https://www.kaggle.com/datasets/rtatman/fraudulent-email-corpus |

---

## A4. Cấu trúc thư mục (phân biệt file gốc và file xử lý)

```
data_train/
├── raw/                    ← FILE GỐC (chưa xử lý — để đối chiếu)
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
├── raw_samples/            ← FILE MẪU 100 DONG/FILE (mo Excel khong lag)
│   ├── ALL_RAW_combined_1000.csv   (1,000 dong gop, co cot source_file)
│   ├── CEAS_08_sample.csv
│   └── ... (11 file mau)
│
├── sample_1000_rows.csv    ← 1,000 DONG MAU TU merged_clean
│
└── processed/              ← FILE ĐÃ XỬ LÝ (dùng cho training)
    └── merged_clean.csv    (361.4 MB, 206,722 email)
```

---

## A5. Schema (cột dữ liệu)

```
Cột         | Kiểu dữ liệu | Ví dụ
------------|--------------|---------------------------
sender      | string       | "admin@bank.com"
receiver    | string       | "user@gmail.com"
date        | string       | "2008-01-15 10:30:00"
subject     | string       | "Verify your account now"
body        | string       | "Click here to verify..."
label       | int (0 or 1) | 1
urls        | string/int   | "http://fake-bank.com/login" hoặc số URL
source      | string       | "CEAS_08" (tên nguồn)
```

**Schema thiếu metadata (2 file: Enron, Ling):**
```
subject   : string
body      : string
label     : int
```

**Trường hợp đặc biệt:**
- **Nazario_5.csv:** cột `urls` là **list object** (không phải số)
- **TREC_05/06:** có dòng `label = NaN` (đã xử lý)

---

## A6. Dữ liệu nội dung thật (mẫu cho cô xem)

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

# PHẦN B — TIỀN XỬ LÝ DỮ LIỆU

## B1. Pipeline tiền xử lý 6 bước (`scripts/merge_datasets.py`)

```
Bước 1: ĐỌC 11 FILE
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

**Bảng chi tiết từng bước:**

| # | Bước | Chi tiết | Số lượng |
|---|------|----------|----------|
| 1 | Đọc 11 file | Thử utf-8 → latin-1, engine c → python | 221,093 |
| 2 | Chuẩn hóa schema | Thêm cột thiếu (sender, date, urls...) | — |
| 3 | Clean text | Bỏ HTML tags, chuẩn hóa whitespace | — |
| 4 | Normalize label | Map về 0/1 thống nhất | — |
| 5 | Bỏ label invalid | Label != 0 và != 1 | −3,862 |
| 6 | Bỏ email rỗng | Cả subject và body đều rỗng | −0 |
| 7 | Dedup | Bỏ trùng theo subject + body | −10,509 |
| **TỔNG** | | | **206,722** |

**Phân bố sau xử lý:**
```
Phishing (1):   98,527 email (47.7%)  ████████████████████░░░░░
Legitimate (0): 108,195 email (52.3%)  █████████████████████░░░

→ Cân bằng tốt (gần 50/50) → Rất tốt cho ML
```

**Kết quả:** `data_train/processed/merged_clean.csv` (361.4 MB, 206,722 email)

---

## B2. Kiểm tra trùng lặp (chống "Accuracy ảo")

**Vì sao phải kiểm tra?** Nếu dữ liệu trùng lặp, mô hình có thể "học thuộc" email test (vì đã thấy trong train) → Accuracy cao nhưng **ảo**, không phản ánh khả năng thật.

Script: `python scripts/check_duplicates.py`

**Kết quả thực tế:**

| Kiểm tra | Kết quả |
|----------|---------|
| Trùng lặp hoàn toàn (7 cột) | **0 dòng (0.00%)** ✅ |
| Trùng theo subject + body | **0 dòng (0.00%)** ✅ |
| Label mâu thuẫn (trùng text nhưng nhãn khác) | **0 nhóm** ✅ |
| Trùng sender+subject+date | 9,744 dòng (4.71%) ⚠️ |

**Giải thích:**
- **Trùng hoàn toàn = 0** → không có 2 email giống hệt nhau → không lo học trùng.
- **4.71% trùng sender+subject+date** là email cùng người gửi/cùng tiêu đề/cùng ngày nhưng **nội dung body khác nhau** (VD: chuỗi email Enron Reply cùng thread). Đây KHÔNG phải trùng lặp nên vẫn giữ.

**Kết luận:** 206,722 email đều duy nhất → **Accuracy là thật, không bị ảo do trùng lặp.**

---

## B3. Chia train/test 80/20

### Nguyên tắc cơ bản
Mô hình chỉ được **học (train)** trên dữ liệu train và **kiểm tra (evaluate)** trên test mà nó **chưa từng thấy**. Nếu trùng nhau → kết quả ảo, mô hình không generalize được.

```
206,722 email
    ↓  split 80/20 (stratified)
165,377 train  →  model HỌC từ đây (TF-IDF fit + Classifier fit)
 41,345 test   →  model CHƯA TỪNG THẤY → ĐÁNH GIÁ trung thực
```

### So sánh các tỷ lệ

| Tỷ lệ | Train | Test | Ưu điểm | Nhược điểm |
|--------|-------|------|---------|-----------|
| 70/30 | 144K | 62K | Test lớn, đánh giá ổn định | Train bớt dữ liệu |
| **80/20** | **165K** | **41K** | **Cân bằng: đủ data train + test đủ lớn** | **(Đang dùng)** |
| 90/10 | 186K | 21K | Train nhiều nhất | Test nhỏ → metric dao động |
| 99/1 | 205K | 2K | Train tối đa | Đánh giá không đáng tin |

### Lý do chọn 80/20
- Test set 41,345 email **rất lớn** → metric có ý nghĩa thống kê cao, không phải do may.
- Train 165K email đủ để mô hình học tốt (quá ít → underfit).
- Đây là **chuẩn ngành (industry standard)**.

### Stratify và random_state
- `stratify=labels`: đảm bảo tỉ lệ phishing/legit trong train và test **giống hệt** dataset gốc (47.7/52.3), tránh lệch do ngẫu nhiên.
- `random_state=42`: mỗi lần chạy cho **kết quả giống nhau** → đảm bảo tính tái lập (reproducibility).

### Tránh Data Leakage
Thứ tự đúng trong code:
```
1. Split TRƯỚC (dòng 90): chia train/test
2. pipeline.fit(x_train) — TF-IDF chỉ fit trên TRAIN (dòng 97)
3. transform(x_test) — test chỉ bị transform, KHÔNG fit
```
Nếu fit TF-IDF trên **toàn bộ** dữ liệu rồi mới split → mô hình "thấy" cả từ trong test → **gian lận (data leakage)**.

---

# PHẦN C — TRÍCH XUẤT ĐẶC TRƯNG (FEATURE ENGINEERING)

## C1. Tổng quan

Mỗi email được biến thành **vector 30,009 chiều** = TF-IDF (30,000) + 9 Security Features:

```
Email text
    ↓
FeatureUnion (pipeline)
├── TfidfVectorizer(max_features=30000, ngram_range=(1,2))
│   → Ma trận 30,000 cột (tần suất từ có trọng số)
└── SecurityFeatureExtractor()
    → 9 số (đếm từ khóa nguy hiểm, URL...)
    ↓
Vector 30,009 chiều → feed vào mô hình
```

## C2. TF-IDF là gì?

**TF-IDF (Term Frequency-Inverse Document Frequency)** biến email thành ma trận 30,000 cột. Mỗi cột là một từ, giá trị = tần suất từ đó trong email × độ hiếm của từ đó trong toàn bộ dataset. Từ phổ biến ở mọi email (như "the") có trọng số thấp, từ hiếm như "urgent" có trọng số cao.

**Công thức:**
```
TF-IDF(t, d) = TF(t, d) × IDF(t)

TF(t,d)  = số lần từ t xuất hiện trong email d
IDF(t)   = log(Tổng số email / Số email chứa từ t)
```

**Ví dụ:**
- Từ "the" xuất hiện ở mọi email → IDF ≈ log(206722/206722) = 0 → TF-IDF ≈ 0
- Từ "urgent" chỉ xuất hiện 1,000 email → IDF = log(206722/1000) = 5.3 → TF-IDF cao

**Tại sao dùng ngram_range=(1,2)?** Bắt cả cụm 2 từ: "verify account", "wire transfer" — phishing thường dùng cụm từ, không chỉ từ đơn lẻ.

## C3. 9 Security Features (chi tiết trong `app/features.py`)

| # | Feature | Cách tính | Lý thuyết ánh xạ |
|---|---------|-----------|-------------------|
| 1 | text_length | `len(text)` | Email dài bất thường (nội dung giả) |
| 2 | url_count | `len(urls)` | Technical: nhiều link = đáng ngờ |
| 3 | suspicious_url_count | URL chứa "login", "bit.ly", ".ru" | Technical: URL có pattern xấu |
| 4 | urgency_count | Đếm "urgent", "khẩn cấp", "act now" | Linguistic: tính cấp bách |
| 5 | credential_count | Đếm "password", "login", "mật khẩu" | Linguistic: yêu cầu thông tin |
| 6 | money_count | Đếm "payment", "invoice", "bank" | Linguistic: liên quan tiền bạc |
| 7 | has_at_in_url | URL có "@" không | Technical: @ trick lừa đảo |
| 8 | has_ip_address | Dùng IP thay domain | Technical: IP thay domain |
| 9 | has_dash_url | Domain có gạch nối | Technical: typosquatting (paypal-secure.com) |

**Từ khóa nhóm Security Features (trong code):**
```
URGENCY_TERMS:    urgent, immediately, within 24 hours, suspended, khẩn cấp...
CREDENTIAL_TERMS: password, login, sign in, verify, mật khẩu, đăng nhập...
MONEY_TERMS:      payment, invoice, wire transfer, bank, thanh toán...
SUSPICIOUS_URL:   login, verify, secure, bit.ly, tinyurl, .ru, .zip
```

---

# PHẦN D — CÁC MÔ HÌNH MACHINE LEARNING

## D1. Tổng quan 4 mô hình so sánh

Để trả lời yêu cầu *"so sánh nhiều mô hình, biết mô hình nào tối ưu"*, em đã chạy **4 mô hình** trên **cùng dataset, cùng features, cùng cách chia train/test** → kết quả công bằng.

### Thiết kế thí nghiệm (giống hệt cho cả 4 mô hình)

| Thành phần | Giá trị |
|------------|-------------------------------------|
| Dataset | `merged_clean.csv` — 204,294 email hợp lệ |
| Chia train/test | 80/20 stratified, `random_state=42` |
| Train / Test | 163,435 / 40,859 email |
| Features | TF-IDF (30,000) + 9 Security Features = 30,009 chiều |
| Label | Nhị phân: 0 (legit) / 1 (phishing) |

> **Tại sao phải giống nhau?** Chỉ khi dữ liệu đầu vào, cách chia và features giống nhau, thì chênh lệch Accuracy/F1 mới **chỉ do mô hình**, không do yếu tố khác.

---

## D2. Random Forest (mô hình hiện tại — baseline)

### Nguyên lý hoạt động
Random Forest là **ensemble** của nhiều cây quyết định (decision tree). Mỗi cây:
1. Học trên 1 mẫu ngẫu nhiên (**bootstrap**) của dữ liệu
2. Tại mỗi nút, chỉ xét 1 tập con ngẫu nhiên các features
3. Ra quyết định: "Nếu có từ 'urgent' → nghi phishing"

**Dự đoán = bỏ phiếu:**
```
P(phishing) = (Số cây bầu class 1) / Tổng số cây
Ví dụ: 170/200 = 0.85 → 85%
```

### Công thức (Gini Impurity — độ tinh khiết)
Cây chọn nút chia sao cho **Gini thấp nhất** (dữ liệu tinh khiết nhất):
```
Gini(node) = 1 − Σ P(i)²

Với P(i) = tỉ lệ class i trong node
Gini = 0 → node thuần 1 lớp (hoàn hảo)
Gini = 0.5 → node chia đều 2 lớp (kém)
```

### Siêu tham số trong code
```python
RandomForestClassifier(
    n_estimators=200,        # 200 cây quyết định
    max_depth=30,            # chiều sâu tối đa mỗi cây (chống overfit)
    class_weight="balanced", # cân bằng 2 lớp
    random_state=42,         # seed cố định (tái lập)
    n_jobs=-1                # dùng toàn bộ CPU
)
```

### Ưu/nhược điểm
| Ưu điểm | Nhược điểm |
|----------|-----------|
| Ổn định, ít tham số tinh chỉnh | Predict chậm nhất trong 4 mô hình (xem D6) |
| Giải thích được (feature importance) | Accuracy thấp hơn LR |
| Chống overfit tốt (vote 200 cây) | FNR cao hơn LR |

### Điểm đặc thù trong đồ án
- **Không cần feature scaling**: RF là mô hình dựa trên ngưỡng tại từng nút cây → giá trị lớn/nhỏ không ảnh hưởng thứ tự chia. Do đó RF chạy đúng ngay trên ma trận TF-IDF thưa, **không cần MaxAbsScaler** — đây là lý do chính em giữ RF làm mô hình vận hành (xem D7).
- **Xác suất = trung bình xác suất 200 cây**: không phải chỉ số cây bầu 1 mà mỗi cây trả về xác suất trong lá (tỉ lệ class 1), rồi lấy trung bình → giá trị dự đoán **điềm đạm hơn**, ít bị đẩy về 0/1 cực đoan.
- **AUC & ma trận nhầm lẫn**: xem biểu đồ `results/roc_comparison.png` và `results/confusion_matrix_rf.png` (hiển thị trong app, tab "Danh gia mo hinh").

---

## D3. Logistic Regression (mô hình TỐT NHẤT)

### Nguyên lý hoạt động
Tìm **đường phân cách tuyến tính** (hyperplane) tốt nhất giữa 2 lớp phishing/legit trong không gian 30,009 chiều.

### Công thức — Hàm Sigmoid
```
P(phishing | x) = σ(w·x + b) = 1 / (1 + e^(−(w·x + b)))

Trong đó:
- w = vector trọng số (học được, 30,009 phần tử)
- b = bias
- w·x = tích vô hướng
- σ(z) = sigmoid, đưa kết quả về khoảng (0, 1)
```

**Quyết định nhị phân:**
```
P ≥ 0.5 → Phishing (label 1)
P <  0.5 → Not Phishing (label 0)
```

### Tối ưu bằng Gradient Descent
```
w_new = w_old − learning_rate × ∇L(w_old)

- learning_rate: bước nhảy (LR mặc định của sklearn: 0.01 với solver saga)
- ∇L: gradient của hàm loss (log-loss)
- Lặp lại đến khi hội tụ
```

### Feature Scaling 
TF-IDF cho giá trị 0–1 nhưng 9 Security Features có thể rất lớn (text_length > 10,000). **Saga solver không hội tụ khi các feature có scale khác nhau** → lần chạy đầu LR chỉ đạt 52.4% (dự đoán tất cả là legit, FNR=100%).

**Giải pháp:** Thêm `MaxAbsScaler` chia giá trị về [−1, 1] → LR hội tụ đúng, đạt **99.02%**.

```python
from sklearn.preprocessing import MaxAbsScaler
scaler = MaxAbsScaler()
X_train_scaled = scaler.fit_transform(X_train)   # fit trên train
X_test_scaled = scaler.transform(X_test)          # chỉ transform test
```

> **Bài học:** Feature scaling rất quan trọng với mô hình tuyến tính.

### Siêu tham số
```python
LogisticRegression(
    max_iter=5000,        # số vòng lặp tối đa (để hội tụ)
    solver="saga",        # solver phù hợp sparse matrix
    tol=1e-4,             # ngưỡng hội tụ
    random_state=42
)
```

### Ưu/nhược điểm
| Ưu điểm | Nhược điểm |
|----------|-----------|
| **Chính xác nhất (99.02%)** | Yêu cầu scale dữ liệu (MaxAbsScaler) |
| **Predict nhanh nhất trong 4 mô hình** (xem D6) | Hội tụ lâu nếu không scale |
| **FNR thấp nhất (0.95%)** | Giả định tuyến tính (không bắt phi tuyến) |
| Giải thích được (hệ số trọng số từng từ) | |

**Vì sao thắng?** TF-IDF cho ma trận **linearly separable** (các từ phân biệt phishing/legit rõ trên không gian 30,009 chiều). LR tìm đường phân cách tuyến tính tối ưu → rất phù hợp dữ liệu text TF-IDF.

### Điểm đặc thù trong đồ án
- **Bắt buộc MaxAbsScaler**: thực nghiệm của chính đồ án cho thấy thiếu scaler, LR chỉ đạt **52.4%** (gần đoán ngẫu nhiên) vì solver saga không hội tụ trên ma trận thưa giá trị lệch thang. Đây là "điểm chết" của LR khi triển khai: một lần quên bước preprocessing là mô hình sụp.
- **Xác suất thường bị đẩy cực đoan**: LR huấn luyện đến hội tụ trên dữ liệu tuyến tính phân ly → xác suất hay về gần 0 hoặc gần 1 → **overconfident** khi gặp dữ liệu ngoài phân phối (email tiếng Việt, định dạng lạ).
- **AUC & ma trận nhầm lẫn**: `results/confusion_matrix_lr.png` — FP/FN thấp nhất trong 4 mô hình ở ngưỡng 0.5 (xem D6).

---

## D4. Multinomial Naive Bayes

### Nguyên lý — Định lý Bayes
```
P(phishing | words) = P(words | phishing) × P(phishing) / P(words)

P(phishing)   = prior (tỉ lệ phishing trong dataset)
P(words|phishing) = likelihood (tần suất các từ trong email phishing)
```

### Giả định "Naive" (độc lập có điều kiện)
Giả định các từ **độc lập với nhau** given lớp:
```
P(w1, w2, ..., wn | phishing) = P(w1|phishing) × P(w2|phishing) × ... × P(wn|phishing)
```

**Ví dụ:** "verify password login" → P = P(verify) × P(password) × P(login)

### Siêu tham số
```python
MultinomialNB(alpha=1.0)   # alpha = Laplace smoothing (tránh P=0)
```

**Laplace smoothing (alpha):** Nếu từ chưa từng xuất hiện trong email phishing → P=0 → cả tích = 0. Thêm alpha=1 để tránh:
```
P(w|phishing) = (count(w) + alpha) / (total + alpha × V)
```

### Ưu/nhược điểm
| Ưu điểm | Nhược điểm |
|----------|-----------|
| **Train NHANH NHẤT (0.2s)** | **Accuracy thấp nhất (95.28%)** |
| Predict nhanh (xem D6) | FNR cao nhất (5.30%) |
| Hợp dữ liệu text/count | Giả định độc lập giữa các từ (naive) |

**Vì sao yếu nhất?** Giả định các từ độc lập, nhưng thực tế từ liên kết chặt (password + verify + login cùng xuất hiện → phishing). Giả định sai → giảm độ chính xác.

### Điểm đặc thù trong đồ án
- **Không dùng được số âm**: phân phối Multinomial yêu cầu đầu vào là số không âm → MaxAbsScaler (cho phép số âm) **không áp dụng được**, mà TF-IDF + 9 Security Features có giá trị dương là phù hợp sẵn.
- **Đóng vai trò baseline**: train 0.2s cho kết quả 95.28% — dùng làm đường cơ sở để chứng minh 3 mô hình phức tạp hơn mang lại cải thiện thật (97–99%).
- **AUC & ma trận nhầm lẫn**: `results/confusion_matrix_mnb.png` — ô FN (bỏ sót) dày nhất trong 4 mô hình (xem D6).

---

## D5. XGBoost (Gradient Boosting)

### Nguyên lý — Gradient Boosting
Xây dựng nhiều cây **học NỐI TIẾP** (không độc lập như RF):
```
Bước 1: Cây 1 dự đoán → còn lỗi
Bước 2: Cây 2 học từ LỖI của Cây 1 → giảm lỗi
Bước 3: Cây 3 học từ LỖI còn lại → giảm thêm
...
Mỗi cây sửa dần lỗi của cây trước
```

### Learning Rate (tốc độ học) — có ở XGBoost!
```
F_0(x) = mean(y)                          # dự đoán ban đầu
F_m(x) = F_{m-1}(x) + η × h_m(x)         # η = learning_rate

Với η = 0.1 (code): mỗi cây chỉ sửa 10% lỗi
- η nhỏ → học chậm nhưng chính xác hơn
- η lớn → học nhanh nhưng có thể nhảy qua tối ưu
```

> **Liên hệ câu hỏi của cô:** Random Forest KHÔNG có learning rate (học độc lập, vote). XGBoost CÓ learning rate (học nối tiếp, sửa dần lỗi).

### Siêu tham số trong code
```python
XGBClassifier(
    n_estimators=200,        # 200 cây
    max_depth=6,             # chiều sâu mỗi cây (hợp lý cho text)
    learning_rate=0.1,       # tốc độ học
    subsample=0.8,           # 80% dữ liệu mỗi cây (tránh overfit)
    colsample_bytree=0.8,    # 80% features mỗi cây
    eval_metric="logloss",
    random_state=42
)
```

### Ưu/nhược điểm
| Ưu điểm | Nhược điểm |
|----------|-----------|
| Chính xác cao (98.27%) | **Train CHẬM NHẤT (~13 phút)** |
| Chống overfit tốt (subsample, colsample) | Predict chậm hơn LR (xem D6) |
| Xử lý phi tuyến tốt | Nhiều siêu tham số phải tinh chỉnh |

### Điểm đặc thù trong đồ án
- **Học nối tiếp thay vì vote độc lập**: 200 cây của XGBoost mỗi cây sửa **10% lỗi còn sót** của cây trước (learning_rate = 0.1) → hội tụ chậm nhưng chính xác; còn RF 200 cây học độc lập rồi bỏ phiếu.
- **Chi phí tính toán trên ma trận thưa**: 204K mẫu × 30.009 chiều khiến train mất ~13 phút — vượt xa RF (~3 phút) và LR (~2 phút). Phù hợp huấn luyện ngoại tuyến, không hợp chạy lặp lại trên máy cá nhân.
- **AUC & ma trận nhầm lẫn**: `results/confusion_matrix_xgb.png` — cân bằng FP/FN tốt, xếp thứ hai sau LR (xem D6).

---

## D6. Bảng kết quả thực tế (đã chạy, số liệu thật)

### Bảng so sánh chi tiết 4 mô hình

| # | Mô hình | Accuracy | F1 (w.) | Precision | Recall | **AUC** | FPR | FNR | Specificity | Train | Predict* |
|---|---------|----------|---------|-----------|--------|---------|-----|-----|-------------|-------|----------|
| 🥇 | **Logistic Regression** | **99.02%** | **99.02%** | **99.02%** | **99.02%** | **0.9992** | **1.01%** | **0.95%** | **98.99%** | 97.1s | **0.03s** |
| 🥈 | XGBoost | 98.27% | 98.27% | 98.28% | 98.27% | 0.9983 | 1.92% | 1.52% | 98.08% | 874.5s | 0.70s |
| 🥉 | Random Forest (mô hình vận hành) | 97.23% | 97.23% | 97.23% | 97.23% | 0.9967 | 2.91% | 2.61% | 97.09% | 155.5s | 1.55s |
| 4 | Multinomial Naive Bayes | 95.28% | 95.28% | 95.28% | 95.28% | 0.9823 | 4.19% | 5.30% | 95.81% | **0.2s** | 0.04s |

> \* Tốc đo predict tính trên **toàn bộ 40.859 email test** — quy về mỗi email: RF ≈ 0,038 ms, LR ≈ 0,0007 ms. Cả 4 đều đáp ứng yêu cầu real-time.

### Ma trận nhầm lẫn 4 mô hình (TP / FP / TN / FN)

| Mô hình | TP (bắt đúng) | FN (bỏ sót) | FP (báo oan) | TN (đúng sạch) |
|---------|--------------|-------------|--------------|----------------|
| **Logistic Regression** | 19,265 | 185 | 217 | 21,192 |
| XGBoost | 19,155 | 295 | 410 | 20,999 |
| **Random Forest** | 18,943 | 507 | 624 | 20,785 |
| Multinomial Naive Bayes | 18,419 | 1,031 | 897 | 20,512 |

> Anh heatmap ma trận nhầm lẫn: `results/confusion_matrix_{rf,lr,mnb,xgb}.png` — hiển thị trực tiếp trong app (tab "Danh gia mo hinh").

### Biểu đồ ROC & AUC

Biểu đồ `results/roc_comparison.png` vẽ 4 đường ROC trên cùng một trục, mỗi đường có AUC ghi trong legend:

```
Xếp hạng theo AUC (diện tích dưới ROC — không phụ thuộc ngưỡng):
1. Logistic Regression   AUC = 0.9992   ← Xếp hạng nguy cơ tốt nhất
2. XGBoost               AUC = 0.9983
3. Random Forest         AUC = 0.9967   ← MÔ HÌNH VẬN HÀNH
4. Naive Bayes           AUC = 0.9823
```

Đọc biểu đồ: cả 4 đường đều đẩy mạnh lên góc trên-trái (chỉ FPR ~2–5% đã bắt được ~95% phishing) → 4 mô hình đều **xuất sắc** (AUC > 0.9). Chênh AUC giữa LR và RF chỉ 0,0025 — rất nhỏ, thêm căn cứ chọn RF (xem D7).

**Xếp hạng theo F1:**
```
1. Logistic Regression   F1 = 99.02%   ← TỐT NHẤT
2. XGBoost               F1 = 98.27%
3. Random Forest          F1 = 97.23%   ← MÔ HÌNH VẬN HÀNH
4. Naive Bayes           F1 = 95.28%
```

**Kết quả lưu tại:** `results/model_comparison.csv` (chạy `python scripts/compare_models.py` để tái lập)

---

## D7. Bảng so sánh toàn diện & KẾT LUẬN

### So sánh toàn diện

> **Lưu ý đọc bảng:** cột *Tốc độ predict* là thời gian dự đoán **toàn bộ test set 40.859 email**, không phải từng email. Quy đổi ra mỗi email: RF ≈ 0,04ms, LR ≈ 0,0007ms — cả hai đều nhanh hơn mức yêu cầu của ứng dụng rất nhiều.

| Tiêu chí | LR | XGBoost | Random Forest | Naive Bayes |
|----------|-----|---------|---------------|-------------|
| **Accuracy** | 🥇 99.02% | 🥈 98.27% | 🥉 97.23% | 95.28% |
| **AUC** | 🥇 0.9992 | 🥈 0.9983 | 🥉 0.9967 | 0.9823 |
| **FNR (bỏ sót)** | 🥇 0.95% | 🥈 1.52% | 2.61% | 5.30% |
| **Tốc độ train** | 97.1s | 874.5s | 155.5s | 🥇 0.2s |
| **Tốc độ predict (toàn test set)** | 🥇 0.03s | 0.70s | 1.55s | 0.04s |
| **Giải thích được** | ✅ | ⚠️ Khó | ✅ | ✅ |
| **Cần scale?** | ✅ Có (bắt buộc) | ❌ Không | ❌ Không | ❌ Không |
| **Learning rate?** | ✅ Có | ✅ Có | ❌ Không | ❌ Không |

### So sánh LR với mô hình cũ (Random Forest)

| Metric | Random Forest (đang dùng) | Logistic Regression (thí nghiệm) | Chênh lệch |
|--------|---------------------------|----------------------------------|-----------|
| Accuracy | 97.23% | **99.02%** | LR hơn 1.79% |
| F1 | 97.23% | **99.02%** | LR hơn 1.79% |
| AUC | 0.9967 | **0.9992** | LR hơn 0.0025 |
| FNR | 2.61% | **0.95%** | LR bỏ sót ít hơn 2.7× |
| Predict (toàn test set) | 1.55s | **0.03s** | LR nhanh hơn ~50× |

### "LR tốt hơn mà sao vẫn chọn Random Forest?"

**Trả lời :**

**1. LR ổn hơn nhờ thêm 1 bước tiền xử lý mà RF không cần **

- RF chạy đúng ngay trên ma trận thưa, **không phụ thuộc bước chuẩn hóa** → pipeline ít điểm hỏng, phù hợp hệ thống nhiều thành phần (Telegram, LLM, Email Fetcher, Auto Monitor).

**2. RF cho xác suất trung thực hơn; LR dễ overconfident trên dữ liệu text.**

- Random Forest (RF) đánh giá xác suất sát với thực tế hơn, còn Logistic Regression (LR) dễ bị overconfident trên dữ liệu văn bản.

  Khi phải xử lý lượng từ vựng khổng lồ (lên tới 30.009 đặc trưng), LR có xu hướng đẩy kết quả dự đoán về hai thái cực: gần như 0% hoặc gần như 100%. Vì vậy, khi gặp những email có nội dung mới lạ, khác với dữ liệu lúc học LR vẫn có thể báo độ tin cậy lên tới 99% nhưng thực chất lại dự đoán sai hoàn toàn.

**3. Chuyển đổi vs lợi ích **

- Chuyển LR đòi hỏi: build lại pipeline (scaler + model lưu cùng 1 file), retrain, test lại toàn bộ tích hợp (orchestrator, Telegram, LLM, monitor), đo lại FPR/FNR hệ thống.
- Lợi ích 1,79% F1 trong khi RF 97,23% **đã vượt ngưỡng đồ án và đang chạy ổn định** → giữ RF, ghi nhận LR là **kết quả thí nghiệm và hướng nâng cấp** cho báo cáo sau.

### KẾT LUẬN TRONG BÁO CÁO

```
"so sánh 4 mô hình trên cùng dataset 204K email, cùng 30.009
features, cùng cách chia 80/20. Logistic Regression đạt F1 cao nhất
(99,02%) — kết quả này em ghi nhận và giải thích: TF-IDF tuyến tính
nên LR tìm đường phân cách tối ưu.

Tuy nhiên em GIỮ Random Forest làm mô hình vận hành vì 3 lý do:
 (1) RF không phụ thuộc bước MaxAbsScaler — LR đã từng sụp xuống
      52,4% khi thiếu scaler, rủi ro pipeline thật;
 (2) hệ thống là hybrid (max điểm ML, điểm heuristic) nên FNR thật
      của hệ thống thấp hơn FNR mô hình đơn lẻ — chênh 1,79% không
      phản ánh kết quả cuối;
 (3) RF cho xác suất trung thực hơn qua trung bình 200 cây, ít
      overconfident khi gặp dữ liệu ngoài phân phối.

LR được giữ làm hướng nâng cấp: nếu có thời gian, tích hợp LR +
MaxAbsScaler thành pipeline 1 file và đo lại toàn bộ hệ thống."
```

### 



```
→ CHUYỂN sang Logistic Regression (99,02%)
→ Cần: pipeline Pipeline([("tfidf",...), ("scale", MaxAbsScaler), ("clf", LR)])
        lưu scaler + model trong CÙNG một file .pkl
→ Lợi: chính xác hơn 1,79%, FNR thấp hơn 2.7×
→ Bắt buộc: test lại toàn bộ tích hợp + đo FPR/FNR ở ngưỡng 60%
```

---

## D8. Quá trình train (chi tiết trong `scripts/train_ml_model.py`)

### Lệnh chạy
```powershell
cd D:\TLCN
python scripts/train_ml_model.py
```

### Input/Output
```python
# Dòng 30 — Input:
INPUT_CSV = "data_train/processed/merged_clean.csv"   (206,722 email)

# Dòng 31 — Output:
MODEL_PATH = "app/models/phishing_rf.pkl"             (file model đã train)
```

### 7 bước chi tiết
```
BƯỚC 1: ĐỌC DỮ LIỆU (dòng 52)
   pd.read_csv("merged_clean.csv")
   → 206,722 email, 7 cột

BƯỚC 2: LÀM SẠCH (dòng 58-59)
   df.dropna(subset=["subject", "body", "label"])  → bỏ dòng thiếu
   df["label"].astype(int)                          → chuẩn hóa nhãn 0/1

BƯỚC 3: GỘP TEXT (dòng 34-44, combine_text)
   Mỗi email → 1 chuỗi:
   "Sender: admin@bank.com
    Subject: Verify your password
    URLs: http://bit.ly/xyz
    Body: Click here to login..."

BƯỚC 4: CHIA 80/20 (dòng 90-96)
   train_test_split(test_size=0.2, stratify=labels, random_state=42)
   → 165,377 train / 41,345 test

BƯỚC 5: TRÍCH ĐẶC TRƯNG (dòng 66-73)
   TF-IDF (30,000 cột) + Security (9 số) → vector 30,009 chiều

BƯỚC 6: TRAIN (dòng 97)
   pipeline.fit(x_train, y_train)
   → 200 cây Random Forest "học" từ 165,377 email

BƯỚC 7: ĐÁNH GIÁ + LƯU (dòng 98-107)
   pipeline.predict(x_test)    → dự đoán trên test
   classification_report()     → in Precision, Recall, F1
   joblib.dump(pipeline)       → lưu .pkl (~50MB)
```

### Kết quả thực tế khi train RF
```
              precision    recall  f1-score   support
           0     0.9762    0.9709    0.9735     21409
           1     0.9681    0.9739    0.9710     19450
    accuracy                         0.9723     40859

Da luu model tai: app/models/phishing_rf.pkl
Thoi gian train: ~5 phut
```

---

## D9. Các lệnh chạy ML riêng (không cần mở app)

| Lệnh | Mục đích | Thời gian |
|------|----------|-----------|
| `python scripts/merge_datasets.py` | Gộp 11 dataset → CSV sạch | ~3 phút |
| `python scripts/train_ml_model.py` | Train model → .pkl | ~5 phút |
| `python scripts/test_binary.py` | Test nhanh đầu ra nhị phân | ~5 giây |
| `python scripts/compare_models.py` | So sánh 4 mô hình | ~20 phút |
| `python scripts/check_duplicates.py` | Kiểm tra trùng lặp + tạo file mẫu | ~1 phút |
| `python scripts/run_auto_monitor.py --once` | Quét Gmail + gửi Telegram | ~10 giây |

### Luồng chạy đầy đủ (reset từ đầu)
```powershell
cd D:\TLCN
python scripts/merge_datasets.py      # Bước 1: Gộp dataset
python scripts/train_ml_model.py      # Bước 2: Train model
python scripts/test_binary.py         # Bước 3: Test
python -m streamlit run app/main.py   # Bước 4: Chạy app UI
```

### Lưu ý: Train vs Predict
- **Train:** Chạy tay `train_ml_model.py`, tạo `phishing_rf.pkl` (~5 phút)
- **Predict:** Mỗi lần upload email trên UI, **chỉ load .pkl và dự đoán** (< 1s), KHÔNG train lại

---

# PHẦN E — ĐÁNH GIÁ MÔ HÌNH

## E1. Ma trận nhầm lẫn (Confusion Matrix)

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

## E2. Các công thức đánh giá

**False Positive Rate (FPR) — Tỷ lệ Âm tính giả:**
```
FPR = FP / (FP + TN)

- FP = email hợp lệ nhưng bị đoán là phishing (báo động giả)
- TN = email hợp lệ và bị đoán đúng là hợp lệ
```

**False Negative Rate (FNR) — Tỷ lệ Dương tính giả:**
```
FNR = FN / (FN + TP)

- FN = email phishing nhưng bị đoán là hợp lệ (bỏ sót)
- TP = email phishing và bị đoán đúng là phishing
```

**Accuracy:**
```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

**Precision:**
```
Precision = TP / (TP + FP)
```

**Recall:**
```
Recall = TP / (TP + FN) = 1 - FNR
```

**F1-Score:**
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

## E3. Kết quả RF thực tế (dataset 206K)

```
Test set: 40,859 email (20% của 206,722)

- TP = 18,943 (bắt đúng phishing)
- FN = 507   (bỏ sót phishing)     ← FNR
- FP = 623   (báo động giả)         ← FPR
- TN = 20,786 (nhận đúng hợp lệ)

FNR = 507 / (507 + 18,943) = 507/19,450 = 2.61%
FPR = 623 / (623 + 20,786) = 623/21,409 = 2.91%
Accuracy = (18943+20786)/40859 = 39,729/40,859 = 97.23%
Precision = 18943 / 19566 = 96.81%
Recall = 18943 / 19450 = 97.39%
F1 = 2 × (96.81 × 97.39)/(96.81 + 97.39) = 97.10%
```

## E4. Confusion Matrix chi tiết (RF)

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

## E5. Bảng các chỉ số chi tiết (RF)

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

## E6. Ý nghĩa quan trọng

- **FNR cao** = NGUY HIỂM: email phishing lọt lưới → user bị lừa
- **FPR cao** = PHIỀN: email hợp lệ bị chặn → user khó chịu
- **Trong security: FNR quan trọng hơn FPR** (bỏ sót phishing nguy hiểm hơn báo động giả)

## E6b. ROC Curve & AUC — lý thuyết so sánh 4 mô hình

### ROC là gì?

**ROC** (Receiver Operating Characteristic) là đường cong vẽ trên đồ thị **TPR (True Positive Rate) vs FPR (False Positive Rate)**, với mọi ngưỡng phân loại từ 0% đến 100%. Ý nghĩa: nếu kéo ngưỡng từ thấp lên cao, mô hình tốt sẽ **nhanh chóng lên góc trên bên trái** (bắt được nhiều phishing thật trong khi chỉ báo oan rất ít email hợp lệ).

```
TPR (Recall)
  1.0 ┤••••••••••••••••••••••╲
      │                       ╲  ← Mô hình tốt
      │                        ╲    (đường cong đẩy lên góc trên trái)
      │    ·  ·  ·  ·  ·  ·  · · · · ·  ← Mô hình ngẫu nhiên (đường chéo)
      │  ╱
  0.0 ┤╱________________________________
      0.0                              1.0
                FPR (False Positive Rate)
```

- **Đường chéo nét đứt** = mô hình đoán ngẫu nhiên (AUC = 0.5).
- **Đường cong đẩy mạnh lên trên trái** = mô hình tốt (AUC gần 1.0).

### AUC là gì?

**AUC** (Area Under Curve) = **diện tích dưới đường cong ROC**, một số từ 0.0 đến 1.0. AUC cao nghĩa là mô hình **xếp hạng đúng thứ tự nguy cơ**: email phishing thật luôn nhận điểm cao hơn email hợp lệ. Đây là chỉ số **không phụ thuộc ngưỡng** — điểm mạnh lớn nhất của nó khi so sánh mô hình.

| Khoảng AUC | Đánh giá |
|------------|----------|
| 0.9 – 1.0 | **Xuất sắc** (4 mô hình của đồ án đều nằm trong khoảng này) |
| 0.8 – 0.9 | Tốt |
| 0.7 – 0.8 | Trung bình |
| < 0.7 | Kém |

### Cách so sánh AUC 4 mô hình (kết quả thực nghiệm)

| Mô hình | AUC | Xếp hạng | Đọc từ biểu đồ |
|---------|-----|----------|----------------|
| **Logistic Regression** | **0.9992** | 🥇 | Đường đỏ — lên đỉnh gần nhất, sát trục |
| XGBoost | 0.9983 | 🥈 | Đường cam — gần trùng LR |
| Random Forest | 0.9967 | 🥉 | Đường xanh dương — mô hình vận hành |
| Multinomial Naive Bayes | 0.9823 | 4 | Đường xanh lá — thấp nhất nhưng vẫn "xuất sắc" |

Biểu đồ: `results/roc_comparison.png` (4 đường ROC + đường chéo ngẫu nhiên AUC=0.5).

Từ biểu đồ ROC, ta đọc được AUC từng mô hình. AUC cao nhất = mô hình **xếp hạng phishing/legit tốt nhất** — đó là tiêu chí quan trọng thứ hai sau F1 khi chọn mô hình cho hệ thống bảo mật. Chênh AUC giữa LR và RF chỉ **0,0025** — rất nhỏ, đủ căn cứ để ưu tiên tiêu chí vận hành (không cần scaler, xác suất trung thực) mà chọn RF (xem D7).

> **Lưu ý khi trả lời cô:** AUC đánh giá khả năng **xếp hạng** còn F1 đánh giá tại **một ngưỡng cụ thể** (60%). Hệ thống dùng F1/FNR/FPR ở ngưỡng 60% để ra quyết định, nhưng AUC cho biết **nếu đổi ngưỡng thì mô hình còn bao nhiêu tiềm năng** — nên AUC và F1 cần đọc cùng nhau.

## E6c. Ma trận nhầm lẫn — hiển thị trong chương trình

### Cách xem ma trận nhầm lẫn từ chương trình

Ma trận nhầm lẫn **không in text trong báo cáo**, mà được **vẽ trực tiếp bởi chương trình** dưới dạng heatmap rồi hiển thị trong app để chụp màn hình chèn vào báo cáo:

```
Cách thực hiện:
1. Chạy:  python scripts/compare_models.py
   → Script tự lưu 4 file PNG:
       results/confusion_matrix_rf.png
       results/confusion_matrix_lr.png
       results/confusion_matrix_mnb.png
       results/confusion_matrix_xgb.png
2. Mở app:  streamlit run app/main.py
   → Click tab "Danh gia mo hinh" trên thanh tab
   → Hiển thị: bảng chỉ số, biểu đồ ROC, 4 ma trận nhầm lẫn
3. Chụp màn hình tab "Danh gia mo hinh" → chèn vào báo cáo Word
```

### Ý nghĩa từng ô trên heatmap

| Ô | Ý nghĩa | Mức độ nghiêm trọng |
|----|---------|---------------------|
| **TN** (xanh đậm) | Email hợp lệ → hệ thống nói "Not Phishing" ✓ | ✅ Tốt |
| **TP** (xanh đậm) | Email phishing → hệ thống nói "Phishing" ✓ | ✅ Tốt |
| **FP** (xanh nhạt) | Email hợp lệ → bị báo oan "Phishing" | ⚠️ Trung bình — gây phiền |
| **FN** (xanh nhạt) | Email phishing → bị bỏ qua "Not Phishing" | 🔴 Nguy hiểm nhất — bỏ sót |

### Cách đọc heatmap khi trình bày

> *"Ô xanh đậm phía trên bên trái là TN — hệ thống nhận đúng email hợp lệ. Ô xanh đậm dưới cùng bên phải là TP — hệ thống bắt đúng email phishing. Hai ô nhạt là lỗi: FP (báo oan) và FN (bỏ sót). Trong security, FN là quan trọng nhất vì email phishing lọt lưới sẽ khiến người dùng bị lừa — đó là lý do em chọn ngưỡng 60% thay vì 70%, để giữ FNR ở mức chấp nhận được."*

## E7. Ngưỡng 60% (Quyết định nhị phân)

### Tại sao chọn ngưỡng 60%?

**Bối cảnh:** Ngưỡng 50% là mặc định của binary classification nhưng là **ngưỡng "cân bằng" cho nghiên cứu**, không phải ngưỡng tối ưu cho **hệ thống cảnh báo đang vận hành**. Em đã chạy thí nghiệm lấy số liệu thật (`scripts/threshold_analysis.py`, RF + guardrail heuristic, test set 40.859 email):

### Số liệu thật: 4 ngưỡng trên cùng test set

| Ngưỡng | Accuracy | FNR (bỏ sót phishing) | FPR (báo giả) | Số email legit bị báo oan |
|--------|----------|------------------------|---------------|---------------------------|
| 50% | 96.89% | 2.57% (500 email) | 3.61% | **772** |
| **60% (CHỌN)** | **95.68%** | **7.53%** (1.465 email) | **1.40%** | **300** |
| 70% | 91.17% | 18.16% (3.532 email) | 0.36% | 77 |
| 80% | 83.79% | 33.98% | 0.07% | 16 |

*(File: `results/threshold_analysis.csv` — gồm cả RF đơn lẻ và LR ở đủ 4 ngưỡng)*

### 4 lý do chọn 60%

1. **Ngưỡng 50% gây "alert fatigue" — kẻ thù của hệ thống cảnh báo:**
   - Ở 50%: **772 email hợp lệ** bị gắn PHISHING và gửi cảnh báo Telegram thật.
   - Người dùng nhận cảnh báo giả liên tục sẽ bắt đầu **bỏ qua mọi cảnh báo** → email phishing thật đến sau cũng bị phớt lờ. Đây là thất bại cổ điển của hệ thống DLP/SOC.
   - Lên 60%: số báo giả giảm **61%** (772 → 300).

2. **Ngưỡng 70% bỏ sót quá nhiều — không chấp nhận được với security:**
   - Ở 70%: FNR nhảy vọt lên **18.16%** — 3.532 email phishing lọt lưới (gấp 7× so với 50%).
   - Đường cong trade-off có **điểm gãy (elbow)** giữa 60% và 70%: FNR đổi từ 7.53% → 18.16% (mất gấp đôi) trong khi FPR chỉ cải thiện thêm 1 điểm phần trăm. → Vượt 60% là "mua" báo giả rất đắt.

3. **Guardrail heuristic bù đắp phần bỏ sót ở vùng ranh giới (50–60%):**
   - `điểm cuối = max(điểm ML, điểm heuristic)`: email có **tín hiệu lừa đảo thật** (từ khóa "urgent/verify/password" + URL bit.ly/giả mạo ngân hàng) sẽ bị heuristic kéo điểm lên trên 60 dù ML chỉ cho 5x%.
   - Email **thực sự mơ hồ** (không đủ tín hiệu từ cả hai nguồn) thì việc không cảnh báo là hợp lý — đó là email cần con người đọc, không phải email lọt lưới.

4. **Thống nhất toàn hệ thống ở 60%:** ngưỡng DUY NHẤT dùng ở mọi nơi — ML label, heuristic label, orchestrator `risk_level()`, UI, Telegram, LLM prompt, Email Fetcher, Auto Monitor. Có `test_binary.py` kiểm chứng: **59 → Not Phishing, 60 → Phishing**.

### Quyết định nhị phân
```
ĐIỂM CUỐI              KẾT LUẬN            LABEL
──────────────────────────────────────────────────
0  - 59                 NOT PHISHING        0     (không bị)
60 - 100                PHISHING            1     (bị)
```

### Cách trả lời khi hỏi: "Tại sao không phải 50% hay 70%?"
> **A:** "Dạ, 50% là mặc định lý thuyết nhưng em đã thí nghiệm 4 ngưỡng trên test set 40.859 email. Ở ngưỡng 50% có 772 email hợp lệ bị báo oan — báo giả tích tụ sẽ làm người dùng bỏ qua cảnh báo thật. Còn 70% thì bỏ sót 18% phishing, gấp 7 lần ngưỡng 50%, em thấy không an toàn. 60% là điểm cân bằng: báo giả giảm 61% còn bỏ sót giữ ở mức 7,5% — và phần bỏ sót này được tầng heuristic (max điểm ML, điểm rules) bù đắp, vì email lừa đảo thật thường có từ khóa khẩn cấp + URL giả mạo nên heuristic sẽ kéo điểm lên trên 60. Toàn bộ code thống nhất ngưỡng duy nhất 60%, có test 59/60 kiểm chứng."

---

# PHẦN F — HỆ THỐNG HYBRID & LLM

## F1. Pipeline hệ thống 6 bước

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

| Bước | Công việc | Đầu ra |
|------|-----------|--------|
| 1. Parsing | Đọc file .eml/.txt, trích header (From, To, Subject, Date) | Raw email fields |
| 2. Preprocessing | Loại bỏ HTML tags, decode base64, normalize text | Text sạch |
| 3. Feature Extraction | TF-IDF vectorization + 9 security features | Feature vector |
| 4. ML Classification | Classifier dự đoán xác suất phishing | Score 0–100 |
| 5. LLM Analysis | Gemini phân tích ngữ cảnh, social engineering | Báo cáo text |
| 6. Decision & Alert | **Nhị phân: Phishing / Not Phishing** → Alert → Telegram | **Có/Không** |

### Flow chi tiết trong code
```
File .eml/.txt
    ↓
parse_uploaded_email()           [orchestrator.py]
    ↓
predict_phishing()               [ml_engine.py]
    ├── TF-IDF Vectorizer (30K features)
    ├── SecurityFeatureExtractor (9 features)
    ├── Classifier.predict_proba() → ML_SCORE
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

## F2. Căn cứ tính điểm rủi ro

### Công thức tổng
```
ĐIỂM CUỐI = max(ML_SCORE, HEURISTIC_SCORE)

Trong đó:

1. ML_SCORE (từ mô hình):
   - predict_proba(text) → xác suất class 1
   - ml_score = probability × 100

2. HEURISTIC_SCORE (rules-based):
   base = 8
   + min(matched_keywords × 8, 48)    // từ khóa đáng ngờ
   + min(url_count × 8, 24)           // số URL
   + min(suspicious_url × 15, 30)     // URL đáng ngờ
   = score 0-95
```

### Ví dụ heuristic score
```
Email có:
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

### Tại sao dùng max(ML, heuristic)?
```
TRƯỜNG HỢP 1: ML đúng (score cao)
- ML = 85, Heuristic = 40 → max = 85 → Đúng (tin ML)

TRƯỜNG HỢP 2: ML sai (miss), Heuristic bắt được
- ML = 30 (model không recognize mẫu mới)
- Heuristic = 75 (keywords + URLs rõ ràng)
- max = 75 → >= 60 → Phishing (heuristic cứu - GUARDRAIL)

TRƯỜNG HỢP 3: Cả hai đều thấp
- ML = 25, Heuristic = 30 → max = 30 → < 60 → Not Phishing

TRƯỜNG HỢP 4: Cả hai đều cao
- ML = 90, Heuristic = 85 → max = 90 → Phishing
```

### Ví dụ hoàn chỉnh
```
Email: "URGENT: Verify your password now!"  "Click: http://bit.ly/xyz"

Bước 1 - ML_SCORE:
  Model: 170/200 cây nói phishing → ML = 0.85 × 100 = 85

Bước 2 - HEURISTIC_SCORE:
  base = 8
  keywords: urgent, verify, password → 3 × 8 = 24
  urls: 1 URL → 1 × 8 = 8
  suspicious: bit.ly → 1 × 15 = 15
  → HEURISTIC = 8 + 24 + 8 + 15 = 55

Bước 3 - ĐIỂM CUỐI:
  max(85, 55) = 85

Bước 4 - ĐẦU RA NHỊ PHÂN:
  85 >= 60 → PHISHING (label = 1) → Gửi Telegram cảnh báo
```

---

## F3. Đầu ra thống nhất nhị phân 

> **"Thống nhất đầu ra là có hoặc không, là bị email phishing hoặc không bị"**

**ĐẦU RA CHỈ CÓ 2 GIÁ TRỊ:**
```
┌─────────────────────────────────────────┐
│   PHISHING     (bị)     → label = 1     │
│   NOT PHISHING (không bị) → label = 0  │
│   Ngưỡng: score >= 60 → PHISHING       │
│           score <  60 → NOT PHISHING   │
└─────────────────────────────────────────┘
```

**Tại sao nhị phân thay vì 3 mức?**
- Thống nhất trong toàn bộ hệ thống
- Dễ đánh giá (binary classification)
- Dễ tích hợp hệ thống bên ngoài
- Phù hợp yêu cầu của cô

**Thống nhất trong toàn bộ code:**

| Thành phần | Trước | Sau |
|------------|-------|-----|
| `orchestrator.risk_level()` | 3 mức (An toan/Dang ngo/Nguy hiem) | **2 mức (Phishing/Not Phishing)** |
| `ml_engine.label` | `score >= 55` | **`score >= 60`** |
| `main.show_risk()` | 3 màu (xanh/vàng/đỏ) | **2 màu (đỏ = Phishing, xanh = Not)** |
| `telegram_notifier` | NGUY HIEM/DANG NGO/AN TOAN | **PHISHING/NOT PHISHING** |
| `llm_agent` prompt | "An toan / Dang ngo / Nguy hiem" | **"PHISHING / NOT PHISHING"** |
| `system_prompt` | 3 mức | **Nhị phân, ngưỡng 60** |
| `email_fetcher` ngưỡng | 55 | **60** |

---

## F4. Mô hình LLM đang sử dụng

### Thông số
| Thông số | Giá trị |
|----------|---------|
| **Tên mô hình** | **Google Gemini** (gemini-3.6-flash / 3.7-flash) |
| Nhà phát triển | Google DeepMind |
| Kiến trúc | Transformer (multi-modal) |
| API | google-genai SDK v2.0+ |
| Temperature | 0.2 (thấp → kết quả ổn định) |
| System Instruction | Custom prompt "Phishing Analyst Agent" |

### Cơ chế Transformer Attention
```
Attention(Q, K, V) = softmax(QK^T / √d_k) × V

- Q (Query): Câu hỏi của model (context email)
- K (Key): Thông tin tham chiếu (ML score, URLs)
- V (Value): Nội dung cần trích xuất
- √d_k: Scaling factor tránh gradient quá lớn
```

### Quy trình LLM phân tích
```
1. Input Construction: System Prompt + Context (email + ML score)
2. Tokenization: Text → Tokens → Embeddings (vector)
3. Forward Pass: Qua nhiều layer Transformer
4. Decoding: temperature=0.2 → câu trả lời ổn định
5. Output: PHISHING / NOT PHISHING + Điểm + Bằng chứng
```

### Tại sao temperature = 0.2?
```
temperature < 1 → Ưu tiên token có xác suất cao nhất
temperature = 0.2 → Rất ổn định, ít "bịa"
temperature > 1 → Sáng tạo hơn nhưng có thể sai

Với security analysis → cần chính xác → temperature thấp
```

### Kết hợp ML + LLM
```
                ML (Classifier)              LLM (Gemini)
Điểm mạnh:      - Nhanh (< 1ms)              - Hiểu ngữ cảnh
                - Nhất quán                  - Giải thích được
                - Không tốn API cost          - Xử lý biến thể mới
Điểm yếu:       - Không hiểu ngữ cảnh        - Chậm (1-3s)
                - Cứng nhắc                   - Tốn API cost
                - Cần dataset lớn            - Có thể "bịa"

→ KẾT HỢP: ML cho điểm nhanh + LLM cho giải thích sâu
```

---

# PHẦN G — DẤU HIỆU PHISHING & TÀI LIỆU THAM KHẢO

## G1. Phân loại dấu hiệu theo lý thuyết

### A. Dấu hiệu NGÔN NGỮ (Linguistic Indicators)
| Dấu hiệu | Ví dụ | Lý thuyết |
|-----------|-------|-----------|
| Tính cấp bách | "urgent", "within 24 hours", "khẩn cấp" | Tạo áp lực thời gian → victim không suy nghĩ kỹ |
| Đe dọa | "account suspended" | Fear appeal → kích hoạt phản xạ sợ hãi |
| Phần thưởng | "you won $1000", "free gift" | Greed appeal → đánh lừa lý trí |
| Yêu cầu thông tin | "verify your password", "confirm your SSN" | Credential theft → mục đích chính |
| Sai chính tả | "recieve", "verfy" | Thấp chất lượng → phishing thường có lỗi |

### B. Dấu hiệu KỸ THUẬT (Technical Indicators)
| Dấu hiệu | Công thức phát hiện | Lý thuyết |
|-----------|---------------------|-----------|
| URL đáng ngờ | Regex: `https?://[^\s]*bit\.ly[^\s]*` | URL shortener che giấu đích |
| IP thay domain | Regex: `https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | Phishing dùng IP trực tiếp |
| Domain sai | `@` trong URL: `http://good.com@evil.com` | Visual trick |
| Gạch nối nhiều | `http://paypal-secure-login.com` | Typosquatting |
| TLD đáng ngờ | `.ru`, `.zip`, `.tk` | TLD rẻ/miễn phí |

### C. Dấu hiệu HEADER (Metadata Indicators)
| Dấu hiệu | Ý nghĩa |
|-----------|---------|
| Sender domain khác brand | "paypal.com" vs "paypal-secure.ru" |
| Reply-To khác From | Phishing đánh lừa reply |
| SPF/DKIM fail | Không xác thực được sender |
| Date bất thường | Thời gian gửi odd (2-3 giờ sáng) |

---

## G2. Tài liệu / Báo cáo liên quan

### Dataset đã sử dụng (Trích dẫn chuẩn)

> **Champa, A. I., Rabbi, M. F., & Zibran, M. F.** (2024). Curated datasets and feature analysis for phishing email detection with machine learning. *2024 IEEE 3rd International Conference on Computing and Machine Intelligence (ICMI)*, pp. 1–7. DOI: `10.6084/m9.figshare.25432108`

**Bài báo thứ 2 (11 datasets đầy đủ):**
> **Champa, A. I., Rabbi, M. F., & Zibran, M. F.** (2024). Why phishing emails escape detection: A closer look at the failure points. *2024 12th IEEE International Symposium on Digital Forensics and Security (ISDFS)*. Kho 11 datasets: DOI `10.6084/m9.figshare.24952503`

**Link xác thực (cấp bài báo / kho dữ liệu):**
- **Bài báo IEEE:** https://ieeexplore.ieee.org/document/10585821
- **Kho 7 Datasets (Figshare):** https://doi.org/10.6084/m9.figshare.25432108
- **Kho 11 Datasets (Figshare):** https://doi.org/10.6084/m9.figshare.24952503
- **Zenodo (tổng hợp):** https://doi.org/10.5281/zenodo.8339691

**Tác giả:**
| Tác giả | Tổ chức | Xác thực |
|---------|---------|----------|
| Arifa Islam Champa | Idaho State University | IEEE Xplore profile |
| Md Fazle Rabbi | Idaho State University | Tác giả đồng nghiệp |
| Minhaz F. Zibran | Idaho State University | Trưởng nhóm nghiên cứu |

**BibTeX:**
```bibtex
@inproceedings{champa2024curated,
  title     = {Curated Datasets and Feature Analysis for Phishing Email Detection with Machine Learning},
  author    = {Champa, Arifa I and Rabbi, Md Fazle and Zibran, Minhaz F},
  booktitle = {2024 IEEE 3rd International Conference on Computing and Machine Intelligence (ICMI)},
  pages     = {1--7},
  year      = {2024},
  doi       = {10.6084/m9.figshare.25432108}
}
```

**Link 11 dataset nguồn (nguồn gốc thô, do Champa et al. trích xuất):**

| Dataset | Tổ chức gốc | Link xác thực |
|---------|-------------|---------------|
| CEAS_08 | University of Waterloo | https://ceas.cc/2008/ · https://plg.uwaterloo.ca/~gvcormac/ceascorpus/ |
| Enron | Carnegie Mellon University | https://www.cs.cmu.edu/~enron/ |
| Ling | Athens Univ. of Economics & Business | https://arxiv.org/abs/cs/0008019 |
| Nazario | Arbor Networks | https://monkey.org/~jose/phishing/ |
| Nigerian_Fraud | University of Michigan (CLAIR Lab) | https://www.kaggle.com/datasets/rtatman/fraudulent-email-corpus |
| SpamAssasin | Apache Foundation | https://spamassassin.apache.org/old/publiccorpus/ |
| TREC_05/06/07 | NIST + University of Waterloo | https://trec.nist.gov/data/spam.html |

### Báo khoa học quốc tế
| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | **Verizon DBIR 2024** | 91% cyberattack bắt đầu từ phishing |
| 2 | **APWG Phishing Activity Trends Report 2024** | Thống kê phishing toàn cầu |
| 3 | **FBI IC3 Report 2023** | Thiệt hại 12.5 tỷ USD từ phishing |
| 4 | **NIST SP 800-177** | Hướng dẫn email authentication |

### Nghiên cứu ML + Phishing
| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | "Curated Datasets and Feature Analysis..." (IEEE ICMI, 2024) | **Dataset đang dùng** |
| 2 | "Phishing Email Detection Using ML" (IEEE, 2020) | So sánh RF, SVM, NB |
| 3 | "BERT-based Phishing Email Detection" (2021) | Dùng NLP transformer |
| 4 | "A Survey on Phishing Attacks and Detection" (ACM, 2022) | Tổng quan toàn diện |
| 5 | "Hybrid Phishing Detection using ML and LLM" (2023-2024) | Gần giống đề tài này |

### Tài liệu tiếng Việt
| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | Báo cáo VNCERT 2024 | Tình hình an ninh mạng Việt Nam |
| 2 | Nghiên cứu ĐHQGHN về spam detection | Áp dụng ML cho email tiếng Việt |
| 3 | Công văn Bộ TT&TT về chống phishing | Chính sách quản lý |

### Chuẩn & Framework
| STT | Tài liệu | Nội dung |
|-----|----------|----------|
| 1 | OWASP Top 10 2021 | Phishing là social engineering |
| 2 | MITRE ATT&CK T1566 | Kiến thức tấn công phishing |
| 3 | RFC 7208 (SPF), RFC 6376 (DKIM) | Chuẩn xác thực email |

---

# PHẦN H — CÂU HỎI  (Q&A)

> **Mục này tổng hợp các câu hỏi cô đã hỏi / có thể hỏi** + câu trả lời mẫu. Đặt ở cuối để tiện ôn tập.

## H1. Về dataset

### Q1: "Tại sao chọn dataset này?"
> **A:** Paper IEEE ICMI 2024 (kho Figshare chính thức: DOI 10.6084/m9.figshare.25432108), Idaho State University, IEEE Xplore. Gộp 11 nguồn uy tín (Waterloo, CMU, Apache, NIST, Michigan). 206K email cân bằng 47.7/52.3.

### Q2: "Nguồn gốc 11 dataset có uy tín không?"
> **A:** Tất cả từ tổ chức top:
> - **University of Waterloo** (Canada) — CEAS, TREC
> - **Carnegie Mellon University** (USA) — Enron
> - **Apache Foundation** — SpamAssassin
> - **NIST** (USA) — TREC
> - **Arbor Networks** — Nazario

### Q3: "Dữ liệu có label đúng không?"
> **A:** Label từ 2 nguồn: (1) Spam feed thật (TREC, SpamAssassin) — người dùng report; (2) Phishing corpus thật (Nazario, Nigerian Fraud) — chuyên gia thu thập. Có 5-10% sai lệch (label noise), nhưng model vẫn đạt 97.23% accuracy.

### Q4: "Làm sao verify dataset?"
> **A:** (1) Kho chính thức trên Figshare: https://doi.org/10.6084/m9.figshare.24952503 (2) Bài báo IEEE: https://ieeexplore.ieee.org/document/10585821 (3) Zenodo tổng hợp: https://doi.org/10.5281/zenodo.8339691 (4) Nguồn gốc thô từng dataset: xem Phần A3.

### Q5: "Tại sao Enron/Ling thiếu sender/date?"
> **A:** Đây là **giới hạn gốc** của dataset (không phải lỗi xử lý). 6/11 file có đủ 7 cột, còn lại thiếu metadata. Đã dùng cột default rỗng.

---

## H2. Về tiền xử lý & trùng lặp

### Q6: "Dữ liệu có bị trùng lặp không? Nếu trùng thì tỉ lệ học sẽ ảo?"
> **A:** Em đã kiểm tra bằng script `check_duplicates.py`:
> - Trùng hoàn toàn (7 cột): **0 dòng (0.00%)**
> - Trùng subject+body: **0 dòng (0.00%)**
> - Label mâu thuẫn: **0 nhóm**
> - Trùng sender+subject+date: 9,744 dòng (4.71%) nhưng body KHÁC nhau (chuỗi email cùng thread) → không phải trùng lặp
>
> **Kết luận:** 206,722 email đều duy nhất → Accuracy là thật, không bị ảo do trùng lặp.

### Q7: "Có data leakage không?"
> **A:** Không. Đã kiểm tra: (1) Dedup trước khi split (bỏ 10,509 email trùng); (2) Split 80/20 stratified; (3) TF-IDF fit trên train set, transform test set (không fit trên test).

### Q8: "Tại sao chia 80% train / 20% test?"
> **A:** Mô hình chỉ được học trên train và đánh giá trên test chưa từng thấy. 80/20 là chuẩn ngành: test 41K email đủ lớn để đánh giá tin cậy, train 165K đủ để học. Dùng stratify để giữ tỉ lệ label, random_state=42 để tái lập.

---

## H3. Về mô hình & train

### Q9: "Train sao? File nào? Model nào?"
> **A:** Train bằng `scripts/train_ml_model.py`. Model gồm 2 phần: TF-IDF (30,000 features) + 9 Security Features → feed vào classifier (RF/LR). Input là `merged_clean.csv` 206K email, output lưu `phishing_rf.pkl`. Chia 80/20 stratified, train ~5 phút.

### Q10: "Learning rate là bao nhiêu?"
> **A:** Random Forest **KHÔNG có learning rate** (học độc lập, vote). Learning rate là tham số của mô hình gradient boosting (XGBoost: learning_rate=0.1) hoặc LR (bước nhảy gradient descent). Thay learning rate, RF dùng `max_depth=30` (chống overfit) và `n_estimators=200`.

### Q11: "Đã so sánh những mô hình nào? Mô hình nào tốt nhất?"
> **A:** Em chạy 4 mô hình trên cùng dataset/features/split:
>
> | # | Mô hình | F1 | AUC | Train | Predict |
> |---|---------|-----|-----|-------|---------|
> | 1 | **Logistic Regression** | **99.02%** | **0.9992** | 97.1s | **0.03s** |
> | 2 | XGBoost | 98.27% | 0.9983 | 874.5s | 0.70s |
> | 3 | Random Forest | 97.23% | 0.9967 | 155.5s | 1.55s |
> | 4 | Naive Bayes | 95.28% | 0.9823 | **0.2s** | 0.04s |
>
> **Logistic Regression thắng** vì features TF-IDF tuyến tính. XGBoost chính xác cao nhưng train ~15 phút. Naive Bayes nhanh nhưng yếu (giả định các từ độc lập). Biểu đồ ROC: `results/roc_comparison.png`; ma trận nhầm lẫn 4 model: xem tab "Danh gia mo hinh" trong app.

### Q12: "Tại sao LR đầu tiên chỉ được 52%?"
> **A:** Vì chưa scale dữ liệu. TF-IDF cho giá trị 0-1 nhưng 9 Security Features có thể rất lớn (text_length > 10,000). Saga solver không hội tụ khi scale khác nhau → dự đoán tất cả là legit (FNR=100%). Thêm MaxAbsScaler → LR đạt 99.02%. **Bài học: feature scaling rất quan trọng với mô hình tuyến tính.**

---

## H4. Về đánh giá & đầu ra

### Q13: "Tại sao ngưỡng 60% mà không phải 50%?"
> **A:** Dạ, em đã thí nghiệm 4 ngưỡng (50/60/70/80) trên test set 40.859 email. Ở 50% có 772 email hợp lệ bị báo oan — báo giả tích tụ sẽ làm người dùng bỏ qua cảnh báo thật (alert fatigue). Ở 70% thì bỏ sót 18% phishing, gấp 7 lần. 60% là điểm cân bằng: báo giả giảm 61% (còn 300), bỏ sót giữ 7,5% và được tầng heuristic (max điểm ML, điểm rules) bù đắp cho email lừa đảo thật. Toàn bộ code thống nhất ngưỡng duy nhất 60%, có test 59/60 kiểm chứng.

### Q14: "FPR/FNR quan trọng thế nào?"
> **A:** FNR (bỏ sót phishing) quan trọng HƠN FPR trong security — bỏ sót phishing khiến user bị lừa, còn FPR chỉ gây phiền. Ở mức mô hình đơn lẻ: RF FNR=2.61%, LR FNR=0.95%. Ở mức hệ thống vận hành (ngưỡng 60% + guardrail): FNR=7.53%, FPR=1.40% — chính vì FNR quan trọng nên phần bỏ sót ở vùng ranh giới được tầng heuristic `max(ML, heuristic)` bù đắp (xem E7).

### Q15: "Vì sao điểm 50% với 200 cây là 100 cây vote phishing?"
> **A:** Gần đúng. Chính xác hơn là trung bình xác suất của 200 cây: mỗi cây cho xác suất 0-1 (tỉ lệ phishing trong lá), rồi lấy trung bình. Trường hợp 100 cây = 1.0 và 100 cây = 0.0 → trung bình = 50%. Nhưng cũng có thể 200 cây đều = 0.5 → cũng ra 50%.

---

## H5. Câu trả lời mẫu (30 giây — cho phần thuyết trình)

> **Về dataset:** *"Dataset của em là bộ 11 Curated Datasets được chuẩn hóa 7 trường bởi nhóm TS. Minhaz F. Zibran và Arifa I. Champa (Idaho State University), công bố tại IEEE ICMI 2024 và IEEE ISDFS 2024, lưu trên Figshare (DOI 10.6084/m9.figshare.24952503). Các nguồn thô từ NIST+Waterloo (TREC), Carnegie Mellon (Enron), Apache (SpamAssassin). Tổng 206K email, phân bố 47.7% phishing / 52.3% legit. Em đã kiểm tra trùng lặp: 0 dòng trùng hoàn toàn → Accuracy không bị ảo."*

> **Về model:** *"Em đã so sánh 4 mô hình trên cùng dataset 204K email, cùng 30.009 features, cùng cách chia 80/20. Logistic Regression đạt F1 cao nhất 99,02% (TF-IDF tuyến tính nên LR tìm đường phân cách tối ưu) — kết quả này em ghi nhận đầy đủ trong báo cáo. Nhưng em giữ Random Forest (97,23%) làm mô hình vận hành vì: (1) LR chỉ thắng khi thêm MaxAbsScaler, thực nghiệm của em cho thấy thiếu bước đó LR sụp về 52,4% — pipeline thật nhiều bước thì mỗi bước là một rủi ro; (2) hệ thống là hybrid, điểm cuối = max(điểm ML, điểm heuristic) nên phần bỏ sót được tầng rules bù đắp, chênh 1,79% không ra tới kết quả cuối; (3) RF trung bình xác suất 200 cây nên không overconfident khi gặp dữ liệu lạ. LR được ghi nhận là hướng nâng cấp."*

> **Về ngưỡng:** *"Em không chọn ngưỡng theo lý thuyết mà theo số liệu: thí nghiệm 4 ngưỡng 50/60/70/80 trên test set 40.859 email. 50% thì 772 email hợp lệ bị báo oan, 70% thì bỏ sót 18% phishing. Chọn 60%: báo giả giảm 61% còn 300, bỏ sót 7,5% và được heuristic bù. Toàn bộ code thống nhất ngưỡng 60, có test 59/60."*

> **Về train:** *"Em train bằng scripts/train_ml_model.py, dùng TF-IDF 30,000 features + 9 Security Features, chia 80/20 stratified. Model lưu ra phishing_rf.pkl. Mỗi lần upload email, app chỉ load .pkl và dự đoán (<1s), không train lại."*

---

*File này là tài liệu tổng hợp — cần thêm nội dung nào, báo lại để bổ sung.*
