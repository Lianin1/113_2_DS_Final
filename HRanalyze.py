import os
import json
import time
import pandas as pd
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions
import re # 匯入正規表達式模組

# 載入 .env 中的 GEMINI_API_KEY
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 設定 API 金鑰
if api_key:
    genai.configure(api_key=api_key)
else:
    print("錯誤：未找到 GEMINI_API_KEY。請檢查您的 .env 檔案或環境變數設定。")
    sys.exit(1) # 如果沒有 API key，則終止程式

# 建立模型
try:
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
except Exception as e:
    print(f"建立 GenerativeModel 時發生錯誤: {e}")
    sys.exit(1)


# 評分項目 (確保與 ITEMS 在 parse_response 中一致)
ITEMS = [
    "離職風險分級"
]

def parse_response(response_text: str) -> list | dict:
    """
    從 API 回應文字中提取並解析 JSON 內容。
    優先尋找被 ```json ... ``` 或 ``` ... ``` 包裹的區塊。
    """
    json_payload_str = ""
    
    # 使用正規表達式尋找被 ```json ... ``` 或 ``` ... ``` 包裹的內容。
    # - ```(?:json)? : 匹配 "```" 或 "```json"
    # - \s* : 匹配零或多個空白字元 (包括換行符，因為 re.DOTALL)
    # - (.*?) : 非貪婪模式捕獲任意字元，這是我們想要的 JSON 字串
    # - re.DOTALL : 使 "." 可以匹配換行符
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL)
    
    if match:
        json_payload_str = match.group(1).strip()
        # print(f"DEBUG: Regex 提取到的內容: >>>{json_payload_str[:200]}...<<<") # 用於偵錯
    else:
        # 如果找不到 Markdown 程式碼區塊，可能是因為 LLM 直接回傳了純 JSON，
        # 或者回應格式不符合預期。
        # 在這種情況下，我們嘗試直接解析整個回應文字，但這可能會因為額外文字而失敗。
        print(f"警告：在回應中未找到標準的 JSON 程式碼區塊 (例如 ```json ... ```)。\n將嘗試直接解析整個回應 (如果回應中包含非 JSON 文字，這可能導致錯誤)。\n原始回應片段：\n{response_text[:300]}...")
        json_payload_str = response_text.strip()

    try:
        result = json.loads(json_payload_str)
        
        # 標準化結果結構，確保 ITEMS 中的鍵存在
        if isinstance(result, list):
            for i in range(len(result)):
                if isinstance(result[i], dict):
                    for item_key in ITEMS:
                        if item_key not in result[i]:
                            result[i][item_key] = ""  # 如果項目不存在，則補空值
                else:
                    # 如果列表中的元素不是字典，用預設值替換
                    print(f"警告：JSON 陣列中的第 {i} 個元素不是字典：'{str(result[i])[:50]}...'。將使用預設值。")
                    result[i] = {item_k: "" for item_k in ITEMS}
        elif isinstance(result, dict):
            # 如果 API 回傳單一物件，確保其包含 ITEMS
            for item_key in ITEMS:
                if item_key not in result:
                    result[item_key] = ""
        else:
            # 如果解析結果既不是列表也不是字典 (例如，純數字、字串)，這不符合我們的期望
            print(f"警告：解析後得到的 JSON 既不是預期的列表也不是字典 (實際類型: {type(result)})。將回傳預設空列表。")
            return [{item_k: "" for item_k in ITEMS}] # 保持回傳類型為 list of dict
            
        return result

    except json.JSONDecodeError as e:
        # 解析 JSON 失敗，提供更詳細的錯誤訊息
        error_line = getattr(e, 'lineno', '?')
        error_col = getattr(e, 'colno', '?')
        error_char_pos = getattr(e, 'pos', '?')
        
        print(f"解析 JSON 失敗：{e.msg} (在字元 {error_char_pos}，約行 {error_line}, 欄 {error_col})")
        
        # 顯示錯誤點附近的上下文，有助於偵錯
        context_len = 50
        start_context = max(0, e.pos - context_len if isinstance(e.pos, int) else 0)
        end_context = min(len(json_payload_str), e.pos + context_len if isinstance(e.pos, int) else len(json_payload_str))
        
        if isinstance(e.pos, int) :
            error_context_str = json_payload_str[start_context:e.pos] + "<*JSON_ERROR_HERE*>" + json_payload_str[e.pos:end_context]
            print(f"發生錯誤的字串片段 (錯誤點標記為 <*>):\n...{error_context_str}...")
        else:
            print(f"嘗試解析的字串片段 (前 200 字元):\n>>>\n{json_payload_str[:200]}...\n<<<")

        # print(f"完整的嘗試解析字串：\n>>>\n{json_payload_str}\n<<<") # 完整字串可能很長，謹慎使用
        print(f"原始 API 回應的前 500 字元：\n>>>\n{response_text[:500]}...\n<<<") # 顯示原始 API 回應的開頭
        return [{item_k: "" for item_k in ITEMS}] # 發生錯誤時，回傳包含一個預設字典的列表

    except Exception as e_general: # 捕捉其他在 parse_response 中可能發生的錯誤
        print(f"parse_response 中發生未預期的錯誤: {e_general}")
        print(f"原始 API 回應的前 500 字元：\n>>>\n{response_text[:500]}...\n<<<")
        return [{item_k: "" for item_k in ITEMS}]


