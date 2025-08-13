from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import sys


from forecast import get_weather_data
from AIForecast import get_ai_health_score 

sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
CORS(app) 

# Kết nối Database
DB_CONFIG = {
    "host": "localhost",
    "port": '3307',
    "user": "root",
    "password": "",
    "database": "iot_data"
}

def get_db_connection():
    """Tạo và trả về một kết nối CSDL mới."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Lỗi kết nối đến MySQL: {e}")
        return None

# Lấy Sensor ID làm tham số
def get_latest_data(sensor_id):
    """Lấy dữ liệu mới nhất cho một cảm biến cụ thể."""
    connection = get_db_connection()
    if not connection: return None
        
    try:
        cursor = connection.cursor(dictionary=True)
        sql = """
            SELECT temperature_C, humidity, dust, reading_time
            FROM sensors
            WHERE sensor_id = %s
            ORDER BY reading_time DESC 
            LIMIT 1
        """
        cursor.execute(sql, (sensor_id,))
        result = cursor.fetchone()
        
        if result:
            temp_c = float(result['temperature_C'])
            return {
                "temperature_C": temp_c,
                "temperature_F": temp_c * 9 / 5 + 32,
                "humidity": float(result['humidity']),
                "dust": float(result['dust']),
                "reading_time": result['reading_time'].strftime("%Y-%m-%d %H:%M:%S")
            }
        return None
    except Error as e:
        print(f"Lỗi truy vấn dữ liệu mới nhất cho sensor_id {sensor_id}: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Lấy sensor ID làm tham số
def get_historical_data(sensor_id, hours=24):
    """Lấy dữ liệu lịch sử trong N giờ qua cho một cảm biến cụ thể."""
    connection = get_db_connection()
    if not connection: return []

    try:
        cursor = connection.cursor(dictionary=True)
        time_filter = datetime.now() - timedelta(hours=hours)
        sql = """
            SELECT temperature_C, humidity, dust, reading_time 
            FROM sensors
            WHERE sensor_id = %s AND reading_time >= %s 
            ORDER BY reading_time ASC
        """
        cursor.execute(sql, (sensor_id, time_filter))
        
        results = cursor.fetchall()
        data = []
        for item in results:
            temp_c = float(item['temperature_C'])
            data.append({
                "temperature_C": temp_c,
                "temperature_F": temp_c * 9 / 5 + 32,
                "humidity": float(item['humidity']),
                "dust": float(item['dust']),
                "reading_time": item['reading_time'].strftime("%Y-%m-%d %H:%M:%S")
            })
        return data
    except Error as e:
        print(f"Lỗi truy vấn dữ liệu lịch sử cho sensor_id {sensor_id}: {e}")
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def calculate_aqi(pm25_value):
    """Tính chỉ số AQI (giữ nguyên)."""
    if pm25_value <= 12: return {"aqi": round(pm25_value * 50 / 12), "level": "Tốt", "color": "#27ae60"}
    elif pm25_value <= 35.4: return {"aqi": round(51 + ((pm25_value - 12.1) * 49 / 23.3)), "level": "Trung bình", "color": "#f1c40f"}
    elif pm25_value <= 55.4: return {"aqi": round(101 + ((pm25_value - 35.5) * 49 / 19.9)), "level": "Có hại cho nhóm nhạy cảm", "color": "#e67e22"}
    elif pm25_value <= 150.4: return {"aqi": round(151 + ((pm25_value - 55.5) * 49 / 94.9)), "level": "Có hại cho sức khỏe", "color": "#e74c3c"}
    elif pm25_value <= 250.4: return {"aqi": round(201 + ((pm25_value - 150.5) * 99 / 99.9)), "level": "Rất có hại", "color": "#9b59b6"}
    else: return {"aqi": round(301 + ((pm25_value - 250.5) * 199 / 249.5)), "level": "Nguy hiểm", "color": "#8e44ad"}


@app.route("/")
def map_page():
    return render_template("map.html")


@app.route("/index")
def dashboard_page():
    return render_template("index.html")


@app.route("/api/sensors")

@app.route("/api/sensors")
def api_get_all_sensors():
    """API lấy danh sách và vị trí TẤT CẢ các cảm biến từ bảng 'sensors'."""
    connection = get_db_connection()
    if not connection: return jsonify([]), 500
    try:
        cursor = connection.cursor(dictionary=True)
        
        sql = "SELECT id, name, latitude, longitude FROM sensors"

        cursor.execute(sql)
        sensors = cursor.fetchall()
        return jsonify(sensors)
    except Error as e:
        print(f"Lỗi truy vấn danh sách cảm biến: {e}")
        return jsonify([]), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/api/latest")
def api_latest():
    """API trả về dữ liệu mới nhất cho một cảm biến cụ thể."""
    sensor_id = request.args.get('id', default=1, type=int)
    if not sensor_id:
        return jsonify({"error": "Thiếu tham số 'id' của cảm biến"}), 400

    data = get_latest_data(sensor_id)
    if data:
        aqi_info = calculate_aqi(data['dust'])
        data['aqi'] = aqi_info
        return jsonify(data)
    else:
        return jsonify({"error": f"Không có dữ liệu cho cảm biến ID {sensor_id}"}), 404


@app.route("/api/historical")
def api_historical():
    """API trả về dữ liệu lịch sử cho một cảm biến cụ thể."""
    sensor_id = request.args.get('id', default=1, type=int)
    if not sensor_id:
        return jsonify({"error": "Thiếu tham số 'id' của cảm biến"}), 400
        
    hours = int(request.args.get('hours', 24))
    data = get_historical_data(sensor_id, hours)
    return jsonify(data)

@app.route("/api/forecast")
def api_forecast():
    """API dự báo thời tiết chung và điểm sức khỏe AI."""
    weather_data = get_weather_data()
    if not weather_data:
        return jsonify({"error": "Không thể lấy dữ liệu dự báo"}), 503
        
    health_score = get_ai_health_score(weather_data.get("current"))
    final_response = {
        "health_score": round(health_score, 2) if health_score is not None else None,
        "current": weather_data.get("current"),
        "forecast_days": weather_data.get("forecast_days")
    }
    return jsonify(final_response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)