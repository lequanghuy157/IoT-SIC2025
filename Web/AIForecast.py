import joblib
import pandas as pd
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# --- TẢI CẢ HAI MÔ HÌNH MỘT LẦN KHI FILE ĐƯỢC IMPORT ---
try:
    #Ước tính AQI từ các chất gây ô nhiễm
    aqi_estimator = joblib.load("aqi_estimator_model.pkl")
    #Dự đoán Điểm sức khỏe từ AQI, Nhiệt độ, Độ ẩm
    health_predictor = joblib.load("health_predictor_model.pkl") 

except FileNotFoundError as e:
    print(f"[AI Forecast] LỖI QUAN TRỌNG: Không tìm thấy file model. Hãy chắc chắn cả 2 file .pkl đều tồn tại.")
    print(f"Lỗi chi tiết: {e}")
    aqi_estimator = None
    health_predictor = None

# --- CẤU HÌNH API ---
API_KEY = "1d682ebed5af4db5aae82919250408"
LOCATION = "Hanoi"

def get_ai_health_score_real():

    
    if not aqi_estimator or not health_predictor:
        print("[AI Forecast] Không thể dự đoán vì một hoặc cả hai model chưa được tải.")
        return None

    # Gọi API để lấy dữ liệu thô 
    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={LOCATION}&days=1&aqi=yes&alerts=no"
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()

    except requests.exceptions.RequestException as e:

        return "API hết hạn rồi @@"

    try:        
        current = data["current"]
        aq_from_api = current["air_quality"]

        # 1. Chuẩn bị dữ liệu đầu vào cho mô hình ước tính AQI
        features_for_aqi = {
            'PM10': [aq_from_api.get("pm10", 0)],
            'PM2_5': [aq_from_api.get("pm2_5", 0)],
            'NO2': [aq_from_api.get("no2", 0)],
            'SO2': [aq_from_api.get("so2", 0)],
            'O3': [aq_from_api.get("o3", 0)]
        }
        df_for_aqi = pd.DataFrame(features_for_aqi)

        # 2. Ước tính giá trị AQI
        estimated_aqi = aqi_estimator.predict(df_for_aqi)[0]

        # 1. Chuẩn bị dữ liệu đầu vào cho mô hình dự đoán sức khỏe
        features_for_health = {
            'AQI': [estimated_aqi],
            'Temperature': [current.get("temp_c", 0)],
            'Humidity': [current.get("humidity", 0)]
        }
        df_for_health = pd.DataFrame(features_for_health)

        # 2. Dự đoán điểm sức khỏe cuối cùng
        predicted_score = health_predictor.predict(df_for_health)[0]
        
        final_score = predicted_score
        return final_score
        
    except (KeyError, Exception) as e:
        print(f"[AI Forecast] Lỗi trong quá trình xử lý dữ liệu hoặc dự đoán: {e}")
        return None
#test
if __name__ == '__main__':

    score = get_ai_health_score_real()
    
    if score is not None:
        print(f"\n>>> Kết quả kiểm tra: Điểm sức khỏe dự đoán là {score:.2f}")
    else:
        print("\n>>> Kiểm tra thất bại. Vui lòng xem lại các lỗi bên trên.")
#final equation
def get_ai_health_score(aqi, temperature, humidity):
    features_for_health = {
            'AQI': [aqi],
            'Temperature': [temperature],
            'Humidity': [humidity]
        }
    df_for_health = pd.DataFrame(features_for_health)
    health_predictor = joblib.load("health_predictor_model.pkl") 

    predicted_score = health_predictor.predict(df_for_health)[0]
        
    final_score = predicted_score
    return final_score