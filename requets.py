import requests
import csv
import time
from datetime import datetime


API_KEY = "4dcad4e696e5cb1356f6b4c8f38f9374"         
LAT = 20.774902             
LON = 105.771795                  
CSV_FILE = "air_quality_log.csv"
SLEEP_INTERVAL = 60 * 10       

def get_air_data():
    url = "https://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        aqi = data['list'][0]['main']['aqi']
        comp = data['list'][0]['components']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {                
            "timestamp": timestamp,
            "aqi": aqi,
            "pm2_5": comp.get("pm2_5", None),
            "pm10": comp.get("pm10", None),
            "co": comp.get("co", None),
            "no2": comp.get("no2", None),
            "o3": comp.get("o3", None)
        }
    except Exception as e:
        print("Failed", e)
        return None

def log_data():
    data = get_air_data()
    if data:
        file_exists = False
        try:
            with open(CSV_FILE, 'r'): file_exists = True
        except FileNotFoundError:
            pass

        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
            print("Done", data)

if __name__ == "__main__":
    while True:
        log_data()
        time.sleep(SLEEP_INTERVAL)
