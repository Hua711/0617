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
            logger.info("開始初始化 Arduino 連接...")
            
            # 如果已經有連接，先關閉
            if arduino:
                try:
                    arduino.close()
                    logger.info("關閉現有連接")
                except Exception as e:
                    logger.warning(f"關閉現有連接時出錯: {str(e)}")
                arduino = None

            # 自動尋找 Arduino 端口
            ports = list(serial.tools.list_ports.comports())
            logger.info(f"找到的串口列表: {[p.device for p in ports]}")
            
            arduino_port = None
            for p in ports:
                logger.info(f"檢查串口 {p.device}...")
                if 'usbmodem' in p.device.lower():
                    arduino_port = p.device
                    logger.info(f"找到 Arduino 端口: {arduino_port}")
                    break

            if not arduino_port:
                logger.error("找不到 Arduino 設備")
                return None

            # 建立連接並重試最多3次
            for attempt in range(3):
                try:
                    logger.info(f"嘗試連接 Arduino ({attempt + 1}/3)...")
                    arduino = serial.Serial(arduino_port, 9600, timeout=3)
                    logger.info("串口打開成功")
                    time.sleep(2)  # 等待 Arduino 重置
                    
                    # 清空緩衝區
                    arduino.flushInput()
                    arduino.flushOutput()
                    
                    # 等待 Arduino 就緒訊息
                    for _ in range(5):  # 最多等待 5 個訊息
                        if arduino.in_waiting:
                            response = arduino.readline().decode().strip()
                            logger.info(f"收到 Arduino 訊息: {response}")
                            if "Arduino ready!" in response:
                                logger.info("Arduino 已就緒！")
                                break
                    
                    # 測試連接
                    logger.info("發送測試命令...")
                    arduino.write(b"TEST\n")
                    
                    # 等待回應
                    start_time = time.time()
                    while time.time() - start_time < 3:  # 最多等待3秒
                        if arduino.in_waiting:
                            response = arduino.readline().decode().strip()
                            logger.info(f"收到測試回應: {response}")
                            if response == "TEST_OK":
                                logger.info("連接測試成功！")
                                return arduino
                    
                    logger.warning("未收到正確的測試回應")
                    
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
def index():
    return render_template('index.html')

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
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        
        # 初始化回應
        response = {
            'command': 'TEST',
            'response': '收到訊息，正在處理...'
        }
        
        # 根據訊息內容決定 LED 模式
        warning_keywords = ['疲倦', '疼痛', '不舒服', '緊繃', '壓力', '頭痛', '眼睛酸', '肩頸痛']
        positive_keywords = [
            '運動', '伸展', '散步', '跑步', '健身', '瑜伽', '騎車', '游泳',
            '休息', '放鬆', '良好', '舒服', '正常',
            '喝水', '起身走動', '伸展操', '休息一下'
        ]
        
        # 判斷訊息類型
        if any(word in message for word in warning_keywords):
            response['command'] = 'WARNING'
            response['response'] = '請注意！建議您立即休息，並做一些伸展運動。'
        elif any(word in message for word in positive_keywords):
            response['command'] = 'GOOD'
            positive_responses = [
                '太棒了！運動對身體很有幫助，繼續保持！',
                '做得好！適時的休息和運動能提高工作效率！',
                '很好的習慣！保持運動能讓身心都更健康！',
                '讚！這些都是很好的健康習慣，請繼續保持！'
            ]
            import random
            response['response'] = random.choice(positive_responses)
        else:
            response['command'] = 'TEST'
            response['response'] = '謝謝您的回饋！我們會持續關注您的健康狀況。'

        # 檢查 Arduino 連接狀態
        if not arduino:
            arduino = init_arduino()
        
        # 控制 Arduino（如果連接成功）
        if arduino:
            try:
                with arduino_lock:
                    # 清空緩衝區
                    arduino.flushInput()
                    arduino.flushOutput()
                    
                    # 發送命令
                    arduino.write(f"{response['command']}\n".encode())
                    time.sleep(0.1)  # 短暫等待確保命令被發送
                    
                    # 嘗試讀取回應（非阻塞）
                    if arduino.in_waiting:
                        arduino_response = arduino.readline().decode().strip()
                        logger.info(f"Arduino 回應: {arduino_response}")
                        
                return jsonify(response)
            except Exception as e:
                logger.error(f"Arduino 通訊錯誤: {str(e)}")
                # Arduino 通訊錯誤，但仍然返回回應
                return jsonify(response)
        else:
            logger.warning("Arduino 未連接，僅返回文字回應")
            # 即使 Arduino 未連接，也返回文字回應
            return jsonify(response)
            
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '系統暫時無法處理請求，但您的輸入已經收到。'
        })

if __name__ == '__main__':
    # 初始化 Arduino
    arduino = init_arduino()
    if not arduino:
        logger.warning("Arduino 初始化失敗，將無法控制 LED")
    
    # 啟動 Flask 應用
    app.run(debug=True, port=5001)
