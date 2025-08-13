import requests
from datetime import datetime
import sys 
sys.stdout.reconfigure(encoding='utf-8')


API_KEY = "1d682ebed5af4db5aae82919250408" 
LOCATION = "Hanoi"

def get_weather_data(api_key=API_KEY, location=LOCATION):
    """
    Hàm này gọi API thời tiết, xử lý dữ liệu và trả về một dictionary Python
    thay vì in ra màn hình.
    """
    
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=3&aqi=yes&alerts=no"
    
    try:
        response = requests.get(url)

        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API, chắc là hết hạn API rồi: {e}")
        return None 


    current_api_data = data["current"]
    current_processed = {
        "temperature": current_api_data["temp_c"],
        "condition": current_api_data["condition"]["text"],
        "uv": current_api_data["uv"],
        "air_quality": {
            "aqi": current_api_data["air_quality"]["us-epa-index"],
            "pm2_5": current_api_data["air_quality"]["pm2_5"],
            "pm10": current_api_data["air_quality"]["pm10"],
            "co": current_api_data["air_quality"]["co"],
            "no2": current_api_data["air_quality"]["no2"],
            "o3": current_api_data["air_quality"]["o3"],
            "so2": current_api_data["air_quality"]["so2"]
        }
    }


    forecast_days_processed = []
    day_names = ["Hôm nay", "Ngày mai", "Ngày kia"] 

    for i, day_api_data in enumerate(data["forecast"]["forecastday"]):
        

        hourly_processed = []
        for hour_api_data in day_api_data["hour"]:
            hourly_processed.append({
                "time": hour_api_data["time"].split(" ")[1], # Lấy HH:MM
                "temp": hour_api_data["temp_c"],
                "rain_chance": hour_api_data["chance_of_rain"],
                "condition": hour_api_data["condition"]["text"]
            })
        
        # Tạo dictionary cho một ngày dự báo
        day_processed = {
            "date": day_api_data["date"],
            # Sử dụng i để lấy tên ngày từ list day_names
            "day_name": day_names[i] if i < len(day_names) else day_api_data["date"],
            "sunrise": day_api_data["astro"]["sunrise"],
            "sunset": day_api_data["astro"]["sunset"],
            "max_temp": day_api_data["day"]["maxtemp_c"],
            "min_temp": day_api_data["day"]["mintemp_c"],
            "condition": day_api_data["day"]["condition"]["text"],
            "chance_of_rain": day_api_data["day"]["daily_chance_of_rain"],
            "hourly": hourly_processed # Gán danh sách dữ liệu theo giờ vào đây
        }
        
        forecast_days_processed.append(day_processed)

    # Kết hợp tất cả lại thành một dictionary lớn duy nhất
    final_structured_data = {
        "current": current_processed,
        "forecast_days": forecast_days_processed
    }

    # Trả về dictionary này thay vì print()
    return final_structured_data

#test file
if __name__ == '__main__':

    import sys
    import json
    sys.stdout.reconfigure(encoding='utf-8')

    weather_data = get_weather_data()
    
    if weather_data:
        # json.dumps để in ra dictionary đẹp
        print(json.dumps(weather_data, indent=2, ensure_ascii=False))