# --- select_dialogue_column, process_batch_dialogue, main 函數保持與你上一版修正相似的結構 ---
# 以下為相關函數，確保它們與新的 parse_response 協同工作

def select_dialogue_column(chunk: pd.DataFrame) -> str:
    preferred = ["text", "utterance", "content", "dialogue", "Dialogue"]
    for col in preferred:
        if col in chunk.columns:
            return col
    # print("CSV 欄位：", list(chunk.columns)) # 已在 main 函數中印出
    return chunk.columns[0] if not chunk.columns.empty else "unknown_column"

def process_batch_dialogue(employee_data_list: list, model_instance, delimiter="-----"):
    prompt = (
        "你是一位資深的人資數據分析師。\n"
        "以下是一批員工的基本資料，每一筆代表一位員工，包含以下欄位：\n"
        "- 性別'男': 0, '女': 1\n"
        "- 部門 '人力資源': 0, '財務': 1, '技術': 2, '行銷': 3, '運營': 4\n"
        "- Level '初階': 0, '中階': 1, '高階': 2\n"
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
        "請僅回傳 JSON 陣列，不要包含任何額外的說明文字或註解，格式如下：\n" # 強調僅回傳 JSON
        "```json\n"
        "[\n"
        "  { \"員工編號\": \"E001\", \"離職風險分級\": 3 },\n"
        "  { \"員工編號\": \"E002\", \"離職風險分級\": 5 },\n"
        "  ...\n"
        "]\n"
        "```\n"
        "以下是需要你評估的員工資料："
    )
    batch_text = []
    for employee_json_str in employee_data_list:
        dialogue_text = f"員工資料：{employee_json_str}"
        batch_text.append(dialogue_text)
    content = prompt + "\n\n" + delimiter.join(batch_text)

    try:
        response = model_instance.generate_content(content)
        # print("批次 API 回傳內容：\n", response.text) # 在 parse_response 中印出更詳細的偵錯訊息
        
        parsed_api_output = parse_response(response.text) # 使用更新後的 parse_response

        final_results: list[dict] = []
        if isinstance(parsed_api_output, list):
            final_results = parsed_api_output
        elif isinstance(parsed_api_output, dict):
            final_results = [parsed_api_output] # 包裝成列表
        else:
            # parse_response 在錯誤時應回傳 list of dict
            # 但以防萬一，如果回傳了非預期類型
            print(f"警告：parse_response 回傳了非預期類型 {type(parsed_api_output)}。為此批次中的每個項目使用預設空值。")
            final_results = [{item_k: "" for item_k in ITEMS} for _ in employee_data_list]

        num_employees_in_batch = len(employee_data_list)
        if len(final_results) != num_employees_in_batch:
            print(f"警告：API 回傳的資料筆數 ({len(final_results)}) 與預期的批次大小 ({num_employees_in_batch}) 不符。將進行調整。")
            if len(final_results) > num_employees_in_batch:
                final_results = final_results[:num_employees_in_batch]
            else:
                missing_count = num_employees_in_batch - len(final_results)
                default_entry = {item_key: "" for item_key in ITEMS}
                final_results.extend([default_entry.copy() for _ in range(missing_count)])
        
        return final_results
        
    except exceptions.GoogleAPIError as e:
        print(f"對 Google API 的呼叫失敗：{e}")
        return [{item_k: "" for item_k in ITEMS} for _ in employee_data_list]
    except Exception as e:
        print(f"處理批次資料時發生未預期錯誤：{e}")
        import traceback
        traceback.print_exc()
        return [{item_k: "" for item_k in ITEMS} for _ in employee_data_list]

