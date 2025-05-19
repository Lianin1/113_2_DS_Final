import os
import json
from dotenv import load_dotenv
import pandas as pd
from snownlp import SnowNLP
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sys

# 載入 .env
load_dotenv()

# 從 .env 取得 JSON 串
google_json_raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
google_json_dict = json.loads(google_json_raw)

# 建立憑證
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_json_dict, scope)
client = gspread.authorize(creds)

# 從命令行參數獲取 Google Sheet ID
if len(sys.argv) > 1:
    input_sheet_id = sys.argv[1]
else:
    input_sheet_id = "1W1c9d6bVet8Lhdb69NbUHjkFxVOdrYOu5VV-xRVh91g"  # 預設值

try:
    input_ws = client.open_by_key(input_sheet_id).sheet1
except Exception as e:
    print(f"無法訪問 Google Sheet: {e}")
    sys.exit(1)

# 讀取原始回饋資料
data = input_ws.get_all_records()
df = pd.DataFrame(data)

# 自動偵測問卷題目欄位（從「工作與生活平衡」右邊開始）
balance_index = df.columns.get_loc("工作與生活平衡")
original_cols = df.columns[balance_index + 1:].tolist()
short_score_cols = [f"Q{i+1}_情緒分數" for i in range(len(original_cols))]

# 定義 SnowNLP 分數轉換
def convert_to_score(text):
    try:
        sentiment = SnowNLP(str(text)).sentiments
        score = round(sentiment * 2 - 1, 1)
        return score if score != 0 else 0.1
    except:
        return 0.1

# 分析每一題情緒
for i, col in enumerate(original_cols):
    df[short_score_cols[i]] = df[col].apply(convert_to_score)

# 計算平均分數
df["回饋情緒分數"] = df[short_score_cols].sum(axis=1) / 6
df["回饋情緒分數"] = df["回饋情緒分數"].round(1)
df.loc[df["回饋情緒分數"] == 0, "回饋情緒分數"] = 0.1

# 組成輸出 DataFrame
result_cols = ["員工編號"] + ['性別'] + ['部門'] + ['Level'] + ['工作環境滿意度'] + ['薪資福利滿意度'] + ['管理制度滿意度'] + ['工作與生活平衡'] + ["回饋情緒分數"]
result_df = df[result_cols]

# 將結果儲存成 CSV 檔案
result_df.to_csv("dataresult.csv", index=False, encoding='utf-8-sig')
print("分析完成，結果已儲存為本地端 CSV 檔案：dataresult.csv")