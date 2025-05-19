import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 字型路徑（使用 TTC 格式）
font_path = os.path.join(os.path.dirname(__file__), 'msjh.ttc')
if not os.path.exists(font_path):
    raise FileNotFoundError("找不到 msjh.ttc 字型檔案，請將其放在與程式相同的資料夾內。")

# 註冊字型
pdfmetrics.registerFont(TTFont('msjh', font_path, subfontIndex=0))

# === 載入 API 金鑰與初始化 Gemini ===
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash")

# === 讀取與處理資料 ===
df = pd.read_csv("dataresult1.csv")

# ✅ 不進行欄位映射，直接使用原始中文資料
# print(df.head()) 可以查看欄位是否正確為「男／女」、「技術」等

# 篩選高風險
risk_5_df = df[df["離職風險分級"] == 5]

# === 建立 Gemini Prompt ===
def build_prompt(df, risk_df):
    summary = df.to_markdown(index=False)
    prompt = f"""
你是一位資深人資顧問，以下是公司員工資料（格式為表格）：
{summary}

請執行以下任務：
1. 對整體資料進行分析，指出潛在人力風險與改進空間。
2. 提出改善組織氛圍、培訓與留才策略。
3. 對所有離職風險為5的員工（提供性別與部門），提出具體挽留建議。
4. 提出問卷設計優化建議（欄位設計、問題範疇、量表與選項）。

請將 (1)-(3) 整合為「人資分析與建議」，(4) 獨立成「問卷設計建議」，並使用繁體字說明，不可有任何表情符號，不可使用 NotoSansJP 無法顯示的字。
"""
    return prompt

# === 呼叫 Gemini 並取得回覆 ===
prompt = build_prompt(df, risk_5_df)
response = model.generate_content(prompt)
response_text = response.text.strip()
parts = response_text.split("問卷設計建議")
analysis_text = parts[0].strip()
form_text = "問卷設計建議" + parts[1].strip() if len(parts) > 1 else "（無問卷建議內容）"

# === 產生 PDF 報告 ===
def create_pdf(path, title, content):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    margin = 50
    y = height - margin

    def split_by_char_count(text, max_chars=46):
        return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

    def draw_wrapped_line(text, font_name, font_size, extra_spacing=0):
        nonlocal y
        c.setFont(font_name, font_size)
        wrapped_lines = split_by_char_count(text.replace("**", ""), max_chars=46)
        for line in wrapped_lines:
            if y < margin + 40:
                c.showPage()
                y = height - margin
                c.setFont(font_name, font_size)
            c.drawString(margin, y, line)
            y -= font_size + extra_spacing

    # 標題
    c.setFont("msjh", 15)
    c.drawString(margin, y, title)
    y -= 30

    # 內文
    for line in content.split("\n"):
        draw_wrapped_line(line.strip(), "msjh", 11, extra_spacing=5)
        y -= 5

    c.save()

# === 建立兩份報告 ===
create_pdf("分析建議報告.pdf", "人資分析與改善建議報告", analysis_text)
create_pdf("問卷設計建議.pdf", "下一次問卷設計建議", form_text)

print(" 兩份 PDF 產出完成！")