def main():
    input_csv = "dataresult.csv"
    output_csv = "dataresult1.csv"

    if os.path.exists(output_csv):
        try:
            os.remove(output_csv)
        except OSError as e:
            print(f"無法刪除舊的輸出檔案 {output_csv}: {e}")
            return


    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"錯誤：找不到輸入的 CSV 檔案 {input_csv}")
        return
    except pd.errors.EmptyDataError:
        print(f"錯誤：輸入的 CSV 檔案 {input_csv} 為空。")
        return
    except Exception as e:
        print(f"讀取 CSV 檔案 {input_csv} 時發生錯誤: {e}")
        return
        
    print("CSV 欄位：", list(df.columns))
    dialogue_col = select_dialogue_column(df) 
    print(f"選擇 '{dialogue_col}' 欄位 (注意：此選擇目前未直接用於建構 API 的主要內容)。")

    batch_size = 10
    total = len(df)

    if total == 0:
        print("輸入的 CSV 檔案沒有資料可處理。")
        return

    # 在迴圈外初始化 model (已移到全域)
    # global model # 如果 model 是在 main 外部定義的

    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]
        
        try:
            employee_data = batch.apply(
                lambda row: json.dumps({
                    "員工編號": row["員工編號"],
                    "性別": row["性別"],
                    "部門": row["部門"],
                    "Level": row["Level"],
                    "工作環境滿意度": row["工作環境滿意度"],
                    "薪資福利滿意度": row["薪資福利滿意度"],
                    "管理制度滿意度": row["管理制度滿意度"],
                    "工作與生活平衡": row["工作與生活平衡"],
                    "回饋情緒分數": row["回饋情緒分數"]
                }, ensure_ascii=False), axis=1
            ).tolist()
        except KeyError as e:
            print(f"處理 CSV 資料時發生 KeyError: 欄位 {e} 不存在。請檢查 CSV 欄位名稱是否與程式碼中的預期一致。")
            return # 或者跳過此批次


        batch_results = process_batch_dialogue(employee_data, model) # model 現在是全域變數
        
        batch_df = batch.copy()
        for item_key_to_extract in ITEMS:
            extracted_values = []
            for res_dict in batch_results:
                if isinstance(res_dict, dict):
                    extracted_values.append(res_dict.get(item_key_to_extract, ""))
                else:
                    print(f"警告：batch_results 中發現非字典元素：{res_dict}。將為 '{item_key_to_extract}' 使用空字串。")
                    extracted_values.append("")
            batch_df[item_key_to_extract] = extracted_values

        try:
            if start_idx == 0:
                batch_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
            else:
                batch_df.to_csv(output_csv, mode='a', index=False, header=False, encoding="utf-8-sig")
        except IOError as e:
            print(f"寫入 CSV 檔案 {output_csv} 時發生錯誤: {e}")
            # 考慮是否要終止或繼續處理下一批次

        print(f"已處理 {end_idx} 筆 / {total}")
        if end_idx < total: # 只有在還有下一批次時才延遲
            time.sleep(1) 

    print("全部處理完成。最終結果已寫入：", output_csv)

if __name__ == "__main__":
    main()