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

#Kết nối Database
DB_CONFIG = {
    "host": "localhost",
    "port": '3307',
    "user": "root",
    "password": "",
    "database": "iot_data"
}

def get_db_connection():

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Lỗi kết nối đến MySQL: {e}")
        return None



def get_latest_data(sensor_id):
    """Lấy dữ liệu mới nhất cho một cảm biến cụ thể từ bảng sensor_data."""
    connection = get_db_connection()
    if not connection: return None
    try:
        cursor = connection.cursor(dictionary=True)

        sql = """
            SELECT temperature, humidity, dust, timestamp 
            FROM sensor_datas
            WHERE sensor_id = %s
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        cursor.execute(sql, (sensor_id,))
        result = cursor.fetchone()
        
        if result:
            temp_c = float(result['temperature'])
            return {
                "temperature_C": temp_c,
                "temperature_F": temp_c * 9 / 5 + 32,
                "humidity": float(result['humidity']),
                "dust": float(result['dust']), # THAY ĐỔI: Sử dụng 'dust'
                "timestamp": result['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            }
        return None
    finally:
        if connection and connection.is_connected(): connection.close()

def get_historical_data(sensor_id, hours=24):
    """Lấy dữ liệu lịch sử cho một cảm biến cụ thể."""

    connection = get_db_connection()
    if not connection: return []
    try:
        cursor = connection.cursor(dictionary=True)
        time_filter = datetime.now() - timedelta(hours=hours)
        sql = """
            SELECT temperature, humidity, dust, timestamp 
            FROM sensor_datas
            WHERE sensor_id = %s AND timestamp >= %s 
            ORDER BY timestamp ASC
        """
        cursor.execute(sql, (sensor_id, time_filter))
        results = cursor.fetchall()

        return results
    finally:
        if connection and connection.is_connected(): connection.close()


def calculate_aqi(dust_value):
    """Tính chỉ số AQI dựa trên giá trị dust."""

    if dust_value <= 12: return {"aqi": round(dust_value * 50 / 12), "level": "Tốt", "color": "#27ae60"}
    elif dust_value <= 35.4: return {"aqi": round(51 + ((dust_value - 12.1) * 49 / 23.3)), "level": "Trung bình", "color": "#f1c40f"}
    elif dust_value <= 55.4: return {"aqi": round(101 + ((dust_value - 35.5) * 49 / 19.9)), "level": "Có hại cho nhóm nhạy cảm", "color": "#e67e22"}
    elif dust_value <= 150.4: return {"aqi": round(151 + ((dust_value - 55.5) * 49 / 94.9)), "level": "Có hại cho sức khỏe", "color": "#e74c3c"}
    elif dust_value <= 250.4: return {"aqi": round(201 + ((dust_value - 150.5) * 99 / 99.9)), "level": "Rất có hại", "color": "#9b59b6"}
    else: return {"aqi": round(301 + ((dust_value - 250.5) * 199 / 249.5)), "level": "Nguy hiểm", "color": "#8e44ad"}


@app.route("/api/latest-all")
def api_latest_all():
    """
    API MỚI: Trả về dữ liệu mới nhất của TẤT CẢ các cảm biến.
    """
    connection = get_db_connection()
    if not connection: return jsonify([]), 500
    try:
        cursor = connection.cursor(dictionary=True)
        # Sử dụng subquery để lấy timestamp mới nhất cho mỗi sensor_id
        sql = """
            SELECT s.id, s.name, s.latitude, s.longitude, sd.temperature, sd.humidity, sd.dust, sd.timestamp
            FROM sensors s
            JOIN sensor_data sd ON s.id = sd.sensor_id
            INNER JOIN (
                SELECT sensor_id, MAX(timestamp) AS max_timestamp
                FROM sensor_data
                GROUP BY sensor_id
            ) AS latest ON sd.sensor_id = latest.sensor_id AND sd.timestamp = latest.max_timestamp
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        

        for sensor_data in results:
            sensor_data['aqi'] = calculate_aqi(sensor_data['dust'])

            temp_c = float(sensor_data['temperature'])
            sensor_data['temperature_C'] = temp_c
            sensor_data['temperature_F'] = temp_c * 9/5 + 32

            if sensor_data['timestamp']:
                sensor_data['timestamp'] = sensor_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify(results)
    except Error as e:
        print(f"Lỗi truy vấn dữ liệu tổng hợp: {e}")
        return jsonify([]), 500
    finally:
        if connection and connection.is_connected(): connection.close()

@app.route("/")
def map_page():
    return render_template("map.html")

@app.route("/dashboard")
def dashboard_page():

    return render_template("dashboard.html")

@app.route("/api/sensors")
def api_get_all_sensors():
    """API lấy danh sách và vị trí TẤT CẢ các cảm biến từ bảng 'sensors'."""
    connection = get_db_connection()
    if not connection: return jsonify([]), 500
    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id, name, latitude, longitude FROM sensors")
        sensors = cursor.fetchall()
        return jsonify(sensors)
    except Error as e:
        print(f"Lỗi truy vấn danh sách cảm biến: {e}")
        return jsonify([]), 500
    finally:
        if connection and connection.is_connected(): connection.close()

@app.route("/api/latest")
def api_latest():

    sensor_id = request.args.get('id', type=int)
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
    sensor_id = request.args.get('id', type=int)
    if not sensor_id: return jsonify({"error": "Thiếu 'id'"}), 400
    hours = int(request.args.get('hours', 24))
    data = get_historical_data(sensor_id, hours)
    return jsonify(data)

@app.route("/api/forecast")
def api_forecast():

    sensor_id = request.args.get('id', type=int)
    
    health_score = None 


    if sensor_id:

        sensor_data = get_latest_data(sensor_id)

        if sensor_data:

            aqi_info = calculate_aqi(sensor_data['dust'])
            aqi_value = aqi_info['aqi']
            

            temperature_value = sensor_data['temperature_C']
            humidity_value = sensor_data['humidity']

            print(f"[API Forecast] Chuẩn bị gọi AI cho Sensor ID #{sensor_id} với các tham số: AQI={aqi_value}, Temp={temperature_value}, Humid={humidity_value}")
            

            health_score = get_ai_health_score(aqi_value, temperature_value, humidity_value)
        else:
            print(f"[API Forecast] CẢNH BÁO: Không tìm thấy dữ liệu cho Sensor ID #{sensor_id}. Không thể dự đoán AI.")
    else:
        print("[API Forecast] CẢNH BÁO: Không có sensor_id được cung cấp. Bỏ qua dự đoán AI.")


    weather_data = get_weather_data()
    if not weather_data:

        if health_score is not None:
             return jsonify({ "health_score": round(health_score, 2) })
        return jsonify({"error": "Không thể lấy dữ liệu dự báo từ dịch vụ bên ngoài"}), 503


    final_response = {
        "health_score": round(health_score, 2) if health_score is not None else None,
        "weather_forecast": weather_data 
    }

    return jsonify(final_response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)