# 113_2_DS_Final

<details>
  <summary><strong>期中提案</strong></summary>

  [提案影片 YouTube 連結](https://youtu.be/qAA3lzzANrg)
  
</details>


<details>
  <summary><strong>第二次進度報告</strong></summary>

  [影片 YouTube 連結](https://youtu.be/xobWjNFoGiE)
  
</details>

<h6>⭐️</h6>

---

# RetainAI - 人資數據分析與報告系統

## 專案簡介

RetainAI 是一套基於網頁的 HR（人力資源）數據分析與報告自動化系統。
使用者只需輸入 Google Sheet ID，系統即會自動處理資料、產生分析報告與圖表，並可於網頁介面即時下載。

## 主要功能
- **Google Sheet 整合**：直接從 Google Sheet 匯入 HR 資料。
- **自動化數據處理**：後端多步驟自動清理、分析與視覺化。
- **報告產生**：自動生成 PDF 報告與建議文件。
- **即時進度顯示**：透過 Socket.IO 前端即時顯示處理進度。
- **現代化介面**：美觀、響應式的 Bootstrap 5 前端設計。

## 安裝步驟

### 1. 下載專案
```bash
git clone <你的-repo-url>
cd <你的專案資料夾>
```

### 2. 安裝所需 Python 套件
建議使用虛擬環境（venv、conda 等）：
```bash
pip install -r requirements.txt
```

**也可以直接複製下方所有套件名稱，一次安裝：**
```bash
pip install flask flask-socketio eventlet gspread oauth2client pandas numpy matplotlib seaborn python-dotenv snownlp reportlab google-generativeai pillow tqdm retrying
```

---

## 必要檔案與設定
1. **Google API 憑證**  
   - 建立 `.env` 檔案，內容如下（請填入你的資訊）：
     ```
     GOOGLE_CREDENTIALS_JSON = 你的 Google API Jasoon
     GEMINI_API_KEY = 你的 Gemini API Key
     ```
2. **字型檔**  
   - 請將 `msjh.ttc`（微軟正黑體）放在專案根目錄，用於 PDF 產生。
3. **資料夾結構**  
   - `template/Index.html`（前端網頁）
   - `static/`（產生的圖表圖片）

---

## 檔案結構說明
```
專案根目錄/
│
├── app.py                      # Flask 主後端
├── Auto.py                     # Google Sheet 資料處理
├── HRanalyze.py                # HR 資料分析
├── hr_analysis_feedback.py     # 報告產生
├── boxplot_col.py              # 各類圖表腳本
├── histogram_col.py
├── satisfaction_bar_col.py
├── turnover_risk_bar_chart.py
├── turnover_risk_pie_dep.py
├── chart_analysis.py           # 圖表分析與 PDF 產生
│
├── template/
│   └── Index.html              # 前端 UI
│
├── static/                     # 產生的圖表圖片
│
├── msjh.ttc                    # PDF 用字型檔
├── .env                        # 環境變數 (Gemini API Key & Google API Jasoon)
└── requirements.txt            # Python 套件清單
```

---

## 執行方式
1. **啟動 Flask 伺服器**
```bash
python app.py
```
2. **於瀏覽器開啟：**
```
http://localhost:5000
```
3. **使用流程**
   - 輸入 Google Sheet ID 並送出。
   - 等待處理，點擊「Generate Analysis Report」。
   - 下載產生的報告與圖表。

---

## 注意事項
- 請確認所有 Python 套件已安裝於正確的虛擬環境。
- 系統需能連線 Google Sheets 與 Gemini API。
- 若遇到字型或 API 錯誤，請檢查 `msjh.ttc`、`.env` 是否正確放置。
- 建議使用 Google Chrome 或其他現代瀏覽器。

---

## 常見問題
- **ModuleNotFoundError**：請確認已啟用正確的虛擬環境並安裝所有套件。
- **Google API 錯誤**：請確認憑證與 Google Sheet 權限正確。
- **PDF/字型錯誤**：請確認 `msjh.ttc` 已放在專案根目錄。

---
