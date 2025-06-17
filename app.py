from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import serial
import serial.tools.list_ports
import time
import logging
import threading

# 設定日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 啟用 CORS 支援
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 自動重新載入模板

# Arduino 連接鎖
arduino_lock = threading.Lock()
arduino = None

def init_arduino():
    """初始化並測試 Arduino 連接"""
    global arduino
    try:
        with arduino_lock:
            # 如果已經有連接，先關閉
            if arduino:
                try:
                    arduino.close()
                except:
                    pass
                arduino = None

            # 自動尋找 Arduino 端口
            ports = list(serial.tools.list_ports.comports())
            arduino_port = None
            for p in ports:
                if 'usbmodem' in p.device.lower() or 'cu.usbmodem' in p.device.lower():
                    arduino_port = p.device
                    break

            if not arduino_port:
                logger.error("找不到 Arduino 設備")
                return None

            # 建立連接並重試最多3次
            for attempt in range(3):
                try:
                    arduino = serial.Serial(arduino_port, 9600, timeout=1)
                    time.sleep(2)  # 等待 Arduino 重置
                    
                    # 測試連接
                    arduino.write(b"TEST\n")
                    response = arduino.readline().decode().strip()
                    if response == "TEST_OK":
                        logger.info(f"Arduino 連接成功: {arduino_port}")
                        return arduino
                    else:
                        logger.warning(f"Arduino 測試失敗，嘗試 {attempt + 1}/3: {response}")
                        arduino.close()
                except Exception as e:
                    logger.warning(f"連接嘗試 {attempt + 1}/3 失敗: {str(e)}")
                    if arduino:
                        arduino.close()
                    time.sleep(1)
            
            logger.error("Arduino 連接失敗，已重試3次")
            return None
            
    except Exception as e:
        logger.error(f"Arduino 連接錯誤: {str(e)}")
        return None

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"模板渲染錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'頁面載入錯誤: {str(e)}'
        }), 500

@app.route('/status')
def status():
    """檢查 Arduino 連接狀態"""
    global arduino
    try:
        if not arduino:
            arduino = init_arduino()
        
        if arduino:
            return jsonify({
                'status': 'success',
                'message': 'Arduino 已連接'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Arduino 未連接'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'狀態檢查錯誤: {str(e)}'
        })

@app.route('/control', methods=['POST'])
def control():
    global arduino
    message = request.json.get('message', '')
    logger.info(f"收到用戶輸入: {message}")

    # 檢查並重試 Arduino 連接
    retry_count = 0
    while not arduino and retry_count < 3:
        arduino = init_arduino()
        retry_count += 1
        if not arduino:
            time.sleep(1)

    if not arduino:
        return jsonify({
            'status': 'error',
            'message': '無法連接 Arduino，請檢查連接',
            'led_status': 'LED 未連接'
        })

    # 決定 LED 模式
    if "久坐" in message or "痛" in message or "累" in message or "不舒服" in message:
        led_command = "WARNING"
        response_message = "請注意！建議您起身活動一下，做些簡單的伸展運動。LED 將以警告模式慢閃提醒。"
    elif "運動" in message or "散步" in message or "伸展" in message:
        led_command = "GOOD"
        response_message = "太棒了！保持運動習慣對健康很有幫助。LED 將以快閃模式表示稱讚。"
    else:
        led_command = "TEST"
        response_message = "收到您的訊息。LED 將閃爍一次表示確認。"

    # 控制 LED
    try:
        with arduino_lock:
            logger.info(f"發送命令到 Arduino: {led_command}")
            arduino.write(f"{led_command}\n".encode())
            
            # 等待 Arduino 完成動作，根據不同模式等待不同時間
            if led_command == "WARNING":
                time.sleep(15)  # 等待 5 次慢閃完成
            elif led_command == "GOOD":
                time.sleep(2)   # 等待 10 次快閃完成
            elif led_command == "TEST":
                time.sleep(1)   # 等待單次閃爍完成
            
            led_status = arduino.readline().decode().strip()
            logger.info(f"Arduino 回應: {led_status}")
            
            # 根據 Arduino 回應決定顯示訊息
            if led_status == "WARNING_DONE":
                status_message = "LED 正在緩慢閃爍，提醒您注意健康！"
            elif led_status == "GOOD_DONE":
                status_message = "LED 快速閃爍，為您的好習慣喝采！"
            elif led_status == "TEST_OK":
                status_message = "LED 已確認閃爍。"
            else:
                status_message = f"LED 狀態: {led_status}"
            
            return jsonify({
                'status': 'success',
                'message': response_message,
                'led_status': status_message
            })
    except Exception as e:
        logger.error(f"Arduino 控制錯誤: {str(e)}")
        # 發生錯誤時重置連接
        try:
            if arduino:
                arduino.close()
            arduino = None
        except:
            pass
        return jsonify({
            'status': 'error',
            'message': f'Arduino 控制錯誤: {str(e)}',
            'led_status': 'LED 控制失敗'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
