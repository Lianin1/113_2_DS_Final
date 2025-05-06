import os
import json
from dotenv import load_dotenv
import pandas as pd
from snownlp import SnowNLP
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 載入 .env
load_dotenv()

# 從 .env 取得 JSON 串
google_json_raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
google_json_dict = json.loads(google_json_raw)

# 建立憑證
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_json_dict, scope)
client = gspread.authorize(creds)

# 你的 Google Sheet ID（原始資料）與目標寫入試算表 ID
input_sheet_id = "1W1c9d6bVet8Lhdb69NbUHjkFxVOdrYOu5VV-xRVh91g"       # TODO: 替換成實際ID
input_ws = client.open_by_key(input_sheet_id).sheet1


# 讀取原始回饋資料

data = input_ws.get_all_records()
df = pd.DataFrame(data)

# 題目欄位與簡化欄名
original_cols = [
    "您認為目前工作的挑戰性如何？請詳細描述您的看法。",
    "在目前的工作環境中，您最喜歡的部分是什麼？為什麼？",
    "您對目前團隊合作的感受如何？請詳細說明。",
    "您認為公司提供的資源與支持足夠嗎？請說明具體情況。",
    "如果您能改進公司的一個方面，會是什麼？請具體描述您的建議。",
    "其他反饋：請分享您對公司或工作的任何建議或想法。"
]
short_score_cols = [f"Q{i+1}_情緒分數" for i in range(6)]

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

# 對應表
gender_map = {'男': 0, '女': 1}
department_map = {'人力資源': 0, '財務': 1, '技術': 2, '行銷': 3, '營運': 4, '運營': 4}
level_map = {'初階': 0, '中階': 1, '高階': 2}

# 轉換欄位
df['性別'] = df['性別'].map(gender_map)
df['部門'] = df['部門'].map(department_map)
df['Level'] = df['Level'].map(level_map)

# 組成輸出 DataFrame
result_cols = ["員工編號"] + ['性別'] + ['部門'] + ['Level'] + ['工作環境滿意度'] + ['薪資福利滿意度'] + ['管理制度滿意度'] + ['工作與生活平衡'] + ["回饋情緒分數"]
result_df = df[result_cols]

# 將結果儲存成 CSV 檔案
result_df.to_csv("dataresult.csv", index=False, encoding='utf-8-sig')
print("✅ 分析完成，結果已儲存為本地端 CSV 檔案：dataresult.csv")