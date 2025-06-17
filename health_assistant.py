import serial
import time
import openai

# 設定 OpenAI API
openai.api_key = 'YOUR_API_KEY'  # 請替換成您的 API 金鑰

# 設定 Arduino 序列通訊
try:
    arduino = serial.Serial('/dev/cu.usbmodem1101', 9600)  # MacOS 路徑，Windows 一般是 'COM3' 之類
    time.sleep(2)  # 等待 Arduino 初始化
except:
    print("無法連接 Arduino，請確認連接埠是否正確")
    arduino = None

def analyze_input(text):
    """分析使用者輸入，判斷應該觸發哪種 LED 模式"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個健康助手，需要判斷用戶的輸入是否表示：1. 不良的習慣（久坐、姿勢不良等）2. 良好的習慣（運動、正確姿勢等）"},
                {"role": "user", "content": text}
            ]
        )
        
        analysis = response.choices[0].message['content'].lower()
        
        # 簡單的關鍵字判斷
        if any(word in analysis for word in ['久坐', '疲勞', '不良', '痛', '累']):
            return '1', "提醒：請注意姿勢，適時休息和活動。"
        elif any(word in analysis for word in ['運動', '散步', '伸展', '很好']):
            return '2', "做得好！繼續保持這個好習慣。"
        else:
            return None, "謝謝分享！請繼續保持健康的生活習慣。"
    
    except Exception as e:
        print(f"API 錯誤：{e}")
        # 如果 API 出錯，使用簡單的關鍵字判斷
        if any(word in text for word in ['久坐', '疲勞', '不良', '痛', '累']):
            return '1', "提醒：請注意姿勢，適時休息和活動。"
        elif any(word in text for word in ['運動', '散步', '伸展']):
            return '2', "做得好！繼續保持這個好習慣。"
        return None, "謝謝分享！請繼續保持健康的生活習慣。"

def main():
    print("歡迎使用健康互動小幫手！")
    print("請分享您今天的姿勢和運動情況（輸入 'exit' 結束）")
    
    while True:
        user_input = input("\n您的分享：")
        if user_input.lower() == 'exit':
            break
            
        mode, response = analyze_input(user_input)
        print(f"\nAI回應：{response}")
        
        if arduino and mode:
            try:
                arduino.write(mode.encode())
                time.sleep(0.1)  # 確保命令有被送出
            except:
                print("無法控制 LED，請檢查連接")

if __name__ == "__main__":
    try:
        main()
    finally:
        if arduino:
            arduino.close()
