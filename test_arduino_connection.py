import serial
import time

def test_arduino_connection():
    try:
        # 嘗試打開串口
        arduino = serial.Serial('/dev/cu.usbmodem101', 9600, timeout=1)
        print(f"成功打開串口：{arduino.name}")
        
        # 等待 Arduino 重置
        time.sleep(2)
        
        # 傳送測試命令
        print("傳送測試命令...")
        arduino.write(b"TEST\n")
        
        # 讀取回應
        response = arduino.readline().decode().strip()
        print(f"Arduino 回應: {response}")
        
        arduino.close()
        print("串口已關閉")
        
    except Exception as e:
        print(f"錯誤: {str(e)}")

if __name__ == "__main__":
    test_arduino_connection()
