import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np

# ✅ 改用 NotoSansTC-Regular.ttf（推薦使用開源字型）
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

# 定義滿意度欄位與色系
satisfaction_columns = {
    '工作環境滿意度': ['#cce6ff', '#99ccff', '#66b3ff', '#3399ff', '#0066cc'],
    '薪資福利滿意度': ['#ccffcc', '#99ff99', '#66ff66', '#33cc33', '#009900'],
    '管理制度滿意度': ['#ffebcc', '#ffd699', '#ffc266', '#ffad33', '#ff9900'],
    '工作與生活平衡': ['#ffe6f0', '#ffccdd', '#ffb3cc', '#ff99bb', '#ff80aa']
}

for col, colors in satisfaction_columns.items():
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    plt.subplots_adjust(right=0.75)

    # ✅ 使用「部門」欄位而非「部門名稱」
    box_plot = sns.boxplot(x='部門', y=col, data=df, palette=colors, width=0.5)
    sns.stripplot(x='部門', y=col, data=df, color='black', alpha=0.6, size=5)

    outliers_count = 0
    for i, department in enumerate(df['部門'].unique()):
        dept_data = df[df['部門'] == department][col]
        q1 = dept_data.quantile(0.25)
        q3 = dept_data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = dept_data[(dept_data < lower_bound) | (dept_data > upper_bound)]
        outliers_count += len(outliers)
        for outlier in outliers:
            y_pos = outlier
            x_pos = i + (np.random.uniform(-0.1, 0.1))
            plt.text(x_pos, y_pos, f'{int(outlier)}', ha='center', va='bottom',
                     fontsize=10, fontproperties=font_prop, color='red')

    mean_scores = df.groupby('部門')[col].mean()
    stats_text = '平均分數：\n'
    for dept, mean in mean_scores.items():
        stats_text += f'{dept}: {mean:.2f}\n'
    stats_text += f'異常值數量：{outliers_count}'

    plt.text(1.05, 0.95, stats_text, transform=plt.gca().transAxes,
             fontsize=12, verticalalignment='top', horizontalalignment='left',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
             fontproperties=font_prop)

    plt.ylim(0.5, 5.5)
    plt.yticks([1, 2, 3, 4, 5], fontsize=12)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)

    plt.title(f'各部門的 {col} 評分分布', fontsize=14, pad=20, fontproperties=font_prop)
    plt.xlabel('部門', fontsize=12, fontproperties=font_prop)
    plt.ylabel(f'{col} 評分', fontsize=12, fontproperties=font_prop)
    plt.xticks(fontproperties=font_prop)

    output_path = os.path.join(output_dir, f'boxplot_{col}.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=100)
    plt.close()

    print(f"{col} 的箱型圖已儲存至：{output_path}")

print("所有箱型圖生成完成！")
