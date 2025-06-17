from flask import Flask, render_template, request, jsonify
import serial
import time

app = Flask(__name__)

# 設定 Arduino 序列通訊
try:
    arduino = serial.Serial('/dev/cu.usbmodem1101', 9600)  # MacOS 路徑
    time.sleep(2)  # 等待 Arduino 初始化
except:
    print("無法連接 Arduino，請確認連接埠是否正確")
    arduino = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    if not arduino:
        return jsonify({'status': 'error', 'message': '無法連接 Arduino'})

    command = request.json.get('command')
    if command in ['ON', 'OFF', 'BLINK', 'STATUS']:
        try:
            arduino.write(f"{command}\n".encode())
            time.sleep(0.1)  # 等待 Arduino 處理
            response = arduino.readline().decode().strip()
            return jsonify({'status': 'success', 'message': response})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    else:
        return jsonify({'status': 'error', 'message': '無效的命令'})

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        if arduino:
            arduino.close()
