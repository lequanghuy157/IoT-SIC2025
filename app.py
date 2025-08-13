
from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import sys
sys.stdout.reconfigure(encoding='utf-8')


app = Flask(__name__)

CORS(app) 


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', 
    'database': 'iot_data'
}
@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    conn = None 
    cursor = None 
    try:
  
        conn = mysql.connector.connect(**db_config)
        
        cursor = conn.cursor(dictionary=True)
        

        query = "SELECT id, temperature, humidity, PM2_5, timestamp FROM sensor_data ORDER BY timestamp DESC"
        cursor.execute(query)
        

        data = cursor.fetchall()

        return jsonify(data)

    except Error as e:

        print(f"Lỗi khi kết nối tới MySQL: {e}")

        return jsonify({"error": "Không thể truy vấn cơ sở dữ liệu"}), 500
    
    finally:

        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("Kết nối MySQL đã được đóng")


if __name__ == '__main__':

    app.run(port=5000, debug=True)