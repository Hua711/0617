import serial
import time

def test_arduino():
    try:
        # 自動尋找 Arduino 端口
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        arduino_port = None
        
        print("可用的序列埠：")
        for p in ports:
            print(f"- {p.device}")
            if 'usbmodem' in p.device.lower():  # Mac 上的 Arduino 通常包含 'usbmodem'
                arduino_port = p.device
        
        if not arduino_port:
            print("\n找不到 Arduino，請確保 Arduino 已連接")
            return
            
        print(f"\n使用端口：{arduino_port}")
        arduino = serial.Serial(arduino_port, 9600)
        time.sleep(2)  # 等待 Arduino 重置
        
        # 測試命令
        tests = [
            ("TEST", "測試連接"),
            ("WARNING", "測試警告模式"),
            ("GOOD", "測試鼓勵模式")
        ]
        
        for cmd, desc in tests:
            print(f"\n{desc}...")
            arduino.write(f"{cmd}\n".encode())
            response = arduino.readline().decode().strip()
            print(f"Arduino 回應: {response}")
            time.sleep(3)  # 等待動畫完成
            
        print("\n測試完成！")
        arduino.close()
        
    except Exception as e:
        print(f"錯誤：{str(e)}")

if __name__ == "__main__":
    test_arduino()
