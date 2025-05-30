import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ✅ 設定字體為程式同目錄下的 NotoSansTC-Regular.ttf
font_path = os.path.join(os.path.dirname(__file__), 'msjh.ttc')
if not os.path.exists(font_path):
    raise FileNotFoundError("找不到 msjh.ttc 字型檔案，請將其放在與程式相同的資料夾內。")

font_prop = fm.FontProperties(fname=font_path)

# 讀取 CSV 檔案
csv_file = 'dataresult1.csv'
if not os.path.exists(csv_file):
    raise FileNotFoundError(f"找不到檔案：{csv_file}，請確保檔案位於程式同一資料夾")
df = pd.read_csv(csv_file, encoding='utf-8')

# 創建輸出資料夾
output_dir = 'static'
os.makedirs(output_dir, exist_ok=True)

# 定義需要分析的滿意度欄位及其對應顏色
satisfaction_columns = {
    '工作環境滿意度': '#66b3ff',
    '薪資福利滿意度': '#99ff99',
    '管理制度滿意度': '#ffcc99',
    '工作與生活平衡': '#ff99cc'
}

# 為每個滿意度欄位生成長條圖
for col, color in satisfaction_columns.items():
    counts = df[col].value_counts().sort_index()
    mean_score = df[col].mean()
    median_score = df[col].median()

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 6))
    bars = sns.countplot(x=col, data=df, color=color, order=[1, 2, 3, 4, 5])

    for bar in bars.patches:
        height = bar.get_height()
        bars.annotate(
            f'{int(height)} 人',
            (bar.get_x() + bar.get_width() / 2, height),
            ha='center', va='bottom', fontsize=12, fontproperties=font_prop
        )

    max_count = counts.max()
    plt.ylim(0, max_count + 2)
    plt.yticks(range(0, int(max_count) + 1, 5 if max_count > 10 else 1), fontsize=12)

    stats_text = f'平均分數：{mean_score:.2f}\n中位數：{median_score:.1f}'
    plt.text(0.95, 0.95, stats_text, transform=plt.gca().transAxes,
             fontsize=12, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
             fontproperties=font_prop)

    plt.title(f'{col} 的人數分布', fontsize=14, pad=20, fontproperties=font_prop)
    plt.xlabel('滿意度分數', fontsize=12, fontproperties=font_prop)
    plt.ylabel('人數', fontsize=12, fontproperties=font_prop)
    plt.xticks(fontproperties=font_prop)

    output_path = os.path.join(output_dir, f'histogram_{col}.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=100)
    plt.close()

    print(f"{col} 的長條圖已儲存至：{output_path}")

print("所有長條圖生成完成！")
