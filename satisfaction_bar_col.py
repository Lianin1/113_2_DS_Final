import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 設定字體為程式同目錄下的 NotoSansTC-Regular.ttf
font_path = os.path.join(os.path.dirname(__file__), 'msjh.ttc')
if not os.path.exists(font_path):
    raise FileNotFoundError("找不到 msjh.ttc 字型檔案，請將其放在與程式相同的資料夾內。")

font_prop = fm.FontProperties(fname=font_path)

# 讀取 CSV 檔案
csv_file = 'dataresult1.csv'
if not os.path.exists(csv_file):
    raise FileNotFoundError(f"找不到檔案：{csv_file}，請確保檔案位於程式同一資料夾")
df = pd.read_csv(csv_file, encoding='utf-8')

# ❌ 不再需要 Level 映射
# level_map = {...}
# df['職級'] = df['Level'].map(level_map)

# 創建輸出資料夾
output_dir = 'static'
os.makedirs(output_dir, exist_ok=True)

# 定義需要分析的滿意度欄位
satisfaction_columns = {
    '工作環境滿意度': '工作環境滿意度平均分數',
    '薪資福利滿意度': '薪資福利滿意度平均分數',
    '管理制度滿意度': '管理制度滿意度平均分數',
    '工作與生活平衡': '工作與生活平衡平均分數'
}

# 為每個滿意度欄位生成長條圖
for col, ylabel in satisfaction_columns.items():
    # ✅ 直接使用 Level 欄位（已經是中文）
    avg_by_level = df.groupby('Level')[col].mean().reindex(['初階', '中階', '高階']).reset_index()
    
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 6))
    bars = sns.barplot(x='Level', y=col, data=avg_by_level, palette='pastel')
    
    for bar in bars.patches:
        height = bar.get_height()
        bars.annotate(
            f'{height:.2f}', 
            (bar.get_x() + bar.get_width() / 2, height),
            ha='center', va='bottom', fontsize=12, fontproperties=font_prop
        )
    
    plt.ylim(0, 5)
    plt.yticks(range(1, 6), fontsize=12)
    plt.title(f'不同職級的 {col} 比較', fontsize=14, pad=20, fontproperties=font_prop)
    plt.xlabel('職級', fontsize=12, fontproperties=font_prop)
    plt.ylabel(ylabel, fontsize=12, fontproperties=font_prop)
    plt.xticks(fontproperties=font_prop)
    
    output_path = os.path.join(output_dir, f'satisfaction_bar_{col}.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=100)
    plt.close()
    
    print(f"{col} 的長條圖已儲存至：{output_path}")

print("所有長條圖生成完成！")
