from flask import Flask, request, jsonify, send_file, send_from_directory
import subprocess
import os
import time
from threading import Thread
import socketio

app = Flask(__name__, static_folder='template')
sio = socketio.Server(cors_allowed_origins='*')
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# 確保必要的目錄存在
os.makedirs('static', exist_ok=True)

def run_script(command):
    """執行指定的命令"""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        error_message = f"執行命令時發生錯誤: {e}\n錯誤輸出: {e.stderr}"
        print(error_message)
        sio.emit('error', error_message)
        return False
    except Exception as e:
        error_message = f"執行命令時發生未預期的錯誤: {str(e)}"
        print(error_message)
        sio.emit('error', error_message)
        return False

def process_data(sheet_id):
    """處理數據的完整流程"""
    try:
        # 1. 執行 Auto.py，傳入 sheet_id
        sio.emit('status_update', {'status': '正在處理 Google Sheet 資料...', 'progress': 20})
        if not run_script(['python', 'Auto.py', sheet_id]):
            sio.emit('error', '處理 Google Sheet 資料時發生錯誤')
            return False
        
        # 2. 執行 HRanalyze.py
        sio.emit('status_update', {'status': '正在分析人力資源資料...', 'progress': 40})
        if not run_script(['python', 'HRanalyze.py']):
            sio.emit('error', '分析人力資源資料時發生錯誤')
            return False
        
        # 3. 並行執行報告生成和圖表生成
        def generate_reports():
            sio.emit('status_update', {'status': '正在生成分析報告...', 'progress': 60})
            run_script(['python', 'hr_analysis_feedback.py'])
        
        def generate_charts():
            # 執行所有圖表生成腳本
            sio.emit('status_update', {'status': '正在生成圖表...', 'progress': 70})
            chart_scripts = [
                'boxplot_col.py',
                'histogram_col.py',
                'satisfaction_bar_col.py',
                'turnover_risk_bar_chart.py',
                'turnover_risk_pie_dep.py'
            ]
            for script in chart_scripts:
                run_script(['python', script])
            # 最後執行圖表分析
            sio.emit('status_update', {'status': '正在生成圖表分析報告...', 'progress': 80})
            run_script(['python', 'chart_analysis.py'])
        
        # 創建並啟動線程
        report_thread = Thread(target=generate_reports)
        chart_thread = Thread(target=generate_charts)
        
        report_thread.start()
        chart_thread.start()
        
        # 等待兩個線程完成
        report_thread.join()
        chart_thread.join()
        
        sio.emit('status_update', {'status': '所有處理完成！', 'progress': 100})
        sio.emit('report_ready')
        return True
    except Exception as e:
        print(f"處理數據時發生錯誤: {e}")
        sio.emit('error', str(e))
        return False

@app.route('/')
def index():
    """提供主頁面"""
    return send_from_directory('template', 'Index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """處理 Google Sheet ID 上傳"""
    data = request.get_json()
    sheet_id = data.get('url')
    
    if not sheet_id:
        return jsonify({'success': False, 'error': '未提供 Sheet ID'})
    
    # 啟動數據處理
    thread = Thread(target=process_data, args=(sheet_id,))
    thread.start()
    
    return jsonify({'success': True})

@app.route('/download/<file_type>')
def download_file(file_type):
    """處理文件下載請求"""
    file_map = {
        'report1': '圖表報告.pdf',
        'report2': '分析建議報告.pdf',
        'report3': '問卷設計建議.pdf'
    }
    
    filename = file_map.get(file_type)
    if not filename or not os.path.exists(filename):
        return jsonify({'error': '文件不存在'}), 404
    
    return send_file(filename, as_attachment=True)

@sio.on('generate_report')
def handle_generate_report(sid):
    """處理報告生成請求"""
    # 檢查所有必要的文件是否都已生成
    required_files = [
        '圖表報告.pdf',
        '分析建議報告.pdf',
        '問卷設計建議.pdf'
    ]
    
    def check_files():
        while True:
            if all(os.path.exists(f) for f in required_files):
                sio.emit('report_ready')
                break
            time.sleep(1)
    
    thread = Thread(target=check_files)
    thread.start()

if __name__ == '__main__':
    app.run(debug=True) 