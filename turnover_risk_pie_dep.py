import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np

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

# 創建輸出資料夾
output_dir = 'static'
os.makedirs(output_dir, exist_ok=True)

# ✅ 改為使用原始「部門」欄位
departments = df['部門'].unique()
for dept in departments:
    dept_data = df[df['部門'] == dept]
    
    risk_counts = dept_data['離職風險分級'].value_counts().sort_index()
    total_people = len(dept_data)
    
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(6, 6))
    colors = sns.color_palette("pastel", len(risk_counts))
    
    wedges, _ = plt.pie(
        risk_counts,
        startangle=90,
        colors=colors,
        shadow=True,
        explode=[0.05] * len(risk_counts)
    )
    
    for i, wedge in enumerate(wedges):
        theta = (wedge.theta2 + wedge.theta1) / 2
        r = 0.6
        x = r * np.cos(np.radians(theta))
        y = r * np.sin(np.radians(theta))
        level = risk_counts.index[i]
        count = risk_counts.iloc[i]
        percentage = (count / total_people) * 100
        label = f'風險分級 {level}\n{percentage:.1f}%\n{count} 人'
        plt.text(x, y, label, ha='center', va='center', fontsize=10,
                 fontproperties=font_prop, color='black')
    
    plt.title(f'{dept} 部門離職風險分級占比\n(總人數：{total_people} 人)',
              fontsize=14, pad=20, fontproperties=font_prop)
    plt.axis('equal')
    
    output_path = os.path.join(output_dir, f'turnover_risk_pie_{dept}.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=100)
    plt.close()
    
    print(f"{dept} 部門的圖表已儲存至：{output_path}")

print("所有部門的圖表生成完成！")
