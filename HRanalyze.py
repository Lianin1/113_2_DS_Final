import os
import json
import time
import pandas as pd
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions

# 載入 .env 中的 GEMINI_API_KEY
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 設定 API 金鑰
genai.configure(api_key=api_key)

# 建立模型
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

#HW2
# 評分項目（僅字彙）
ITEMS = [
    "離職風險等級"
]

def parse_response(response_text):
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        result = json.loads(cleaned)
        for item in ITEMS:
            if item not in result:
                result[item] = ""
        return result
    except Exception as e:
        print(f"解析 JSON 失敗：{e}")
        print("原始回傳內容：", response_text)
        return {item: "" for item in ITEMS}

def select_dialogue_column(chunk: pd.DataFrame) -> str:
    preferred = ["text", "utterance", "content", "dialogue", "Dialogue"]
    for col in preferred:
        if col in chunk.columns:
            return col
    print("CSV 欄位：", list(chunk.columns))
    return chunk.columns[0]

def process_batch_dialogue(dialogues: list, model, delimiter="-----"):
    prompt = (
        "你是一位資深的人資數據分析師。\n"
        "以下是一批員工的基本資料，每一筆代表一位員工，包含以下欄位：\n"
        "- 所屬部門（如：人資部、財務部等）\n"
        "- 職位（如：專員、經理、助理等）\n"
        "- 性別（男／女）\n"
        "- 工作環境滿意度（0~5 分）\n"
        "- 薪資福利滿意度（0~5 分）\n"
        "- 管理制度滿意度（0~5 分）\n"
        "- 工作與生活平衡（0~5 分）\n"
        "- 回饋情緒分數（-1 到 1 之間，數字越負面代表情緒越差）\n\n"
        "請你根據這些資料分析每位員工的離職風險，並以 1 到 5 的數字表示：\n"
        "- 1：極低離職風險\n"
        "- 2：偏低離職風險\n"
        "- 3：中等離職風險\n"
        "- 4：偏高離職風險\n"
        "- 5：極高離職風險\n\n"
        "請以 JSON 陣列方式回覆，格式如下：\n"
        "```json\n"
        "[\n"
        "  { \"員工編號\": \"E001\", \"離職風險等級\": 3 },\n"
        "  { \"員工編號\": \"E002\", \"離職風險等級\": 5 },\n"
        "  ...\n"
        "]\n"
        "```\n"
        "以下是需要你評估的員工資料："
    )
    batch_text = f"\n-----\n".join(dialogues)
    content = prompt + "\n\n" + batch_text

    try:
        response = model.generate_content(content)
        print("批次 API 回傳內容：", response.text)
        parts = response.text.split("-----")
        results = []
        for part in parts:
            part = part.strip()
            if part:
                results.append(parse_response(part))
        if len(results) > len(dialogues):
            results = results[:len(dialogues)]
        elif len(results) < len(dialogues):
            results.extend([{item: "" for item in ITEMS}] * (len(dialogues) - len(results)))
        return results
    except exceptions.GoogleAPIError as e:
        print(f"API 呼叫失敗：{e}")
        return [{item: "" for item in ITEMS} for _ in dialogues]

def main():
    if len(sys.argv) < 2:
        print("Usage: python DRai.py <path_to_csv>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = "人資數據HR.csv"
    summary_csv = "統計結果_summary.csv"

    if os.path.exists(output_csv):
        os.remove(output_csv)
    if os.path.exists(summary_csv):
        os.remove(summary_csv)

    df = pd.read_csv(input_csv)
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("請設定環境變數 GEMINI_API_KEY")

    dialogue_col = select_dialogue_column(df)
    print(f"使用欄位作為逐字稿：{dialogue_col}")

    batch_size = 10
    total = len(df)

    # 初始化計數器
    total_counts = {item: 0 for item in ITEMS}

    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]
        dialogues = batch[dialogue_col].tolist()
        dialogues = [str(d).strip() for d in dialogues]
        batch_results = process_batch_dialogue(dialogues, model)
        batch_df = batch.copy()
        for item in ITEMS:
            batch_df[item] = [res.get(item, "") for res in batch_results]

        # 累加統計數據
        for result in batch_results:
            for item in ITEMS:
                if result.get(item, "") == "1":
                    total_counts[item] += 1

        if start_idx == 0:
            batch_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        else:
            batch_df.to_csv(output_csv, mode='a', index=False, header=False, encoding="utf-8-sig")

        print(f"已處理 {end_idx} 筆 / {total}")
        time.sleep(1)

    # 輸出統計數據
    pd.DataFrame([total_counts]).to_csv(summary_csv, index=False, encoding="utf-8-sig")
    print("全部處理完成。最終結果已寫入：", output_csv)
    print("統計結果已寫入：", summary_csv)

if __name__ == "__main__":
    main()