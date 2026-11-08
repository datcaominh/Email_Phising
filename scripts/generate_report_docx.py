# -*- coding: utf-8 -*-
"""Tao file Word Bao cao tien do lan 2 theo mau GV.

Doc ket qua tu results/model_comparison.csv (chay compare_models.py truoc).
Output: D:/TLCN/BaoCaoTienDo_Lan2.docx
"""

from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, Inches, RGBColor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_CSV = PROJECT_ROOT / "results" / "model_comparison.csv"
RESULTS_DIR = PROJECT_ROOT / "results"
CHART_PNG = PROJECT_ROOT / "results" / "model_comparison_chart.png"
ROC_PNG = RESULTS_DIR / "roc_comparison.png"
CM_PNGS = {
    "Random Forest": RESULTS_DIR / "confusion_matrix_rf.png",
    "Logistic Regression": RESULTS_DIR / "confusion_matrix_lr.png",
    "Multinomial Naive Bayes": RESULTS_DIR / "confusion_matrix_mnb.png",
    "XGBoost": RESULTS_DIR / "confusion_matrix_xgb.png",
}
OUTPUT_DOCX = PROJECT_ROOT / "BaoCaoTienDo_Lan2.docx"


# ---------------------------------------------------------------------------
# Doc ket qua so sanh model
# ---------------------------------------------------------------------------

def load_results() -> pd.DataFrame:
    df = pd.read_csv(RESULTS_CSV)
    # Cot trong CSV: Model,Accuracy,Precision (weighted),Recall (weighted),
    # F1 (weighted),ROC AUC,FPR,FNR,Specificity,Train time,Predict time,
    # TP,FP,TN,FN
    df = df.sort_values("F1 (weighted)", ascending=False).reset_index(drop=True)
    return df


def has_eval_images() -> bool:
    """Kiem tra cac anh ROC + ma tran nham lan da duoc script compare_models.py tao chua."""
    required = [
        RESULTS_DIR / "roc_comparison.png",
        RESULTS_DIR / "confusion_matrix_rf.png",
        RESULTS_DIR / "confusion_matrix_lr.png",
        RESULTS_DIR / "confusion_matrix_mnb.png",
        RESULTS_DIR / "confusion_matrix_xgb.png",
    ]
    return all(p.exists() for p in required)


def make_chart(df: pd.DataFrame) -> None:
    labels = ["RF", "LR", "MNB", "XGB"]
    # Xep theo thu tu RF, LR, MNB, XGBoost de bieu do de doc
    order = []
    for key in ["Random Forest", "Logistic", "Multinomial", "XGBoost"]:
        for i, name in enumerate(df["Model"]):
            if key.lower() in str(name).lower():
                order.append(i)
                break
    f1 = [float(str(df["F1 (weighted)"][i]).replace("%", "")) for i in order]
    acc = [float(str(df["Accuracy"][i]).replace("%", "")) for i in order]

    plt.rcParams["font.family"] = "Arial"
    x = range(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=150)
    b1 = ax.bar([i - w / 2 for i in x], f1, w, label="F1 (%)", color="#2E75B6")
    b2 = ax.bar([i + w / 2 for i in x], acc, w, label="Accuracy (%)", color="#ED7D31")
    ax.set_ylim(90, 100)
    ax.set_ylabel("Percent (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title("Comparison of 4 models on merged_clean.csv (206,722 emails)")
    ax.legend()
    ax.bar_label(b1, fmt="%.2f", fontsize=8, padding=1)
    ax.bar_label(b2, fmt="%.2f", fontsize=8, padding=1)
    fig.tight_layout()
    fig.savefig(CHART_PNG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Helper docx
# ---------------------------------------------------------------------------

def set_run_font(run, size=13, bold=None, italic=None, name="Times New Roman"):
    run.font.name = name
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    # Dau tieng Viet
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), name)


def para(doc, text="", size=13, bold=False, italic=False, align=None,
         space_after=6, space_before=0, style=None):
    p = doc.add_paragraph(style=style)
    if text:
        r = p.add_run(text)
        set_run_font(r, size=size, bold=bold, italic=italic)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    return p


def heading1(doc, text):
    p = doc.add_paragraph(style="Heading 1")
    r = p.add_run(text)
    set_run_font(r, size=16, bold=True)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(8)
    return p


def heading2(doc, text):
    p = doc.add_paragraph(style="Heading 2")
    r = p.add_run(text)
    set_run_font(r, size=14, bold=True)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    set_run_font(r, size=13)
    p.paragraph_format.space_after = Pt(4)
    return p


def formula(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_run_font(r, size=13, italic=True)
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_after = Pt(6)
    return p


def caption(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_run_font(r, size=12, italic=True)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    return p


def add_table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        set_run_font(r, size=12, bold=True)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(str(val))
            set_run_font(r, size=12)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_toc(doc):
    """Chen field Muc luc (Word tu cap nhat khi mo, Ctrl+A -> F9)."""
    p = doc.add_paragraph()
    run = p.add_run()
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t")
    t.text = "(Nhan Ctrl+A roi F9 de cap nhat muc luc)"
    fld3 = OxmlElement("w:fldChar")
    fld3.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    run._r.append(t)
    run._r.append(fld3)


def enable_update_fields(doc):
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)


def add_footer_pagenum(doc):
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    set_run_font(run, size=12)
    f1 = OxmlElement("w:fldChar")
    f1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "end")
    run._r.append(f1)
    run._r.append(instr)
    run._r.append(f2)


# ---------------------------------------------------------------------------
# Noi dung bao cao
# ---------------------------------------------------------------------------

