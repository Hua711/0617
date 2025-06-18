import serial
import time
import logging

# 設定日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_led():
    try:
        # 嘗試連接 Arduino
        port = '/dev/cu.usbmodem101'  # 使用我們看到的端口
        logger.info(f"嘗試連接到 {port}...")
        
        arduino = serial.Serial(port, 9600, timeout=1)
        logger.info("連接成功，等待 Arduino 重置...")
        time.sleep(2)  # 等待 Arduino 重置
        
        # 測試不同的 LED 模式
        tests = [
            ("WARNING", "警告模式 - 快閃 15 次"),
            ("GOOD", "鼓勵模式 - 慢閃 5 次"),
            ("TEST", "測試模式 - 單次閃爍")
        ]
        
        for command, description in tests:
            logger.info(f"\n測試 {description}")
            logger.info(f"發送命令: {command}")
            
            arduino.write(f"{command}\n".encode())
            time.sleep(0.1)
            
            response = arduino.readline().decode().strip()
            logger.info(f"收到回應: {response}")
            
            # 根據模式等待適當的時間
            if command == "WARNING":
                time.sleep(3)   # 15 次快閃
            elif command == "GOOD":
                time.sleep(15)  # 5 次慢閃
            elif command == "TEST":
                time.sleep(1)   # 單次閃爍
                
        arduino.close()
        logger.info("測試完成，串口已關閉")
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")

if __name__ == "__main__":
    test_led()