def build_document(df: pd.DataFrame) -> Document:
    doc = Document()

    # Style Normal: Times New Roman 13
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), "Times New Roman")

    # Khop mau: Letter, le 3/2/2.2/2 cm
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    sec.left_margin = Cm(3.0)
    sec.right_margin = Cm(2.0)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)
    add_footer_pagenum(doc)

    # ---------------- TRANG BIA ----------------
    para(doc, "BỘ GIÁO DỤC VÀ ĐÀO TẠO", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    para(doc, "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP. HCM", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    para(doc, "KHOA CÔNG NGHỆ THÔNG TIN", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)
    para(doc, "BÁO CÁO TIẾN ĐỘ TIỂU LUẬN CHUYÊN NGÀNH", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)
    para(doc, "XÂY DỰNG HỆ THỐNG PHÁT HIỆN EMAIL PHISHING", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    para(doc, "SỬ DỤNG MACHINE LEARNING VÀ AI", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("Giai đoạn: ")
    set_run_font(r1, size=13, bold=True)
    r2 = p.add_run("Báo cáo lần 2 - Cập nhật dataset và tối ưu mô hình học máy")
    set_run_font(r2, size=13)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("Sinh viên thực hiện: ")
    set_run_font(r1, size=13, bold=True)
    r2 = p.add_run(".............................     MSSV: ....................")
    set_run_font(r2, size=13)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("Giảng viên hướng dẫn: ")
    set_run_font(r1, size=13, bold=True)
    r2 = p.add_run("Cô Võ Lê Phúc Hậu")
    set_run_font(r2, size=13)
    for _ in range(6):
        para(doc, "", space_after=0)
    para(doc, "TP. Hồ Chí Minh, tháng 10 năm 2026", align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- MUC LUC ----------------
    heading1(doc, "MỤC LỤC")
    add_toc(doc)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- DANH MUC TU VIET TAT ----------------
    heading1(doc, "DANH MỤC TỪ VIẾT TẮT")
    add_table(doc, ["Từ viết tắt", "Diễn giải"], [
        ["ML", "Machine Learning – học máy"],
        ["AI", "Artificial Intelligence – trí tuệ nhân tạo"],
        ["NLP", "Natural Language Processing – xử lý ngôn ngữ tự nhiên"],
        ["TF-IDF", "Term Frequency – Inverse Document Frequency"],
        ["RF", "Random Forest – rừng ngẫu nhiên"],
        ["LR", "Logistic Regression – hồi quy logistic"],
        ["MNB", "Multinomial Naive Bayes – Naive Bayes đa thức"],
        ["TP / FP / TN / FN", "True/False Positive/Negative – kết quả ma trận nhầm lẫn"],
        ["FNR", "False Negative Rate – tỷ lệ bỏ sót phishing"],
        ["FPR", "False Positive Rate – tỷ lệ báo nhầm"],
        ["IEEE", "Institute of Electrical and Electronics Engineers"],
        ["DOI", "Digital Object Identifier – mã định danh tài liệu số"],
    ], col_widths=[4.5, 11.0])
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- LOI MO DAU ----------------
    heading1(doc, "LỜI MỞ ĐẦU")
    para(doc,
         "Báo cáo lần 2 trình bày tiến độ của đồ án “Hệ thống phát hiện email phishing sử dụng "
         "Machine Learning và AI” trong giai đoạn cập nhật bộ dữ liệu huấn luyện và tối ưu mô hình "
         "học máy. Mốc này tập trung vào ba nội dung chính: (1) thay thế bộ dữ liệu huấn luyện bằng "
         "11 Curated Datasets được chuẩn hóa công bố tại IEEE ICMI 2024 và IEEE ISDFS 2024; "
         "(2) thử nghiệm so sánh bốn mô hình học máy trên cùng một quy trình tiền xử lý để chọn mô "
         "hình tối ưu; (3) hệ thống hóa lý thuyết tiền xử lý dữ liệu và các công thức của từng mô "
         "hình. Kết quả tích hợp mô hình tối ưu vào hệ thống và đánh giá đầu cuối sẽ được trình bày "
         "ở báo cáo lần 3.")

    # ---------------- TOM TAT TIEN DO ----------------
    heading1(doc, "TÓM TẮT TIẾN ĐỘ BÁO CÁO")
    para(doc,
         "Khoảng thời gian báo cáo: Từ ngày 03/10/2026 đến ngày 17/10/2026. Tỷ lệ hoàn thành theo "
         "đề cương: 100% cho mốc báo cáo lần 2. Giá trị này cần được sinh viên điều chỉnh theo mốc "
         "chính thức đã thống nhất với giảng viên hướng dẫn.")
    add_table(doc,
              ["Hạng mục", "Kế hoạch", "Kết quả tại mốc báo cáo", "Minh chứng", "Trạng thái"],
              [
                  ["Cập nhật dataset",
                   "Thay dataset cũ bằng bộ 11 Curated Datasets 2024 (IEEE)",
                   "Đã tải, gộp và làm sạch 206.722 email",
                   "data_train/processed/merged_clean.csv", "Hoàn thành"],
                  ["Kiểm tra trùng lặp",
                   "Đảm bảo không huấn luyện trên dữ liệu trùng lặp",
                   "0 dòng trùng hoàn toàn; 9.744 dòng trùng metadata (4,71%) đã được ghi nhận",
                   "Script check_duplicates.py", "Hoàn thành"],
                  ["So sánh mô hình",
                   "Thử nghiệm 3–4 mô hình ML trên cùng dữ liệu",
                   "Đã so sánh 4 mô hình; LR đạt F1 99,02%, XGBoost 98,27%, RF 97,23%, MNB 95,28%",
                   "results/model_comparison.csv", "Hoàn thành"],
                  ["Lý thuyết và tài liệu",
                   "Cập nhật lý thuyết tiền xử lý, công thức ML",
                   "Đã tổng hợp Master_Theory.md (hơn 1.000 dòng, phần A–H)",
                   "Master_Theory.md", "Hoàn thành"],
                  ["Tích hợp mô hình tối ưu",
                   "Đưa mô hình tốt nhất vào hệ thống",
                   "Đã quyết định giữ RF làm mô hình vận hành (3 lý do tại Master_Theory.md, mục D7); LR là hướng nâng cấp",
                   "app/models/phishing_rf.pkl", "Hoàn thành"],
                  ["Thí nghiệm chọn ngưỡng",
                   "Chọn ngưỡng quyết định dựa trên số liệu",
                   "Thử 4 ngưỡng (50/60/70/80) trên test set 40.859 email; chọn 60% – báo giả giảm 61%, bỏ sót 7,53% nhờ heuristic bù; thống nhất ngưỡng 60 trong toàn bộ code + test 59/60",
                   "results/threshold_analysis.csv", "Hoàn thành"],
              ],
              col_widths=[2.8, 3.4, 4.4, 3.2, 2.0])
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- CHUONG 1 ----------------
    heading1(doc, "CHƯƠNG 1. CƠ SỞ LÝ THUYẾT VỀ PHÁT HIỆN PHISHING BẰNG HỌC MÁY")

    heading2(doc, "1.1. Bài toán phát hiện email phishing")
    para(doc,
         "Phát hiện email phishing được mô hình hóa như một bài toán phân loại nhị phân: đầu vào là "
         "nội dung email (sender, receiver, date, subject, body, urls), đầu ra là Phishing (1) hoặc "
         "Not Phishing (0). Toàn bộ hệ thống thống nhất ngưỡng điểm 60: điểm nguy cơ lớn hơn hoặc "
         "bằng 60 thì kết luận Phishing, nhỏ hơn 60 là Not Phishing. Ngưỡng này không chọn theo "
         "lý thuyết mà theo số liệu: em đã thí nghiệm 4 ngưỡng (50/60/70/80) trên test set 40.859 "
         "email và chọn 60 vì đó là điểm cân bằng giữa bỏ sót phishing và báo động giả. Kết luận "
         "của mô hình học máy "
         "còn được bảo vệ bằng cơ chế guardrail: điểm cuối cùng luôn bằng lớn hơn giữa điểm ML và "
         "điểm heuristic, nhằm giảm bỏ sót phishing thật.")

    heading2(doc, "1.2. Bộ dữ liệu 11 Curated Datasets (nguồn IEEE)")
    para(doc,
         "Các kho dữ liệu thô ban đầu (Enron, TREC, SpamAssassin…) vốn ở định dạng email thô. Đồ án "
         "sử dụng phiên bản 11 Curated Datasets đã được chuẩn hóa cấu trúc 7 trường và làm sạch bởi "
         "nhóm nghiên cứu TS. Minhaz F. Zibran và Arifa I. Champa (Idaho State University, Mỹ), công "
         "bố tại IEEE ICMI 2024 và IEEE ISDFS 2024, lưu trữ trên Figshare với DOI chính thức "
         "(10.6084/m9.figshare.25432108 và 10.6084/m9.figshare.24952503).")
    add_table(doc,
              ["#", "File", "Số email", "Phishing (1)", "Legit (0)"],
              [
                  ["1", "CEAS_08.csv", "39.154", "21.842", "17.312"],
                  ["2", "Enron.csv", "29.767", "13.976", "15.791"],
                  ["3", "Ling.csv", "2.859", "458", "2.401"],
                  ["4", "Nazario.csv", "1.565", "1.565", "0"],
                  ["5", "Nazario_5.csv", "3.065", "1.565", "1.500"],
                  ["6", "Nigerian_5.csv", "6.331", "3.332", "2.999"],
                  ["7", "Nigerian_Fraud.csv", "3.332", "3.332", "0"],
                  ["8", "SpamAssasin.csv", "5.809", "1.718", "4.091"],
                  ["9", "TREC_05.csv", "55.990", "22.946", "32.329"],
                  ["10", "TREC_06.csv", "16.457", "3.989", "12.411"],
                  ["11", "TREC_07.csv", "53.757", "29.399", "24.358"],
                  ["", "TỔNG (trước xử lý)", "218.086", "103.122", "114.792"],
              ],
              col_widths=[1.2, 4.5, 3.4, 3.4, 3.4])
    para(doc,
         "Sau khi loại các dòng thiếu nhãn và làm sạch, tập dữ liệu sạch còn 206.722 email với phân "
         "bố 47,7% phishing và 52,3% hợp lệ – phân bố cân bằng, phù hợp huấn luyện mô hình phân "
         "loại. Khi đưa vào huấn luyện, tập con có subject và body đầy đủ gồm 204.294 email "
         "(97.251 phishing / 107.043 hợp lệ) được sử dụng.")

    heading2(doc, "1.3. Quy trình tiền xử lý dữ liệu")
    para(doc, "Quy trình tiền xử lý bảy bước được thực hiện tự động bằng script:")
    add_table(doc, ["Bước", "Nội dung thực hiện", "Dữ liệu ra"], [
        ["1", "Đọc 11 file CSV trong data_train/raw/", "218.086 dòng thô"],
        ["2", "Chuẩn hóa tên cột và kiểu dữ liệu (urls chuyển sang chuỗi)", "Cột đồng nhất"],
        ["3", "Loại dòng thiếu nhãn hoặc nhãn không hợp lệ (NaN ở TREC_05, TREC_06)", "Nhãn nhị phân 0/1"],
        ["4", "Làm sạch text: bỏ HTML, khoảng trắng thừa, chuẩn hóa UTF-8", "Subject và body sạch"],
        ["5", "Gộp metadata + subject + body + urls thành một chuỗi văn bản", "Text đầu vào cho TF-IDF"],
        ["6", "Kiểm tra và loại trùng lặp", "0 dòng trùng hoàn toàn"],
        ["7", "Lưu tập huấn luyện", "merged_clean.csv (206.722 dòng)"],
    ], col_widths=[1.5, 9.0, 5.5])

    heading2(doc, "1.4. Đại diện văn bản bằng TF-IDF")
    para(doc,
         "Mô hình học máy không đọc được chữ, chỉ đọc được số. TF-IDF biến văn bản email thành vector "
         "số theo nguyên tắc: từ xuất hiện nhiều trong email nhưng hiếm trong toàn bộ corpus thì có "
         "giá trị cao (từ khóa phân biệt).")
    formula(doc, "TF(t, d) = (số lần từ t xuất hiện trong văn bản d) / (tổng số từ trong d)")
    formula(doc, "IDF(t) = log(N / df(t))    với N là số văn bản, df(t) là số văn bản chứa từ t")
    formula(doc, "TF-IDF(t, d) = TF(t, d) × IDF(t)")
    para(doc,
         "Tham số đang dùng: max_features = 30.000 (giữ 30.000 từ quan trọng nhất), "
         "ngram_range = (1, 2) (quan sát cả từ đơn và cặp từ). Vector TF-IDF 30.000 chiều được gộp "
         "song song với 9 đặc trưng bảo mật (FeatureUnion) thành vector 30.009 chiều.")

    heading2(doc, "1.5. Chín đặc trưng bảo mật (Security Features)")
    add_table(doc, ["#", "Đặc trưng", "Cách tính"], [
        ["1", "Độ dài văn bản", "len(text)"],
        ["2", "Số lượng URL", "Đếm URL khớp regex https?:// hoặc www."],
        ["3", "Số URL đáng ngờ", "URL chứa login, verify, bit.ly, tinyurl, .ru, .zip…"],
        ["4", "Từ khóa khẩn cấp", "Đếm urgent, immediately, suspended, act now, khẩn cấp…"],
        ["5", "Từ khóa thông tin đăng nhập", "Đếm password, sign in, verify, tài khoản, mật khẩu…"],
        ["6", "Từ khóa tiền bạc", "Đếm payment, invoice, bank, gift card, thanh toán…"],
        ["7", "URL chứa ký tự @", "int(\"@\" trong URL) – kỹ thuật giấu tên miền thật"],
        ["8", "URL dùng địa chỉ IP", "Regex d{1,3}.d{1,3}.d{1,3}.d{1,3}"],
        ["9", "Gạch nối trong tên miền", "URL có dạng http://ten-mien-vay.com – mạo danh thương hiệu"],
    ], col_widths=[1.2, 5.0, 9.8])

    heading2(doc, "1.6. Bốn mô hình học máy và công thức chính")
    para(doc,
         "Bốn mô hình được huấn luyện trên cùng dữ liệu, cùng cách trích đặc trưng, cùng tỷ lệ "
         "chia tập 80/20 để so sánh công bằng.")

    para(doc, "a) Random Forest (Rừng ngẫu nhiên)", bold=True, space_after=2)
    para(doc,
         "Huấn luyện nhiều cây quyết định song song trên các mẫu bootstrap khác nhau, mỗi cây chỉ "
         "được xem xét một tập con ngẫu nhiên các đặc trưng; kết quả cuối là phiếu đa số của các cây.")
    formula(doc, "Gini(n) = 1 − Σ p(i|n)²    (độ không thuần khiết của nút)")
    formula(doc, "Dự đoán cuối = majority vote của 200 cây")
    para(doc,
         "Siêu tham số đang dùng: n_estimators = 200, max_depth = 30, class_weight = balanced. "
         "Ưu điểm: không cần chuẩn hóa dữ liệu, chống overfit tốt. Lưu ý: thời gian huấn luyện "
         "khoảng 3 phút, thời gian dự đoán mỗi email khoảng 2,71 giây – chậm nhất trong bốn mô hình.")

    para(doc, "b) Logistic Regression (Hồi quy logistic)", bold=True, space_after=2)
    para(doc,
         "Mô hình tuyến tính dùng hàm sigmoid biến đầu ra về khoảng [0, 1], huấn luyện bằng tối "
         "thiểu hóa hàm log-loss kèm chừng phạt L2.")
    formula(doc, "σ(z) = 1 / (1 + e^(−z)),  z = w·x + b")
    formula(doc, "Log-loss = −[y·log(σ(z)) + (1−y)·log(1−σ(z))] + λ‖w‖²")
    para(doc,
         "Siêu tham số: solver = saga, max_iter = 5000, chừng phạt L2. Lưu ý quan trọng: vì dữ "
         "liệu đầu vào là ma trận thưa nên BẮT BUỘC chuẩn hóa bằng MaxAbsScaler trước khi huấn "
         "luyện. Thực nghiệm cho thấy nếu quên chuẩn hóa, độ chính xác chỉ đạt 52,4%; sau khi thêm "
         "MaxAbsScaler đạt 99,02%.")

    para(doc, "c) Multinomial Naive Bayes", bold=True, space_after=2)
    para(doc,
         "Mô hình xác suất dựa trên định lý Bayes với giả định các từ độc lập với nhau:")
    formula(doc, "P(Phishing | x) ∝ P(Phishing) × Π P(xᵢ | Phishing)")
    formula(doc, "P(xᵢ | c) = (N_ci + α) / (N_c + α·n)    (Laplace smoothing, α = 1)")
    para(doc,
         "Ưu điểm: huấn luyện cực nhanh (0,1 giây). Lưu ý: chỉ dùng được với đặc trưng không âm "
         "(TF-IDF phù hợp; MaxAbsScaler sinh số âm thì không dùng được); giả định độc lập mạnh nên "
         "hiệu năng thấp nhất trong bốn mô hình.")

    para(doc, "d) XGBoost", bold=True, space_after=2)
    para(doc,
         "Gradient boosting trên cây quyết định: mỗi cây mới học sửa lỗi của cây trước, tối ưu hóa "
         "hàm mục tiêu gồm phần sai số và phần chừng phạt độ phức tạp:")
    formula(doc, "Obj = Σ l(yᵢ, ŷᵢ^(t−1) + fₜ(xᵢ)) + Σ Ω(fₜ),  Ω(f) = γT + ½λ‖w‖²")
    para(doc,
         "Siêu tham số: n_estimators = 200, max_depth = 6, learning_rate = 0,1, subsample = 0,8. "
         "Ưu điểm: hiệu năng cao. Lưu ý: thời gian huấn luyện khoảng 774 giây (13 phút) – lâu nhất, "
         "phù hợp huấn luyện ngoại tuyến.")

    heading2(doc, "1.7. Chỉ số đánh giá")
    add_table(doc, ["Chỉ số", "Công thức", "Ý nghĩa"], [
        ["Accuracy", "(TP + TN) / (TP + TN + FP + FN)", "Tỷ lệ dự đoán đúng tổng thể"],
        ["Precision", "TP / (TP + FP)", "Trong các email báo phishing, bao nhiêu phần trăm là đúng"],
        ["Recall", "TP / (TP + FN)", "Trong các email phishing thật, mô hình phát hiện được bao nhiêu"],
        ["F1", "2 × (Precision × Recall) / (Precision + Recall)", "Trung bình điều hòa Precision và Recall"],
        ["FNR", "FN / (TP + FN)", "Tỷ lệ phishing bị bỏ sót – chỉ số quan trọng nhất với bài toán này"],
        ["FPR", "FP / (FP + TN)", "Tỷ lệ email hợp lệ bị báo nhầm phishing"],
    ], col_widths=[3.0, 7.5, 6.0])
    para(doc,
         "Với bài toán bảo mật, FNR cần được theo dõi chặt hơn Accuracy vì email phishing bị bỏ sót "
         "gây hậu quả trực tiếp cho người dùng.")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- CHUONG 2 ----------------
    heading1(doc, "CHƯƠNG 2. CẬP NHẬT VÀ LÀM SẠCH BỘ DỮ LIỆU")

    heading2(doc, "2.1. Lý do cập nhật dataset")
    para(doc,
         "Bộ dữ liệu cũ không có nguồn xác thực rõ ràng, dung lượng nhỏ và chưa đủ đa dạng về loại "
         "phishing. Bộ 11 Curated Datasets 2024 được chọn vì: (1) công bố tại hội nghị IEEE, có DOI "
         "xác thực; (2) gộp 11 nguồn uy tín gồm NIST và University of Waterloo (TREC), Carnegie "
         "Mellon (Enron), Apache Foundation (SpamAssassin), Đại học Michigan (Nigerian Fraud); "
         "(3) quy mô lớn (hơn 206 nghìn email) và phân bố cân bằng; (4) đã được chuẩn hóa 7 trường "
         "dữ liệu đồng nhất.")

    heading2(doc, "2.2. Tải và kiểm tra 11 file CSV")
    para(doc,
         "Toàn bộ 11 file được tải trực tiếp từ kho Figshare của nhóm tác giả, kiểm tra bằng script "
         "inspect_datasets.py (cột dữ liệu, mẫu nội dung, phân bố nhãn thực tế) trước khi xử lý. "
         "Bảng chi tiết 11 file đã nêu tại Chương 1, mục 1.2. Hai file Enron.csv và Ling.csv chỉ có "
         "3 cột (subject, body, label) nên khi gộp, các cột còn lại được để trống.")

    heading2(doc, "2.3. Quy trình gộp và làm sạch")
    para(doc,
         "Script merge_datasets.py thực hiện bảy bước tiền xử lý đã mô tả tại mục 1.3. Kết quả cuối "
         "cùng: 206.722 email hợp lệ, lưu tại data_train/processed/merged_clean.csv. Dữ liệu đã làm "
         "sạch được dùng chung cho tất cả các bước huấn luyện và thử nghiệm trong báo cáo này.")

    heading2(doc, "2.4. Kiểm tra trùng lặp (chống Accuracy ảo)")
    para(doc,
         "Nếu dữ liệu huấn luyện và kiểm thử có dòng trùng lặp, mô hình chỉ cần “nhớ đáp án” là "
         "đạt độ chính xác cao ảo. Script check_duplicates.py đã kiểm tra và kết quả:")
    add_table(doc, ["Kiểu kiểm tra", "Số dòng trùng", "Kết luận"], [
        ["Trùng hoàn toàn (toàn bộ các cột)", "0", "An toàn"],
        ["Trùng subject + body", "0", "An toàn"],
        ["Nhãn mâu thuẫn (cùng nội dung, nhãn khác nhau)", "0", "An toàn"],
        ["Trùng sender + subject + date", "9.744 (4,71%)", "Body khác nhau – không phải trùng lặp"],
    ], col_widths=[7.5, 3.5, 5.5])
    para(doc,
         "Kết luận: bộ dữ liệu không chứa dòng trùng lặp, độ chính xác đo được là thực chứ không ảo.")

    heading2(doc, "2.5. File mẫu phục vụ đối chiếu")
    para(doc,
         "Vì file dữ liệu gốc có dung lượng lớn (tổng khoảng 430 MB) khiến phần mềm bảng tính mở "
         "chậm, đã trích xuất file mẫu phục vụ đối chiếu nhanh:")
    bullet(doc, "data_train/sample_1000_rows.csv: 1.000 dòng lấy ngẫu nhiên từ merged_clean.csv (516 email hợp lệ, 484 phishing), phần thân email cắt còn 500 ký tự.")
    bullet(doc, "data_train/raw_samples/: mỗi file raw 100 dòng đầu tiên (11 file) và file gộp ALL_RAW_combined_1000.csv có cột source_file đánh dấu nguồn, thân email cắt còn 300 ký tự.")

    heading2(doc, "2.6. Hiệu đính nguồn gốc và link xác thực")
    para(doc,
         "Toàn bộ nguồn gốc 11 dataset đã được hiệu đính theo đúng tài liệu gốc: Enron do GS. William "
         "W. Cohen (Carnegie Mellon) chuẩn hóa; Ling-Spam của GS. Ion Androutsopoulos (Đại học "
         "Kinh tế và Kinh doanh Athens, Hy Lạp, 2000); Nigerian Fraud thuộc bộ CLAIR của GS. Dragomir "
         "Radev (Đại học Michigan, 2008). Link xác thực (bài báo IEEE, DOI Figshare, NIST, Apache, "
         "CMU…) đã được cập nhật đầy đủ trong file Master_Theory.md, Phần A.")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- CHUONG 3 ----------------
    heading1(doc, "CHƯƠNG 3. THỬ NGHIỆM SO SÁNH CÁC MÔ HÌNH HỌC MÁY")

    heading2(doc, "3.1. Thiết kế thực nghiệm")
    para(doc, "Bốn mô hình được chạy trên cùng một điều kiện để so sánh công bằng:")
    add_table(doc, ["Yếu tố", "Giá trị thống nhất"], [
        ["Dữ liệu", "merged_clean.csv – 204.294 email có subject/body đầy đủ (tổng file 206.722 dòng)"],
        ["Chia tập", "80% huấn luyện, 20% kiểm thử, stratify, random_state = 42"],
        ["Đặc trưng", "TF-IDF (30.000 chiều) + 9 Security Features = 30.009 chiều (FeatureUnion)"],
        ["Chỉ số", "Accuracy, Precision, Recall, F1 (weighted), FPR, FNR, thời gian huấn luyện/dự đoán"],
    ], col_widths=[3.5, 13.0])

    heading2(doc, "3.2. Kết quả đo lường")
    rows = []
    for _, r in df.iterrows():
        row = [
            r["Model"], r["Accuracy"], r["F1 (weighted)"], r["FNR"], r["FPR"],
            r["Train time"], r["Predict time"],
        ]
        # Cot AUC/Specificity chi co sau khi chay lai compare_models.py moi
        if "ROC AUC" in df.columns:
            row.append(str(r["ROC AUC"]))
        if "Specificity" in df.columns:
            row.append(str(r["Specificity"]))
        rows.append(row)
    header = ["Mô hình", "Accuracy", "F1", "FNR", "FPR", "Huấn luyện", "Dự đoán*"]
    if "ROC AUC" in df.columns:
        header.append("AUC")
    if "Specificity" in df.columns:
        header.append("Specificity")
    add_table(doc, header, rows)
    para(doc, "* Thời gian dự đoán tính trên toàn bộ 40.859 email kiểm thử.",
         size=11, italic=True, space_after=6)
    doc.add_picture(str(CHART_PNG), width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, "Hình 3.1. Biểu đồ so sánh F1 và Accuracy của bốn mô hình.")

    # --- ROC + AUC ---
    heading2(doc, "3.3. Biểu đồ ROC và chỉ số AUC")
    para(doc,
         "ROC (Receiver Operating Characteristic) là đường cong vẽ giữa TPR (tỷ lệ bắt được "
         "phishing) và FPR (tỷ lệ báo oan email hợp lệ) tại mọi ngưỡng phân loại từ 0 đến 1. "
         "AUC (Area Under Curve) là diện tích dưới đường cong đó, không phụ thuộc ngưỡng — chỉ "
         "số quan trọng để so sánh khả năng xếp hạng nguy cơ của các mô hình. AUC = 1.0 là hoàn "
         "hảo, AUC = 0.5 là đoán ngẫu nhiên; cả bốn mô hình trong đồ án đều đạt AUC trên 0.98 "
         "(mức xuất sắc).")
    auc_rows = []
    for _, r in df.iterrows():
        auc_rows.append([
            r["Model"], str(r.get("ROC AUC", "-")), r["Accuracy"], r["F1 (weighted)"],
        ])
    add_table(doc,
              ["Mô hình", "ROC AUC", "Accuracy", "F1"],
              auc_rows,
              col_widths=[5.4, 2.4, 2.4, 2.4])
    para(doc,
         "Xếp hạng AUC: Logistic Regression 0.9992 > XGBoost 0.9983 > Random Forest 0.9967 > "
         "Naive Bayes 0.9823. Chênh AUC giữa LR và mô hình vận hành (RF) chỉ 0.0025 — rất nhỏ.")
    if ROC_PNG.exists():
        doc.add_picture(str(ROC_PNG), width=Inches(5.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption(doc,
                "Hình 3.2. So sánh ROC Curve của bốn mô hình (số AUC ghi trên từng đường).")
    else:
        para(doc, "(Chạy python scripts/compare_models.py để tạo ảnh ROC.)",
             size=11, italic=True)

    # --- Ma tran nham lan ---
    heading2(doc, "3.4. Ma trận nhầm lẫn hiển thị trực tiếp từ chương trình")
    para(doc,
         "Theo yêu cầu của giảng viên, ma trận nhầm lẫn không in dưới dạng bảng chữ trong báo "
         "cáo, mà được chương trình tính toán và hiển thị trực tiếp: chạy "
         "python scripts/compare_models.py sẽ vẽ ma trận nhầm lẫn của cả bốn mô hình ra file "
         "PNG, sau đó mở ứng dụng Streamlit, tab \"Danh gia mo hinh\" sẽ hiển thị bảng chỉ số, "
         "biểu đồ ROC và bốn ma trận nhầm lẫn. Ảnh bên dưới là ảnh chụp từ chương trình.")
    if has_eval_images():
        cm_items = [(name, path) for name, path in CM_PNGS.items() if path.exists()]
        for i in range(0, len(cm_items), 2):
            pair = cm_items[i:i + 2]
            pic = doc.add_paragraph()
            for name, path in pair:
                run = pic.add_run()
                run.add_picture(str(path), width=Inches(2.6))
            pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            labels = "    ".join(name for name, _ in pair)
            r = cap.add_run(f"Hình 3.{5 + i // 2}. Ma trận nhầm lẫn — {labels}")
            set_run_font(r, size=11, italic=True)
        para(doc,
             "Đọc heatmap: hàng = nhãn thực tế, cột = dự đoán. Ô TN (trên trái) và TP (dưới phải) "
             "là dự đoán đúng; ô FP (trên phải) là email hợp lệ bị báo oan; ô FN (dưới trái) là "
             "phishing bị bỏ sót — lỗi nguy hiểm nhất trong hệ thống bảo mật.")
    else:
        para(doc,
             "(Chạy python scripts/compare_models.py để tạo 4 ảnh ma trận nhầm lẫn "
             "results/confusion_matrix_*.png rồi chạy lại script này.)",
             size=11, italic=True)

    heading2(doc, "3.5. Nhận xét từng mô hình")
    bullet(doc, "Logistic Regression đạt kết quả tốt nhất (F1 99,02%, FNR 0,95%) và dự đoán nhanh nhất (0,03 giây cho toàn bộ 40.859 email kiểm thử). Điều kiện cần: chuẩn hóa MaxAbsScaler cho ma trận thưa.")
    bullet(doc, "XGBoost xếp thứ hai (98,27%) nhưng huấn luyện lâu nhất (khoảng 13 phút) – phù hợp huấn luyện ngoại tuyến, không phù hợp chạy lại thường xuyên trên máy cá nhân.")
    bullet(doc, "Random Forest đạt 97,23% (FNR 2,61%, FPR 2,91%), không cần chuẩn hóa dữ liệu, là mô hình đang được tích hợp trong ứng dụng.")
    bullet(doc, "Multinomial Naive Bayes đạt 95,28% nhưng huấn luyện chỉ mất 0,1 giây – phù hợp làm đường cơ sở (baseline) hoặc môi trường hạn chế tài nguyên.")

    heading2(doc, "3.6. Bài học thực nghiệm: chuẩn hóa đặc trưng")
    para(doc,
         "Lần chạy đầu tiên, Logistic Regression chỉ đạt 52,4% – gần như đoán ngẫu nhiên. Nguyên "
         "nhân: mô hình tuyến tính nhạy với độ lớn đặc trưng, trong khi ma trận TF-IDF rất thưa và "
         "có giá trị trị lớn nhỏ chênh lệch nhiều. Sau khi thêm MaxAbsScaler (chuẩn hóa mỗi cột về "
         "khoảng [−1, 1] mà vẫn giữ tính thưa của ma trận) kết quả đạt 99,02%. Đây là bài học quan "
         "trọng: tiền xử lý phải phù hợp với đặc tính của từng mô hình.")

    heading2(doc, "3.7. Kết luận lựa chọn mô hình")
    para(doc,
         "Logistic Regression đạt chỉ số cao nhất và kết quả này được ghi nhận đầy đủ: TF-IDF tạo "
         "ma trận tuyến tính nên LR tìm được đường phân cách tối ưu. Tuy nhiên, sau khi cân nhắc, "
         "đồ án giữ Random Forest (97,23%) làm mô hình vận hành vì 3 lý do. Thứ nhất, LR chỉ thắng "
         "khi thêm bước chuẩn hóa MaxAbsScaler – thực nghiệm của chính đồ án cho thấy thiếu bước đó "
         "LR sụp về 52,4%; một pipeline vận hành nhiều bước thì mỗi bước là một rủi ro khi thay đổi "
         "hoặc tái huấn luyện, còn RF chạy đúng ngay trên ma trận thưa. Thứ hai, hệ thống là hybrid: "
         "điểm cuối cùng bằng lớn hơn (điểm ML, điểm heuristic) nên phần bỏ sót được tầng quy tắc "
         "bù đắp, khoảng cách 1,79% giữa hai mô hình không phản ánh ra kết quả cuối mà người dùng "
         "nhận được. Thứ ba, RF tính trung bình xác suất của 200 cây nên giá trị dự đoán điềm đạm "
         "hơn, ít khi tự tin sai trên dữ liệu ngoài phân phối – còn LR có xu hướng đẩy xác suất về "
         "gần 0 hoặc gần 1. LR được ghi nhận là hướng nâng cấp: nếu chuyển, phải build pipeline "
         "mới chứa cả scaler lẫn mô hình (lưu cùng một file .pkl) rồi đo lại toàn bộ hệ thống ở "
         "ngưỡng 60%.")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- CHUONG 4 ----------------
    heading1(doc, "CHƯƠNG 4. THỰC NGHIỆM TRÊN HỆ THỐNG VÀ KẾT QUẢ ĐẠT ĐƯỢC")

    heading2(doc, "4.1. Môi trường thực hiện")
    add_table(doc, ["Thành phần", "Phiên bản / thông số"], [
        ["Ngôn ngữ", "Python 3.13"],
        ["Thư viện ML", "scikit-learn 1.8.0, xgboost 3.4.1, lightgbm 4.7.0"],
        ["Giao diện", "Streamlit (tab Phân tích Email và Auto Monitor)"],
        ["Tích hợp AI", "Google Gemini (gemini-3.6-flash), SDK google-genai"],
        ["Dữ liệu", "206.722 email – merged_clean.csv"],
    ], col_widths=[4.5, 12.0])

    heading2(doc, "4.2. Luồng dự đoán trong hệ thống")
    para(doc,
         "Khi người dùng gửi email cần kiểm tra, hệ thống thực hiện: trích xuất đặc trưng (TF-IDF + "
         "9 Security Features) → mô hình ML dự đoán xác suất phishing (điểm ML) → điểm heuristic "
         "tính riêng từ các dấu hiệu bảo mật → điểm cuối cùng = lớn hơn (điểm ML, điểm heuristic) → "
         "nhận định Phishing nếu điểm ≥ 60. Cơ chế này đảm bảo email có dấu hiệu lừa đảo rõ ràng "
         "vẫn bị cảnh báo kể cả khi mô hình ML đánh giá thấp.")

    heading2(doc, "4.3. Thí nghiệm chọn ngưỡng 60%")
    para(doc,
         "Ngưỡng quyết định được chọn bằng số liệu thực nghiệm thay vì mặc định 50%. Bốn ngưỡng "
         "được thử trên cùng test set 40.859 email, dùng cấu hình đang vận hành (RF + guardrail "
         "heuristic); kết quả đầy đủ lưu tại results/threshold_analysis.csv:")
    add_table(doc, ["Ngưỡng", "FNR (bỏ sót phishing)", "FPR (báo giả)", "Email hợp lệ bị báo oan"], [
        ["50%", "2,57%", "3,61%", "772"],
        ["60% (chọn)", "7,53%", "1,40%", "300"],
        ["70%", "18,16%", "0,36%", "77"],
        ["80%", "33,98%", "0,07%", "16"],
    ], col_widths=[2.6, 5.0, 4.0, 4.6])
    para(doc,
         "Ở ngưỡng 50%, hệ thống gửi cảnh báo Telegram cho 772 email hợp lệ; cảnh báo giả tích tụ "
         "sẽ khiến người dùng bỏ qua cảnh báo thật (hiện tượng alert fatigue). Ở ngưỡng 70%, tỷ lệ "
         "bỏ sót nhảy vọt lên 18,16% – gấp khoảng 7 lần ngưỡng 50%, không phù hợp hệ thống bảo "
         "mật. Ngưỡng 60% là điểm cân bằng: báo giả giảm 61% so với 50% (còn 300 email), bỏ sót "
         "được giữ ở mức 7,53% và phần bỏ sót này được tầng heuristic bù đắp – email lừa đảo thật "
         "thường có từ khóa khẩn cấp cùng URL giả mạo nên heuristic sẽ kéo điểm cuối lên trên 60. "
         "Ngưỡng 60% được thống nhất trong toàn bộ code (nhãn của mô hình, orchestrator, giao diện, "
         "Telegram, lời nhắc của trợ lý AI, Email Fetcher) và có script test_binary.py kiểm chứng "
         "ranh giới 59/60.")

    heading2(doc, "4.4. Kết quả đạt được")
    add_table(doc, ["Nội dung", "Kết quả"], [
        ["Bộ dữ liệu huấn luyện", "206.722 email sạch, phân bố 47,7% / 52,3%, 0 dòng trùng"],
        ["Mô hình RF đang chạy", "Accuracy 97,23%, F1 97,23%, FNR 2,61%, FPR 2,91%"],
        ["Mô hình LR (thí nghiệm)", "Accuracy 99,02%, F1 99,02%, FNR 0,95%, FPR 1,01%"],
        ["Tốc độ dự đoán", "RF: 2,71 giây và LR: 0,03 giây cho toàn bộ 40.859 email kiểm thử"],
        ["Ngưỡng quyết định", "60% – FPR 1,40%, FNR 7,53% (số liệu 4 ngưỡng: threshold_analysis.csv)"],
        ["Ứng dụng Streamlit", "Chạy ổn định trên localhost:8501 với 2 tab"],
        ["Tài liệu lý thuyết", "Master_Theory.md – 8 phần (A–H), 15 câu hỏi đáp"],
    ], col_widths=[5.0, 11.5])

    heading2(doc, "4.5. Hạn chế được ghi nhận")
    bullet(doc, "Mô hình RF đang chạy có tốc độ dự đoán 2,71 giây cho 40.859 email kiểm thử (tương đương 0,07 mili giây mỗi email) – đủ nhanh cho chế độ giám sát email hàng loạt.")
    bullet(doc, "Chưa thử nghiệm trên email tiếng Việt có dấu thật ngoài các file mẫu; bộ dữ liệu 2024 chủ yếu email tiếng Anh.")
    bullet(doc, "Kết quả LR tốt hơn nhưng được giữ làm hướng nâng cấp; nếu chuyển phải build pipeline mới chứa cả scaler lẫn mô hình rồi đo lại toàn bộ ở ngưỡng 60%.")
    bullet(doc, "Ở ngưỡng vận hành 60%, tỷ lệ bỏ sót phishing trên test set là 7,53% – cần thử thêm trên email thực tế ngoài phân phối để đánh giá đúng hơn.")
    bullet(doc, "Một số file nguồn (Enron, Ling) thiếu trường metadata nên không khai thác được tín hiệu người gửi/URL từ các nguồn này.")

    # ---------------- KHÓ KHĂN ----------------
    heading1(doc, "KHÓ KHĂN, CÁCH XỬ LÝ VÀ KẾ HOẠCH TIẾP THEO")
    heading2(doc, "Khó khăn và cách xử lý")
    add_table(doc, ["Vấn đề", "Nguyên nhân / tác động", "Cách xử lý"], [
        ["LR chỉ đạt 52,4% (lần chạy đầu)",
         "Mô hình tuyến tính nhạy cỡ đặc trưng, TF-IDF thưa và giá trị lệch",
         "Thêm MaxAbsScaler → đạt 99,02%"],
        ["XGBoost huấn luyện 13 phút",
         "204 nghìn mẫu × 30.009 đặc trưng, boosting 200 cây",
         "Chấp nhận huấn luyện ngoại tuyến; dùng lại file mô hình đã lưu"],
        ["File dữ liệu mở bảng tính bị lag",
         "File gốc hàng trăm MB",
         "Trích file mẫu 1.000 dòng cho Excel"],
        ["Dòng label thiếu trong TREC",
         "NaN ở TREC_05 (715 dòng), TREC_06 (57 dòng)",
         "Loại khi tiền xử lý, ghi nhận số dòng đã loại"],
        ["Lỗi hiển thị tiếng Việt trong console",
         "PowerShell dùng mã ký tự khác UTF-8",
         "In thông báo ASCII trong script; đọc kết quả qua file"],
    ], col_widths=[4.2, 6.3, 6.0])

    heading2(doc, "Kế hoạch mốc tiếp theo")
    add_table(doc, ["Công việc", "Đầu ra cần có", "Tiêu chí kiểm tra"], [
        ["Đo trên email thực tế",
         "Bộ email mẫu tiếng Anh/tiếng Việt mới ngoài tập huấn luyện",
         "Ghi nhận FNR, FPR thực tế; đối chiếu với số liệu 7,53% / 1,40% trên test set"],
        ["Hoàn thiện tài liệu báo cáo",
         "Báo cáo lần 3 với số liệu đầu cuối",
         "Đối chiếu được số liệu với file results/"],
    ], col_widths=[4.5, 6.0, 6.0])
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------- KET LUAN ----------------
    heading1(doc, "KẾT LUẬN GIAI ĐOẠN 2")
    para(doc,
         "Trong giai đoạn báo cáo lần 2, đồ án đã hoàn thành cập nhật bộ dữ liệu huấn luyện theo "
         "nguồn IEEE có xác thực (206.722 email, không trùng lặp), hoàn thiện quy trình tiền xử lý "
         "tự động và hệ thống hóa lý thuyết TF-IDF, đặc trưng bảo mật cùng công thức bốn mô hình học "
         "máy. Thử nghiệm so sánh cho thấy Logistic Regression đạt F1 cao nhất (99,02%) và dự đoán "
         "nhanh nhất, tiếp theo là XGBoost (98,27%), Random Forest (97,23%) và Multinomial Naive "
         "Bayes (95,28%). Mốc tiếp theo là quyết định và tích hợp mô hình tối ưu vào hệ thống, thử "
         "nghiệm trên email thực tế và tổng hợp số liệu đầu cuối cho báo cáo lần 3.")

    # ---------------- TAI LIEU THAM KHAO ----------------
    heading1(doc, "TÀI LIỆU THAM KHẢO")
    refs = [
        "[1] Champa, A. I., Rabbi, M. F., & Zibran, M. F. (2024). Curated Datasets and Feature Analysis for Phishing Email Detection with Machine Learning. 2024 IEEE 3rd International Conference on Computing and Machine Intelligence (ICMI). DOI: 10.6084/m9.figshare.25432108.",
        "[2] Champa, A. I., Rabbi, M. F., & Zibran, M. F. (2024). Why Phishing Emails Escape Detection: A Closer Look at the Failure Points. 2024 12th IEEE International Symposium on Digital Forensics and Security (ISDFS). DOI: 10.6084/m9.figshare.24952503.",
        "[3] Kho dữ liệu tổng hợp trên Zenodo. DOI: 10.5281/zenodo.8339691.",
        "[4] Cormack, G. V. TREC Spam Track Corpus. https://trec.nist.gov/data/spam.html.",
        "[5] Cohen, W. W. Enron Email Dataset. https://www.cs.cmu.edu/~enron/.",
        "[6] The Apache Software Foundation. SpamAssassin Public Corpus. https://spamassassin.apache.org/old/publiccorpus/.",
        "[7] Androutsopoulos, I. et al. (2000). An Evaluation of Naive Bayesian Anti-Spam Filtering. arXiv:cs/0008019.",
        "[8] Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. JMLR, 12, 2825–2830.",
        "[9] Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5–32.",
        "[10] Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. Proceedings of KDD.",
    ]
    for ref in refs:
        para(doc, ref, size=13, space_after=4)

    enable_update_fields(doc)
    return doc


def main():
    df = load_results()
    make_chart(df)
    doc = build_document(df)
    doc.save(str(OUTPUT_DOCX))
    print(f"Da tao file: {OUTPUT_DOCX}")


if __name__ == "__main__":
    main()
