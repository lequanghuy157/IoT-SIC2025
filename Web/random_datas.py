import mysql.connector
from mysql.connector import Error
import random
import time
from datetime import datetime
import sys


sys.stdout.reconfigure(encoding='utf-8')


DB_CONFIG = {
    "host": "localhost",
    "port": "3307",
    "user": "root",
    "password": "",
    "database": "iot_data"
}

# Danh sách ID
SENSOR_IDS = [1, 2, 3, 4, 5]

# Thời gian chờ ghi dữ liệu ảo
INSERT_INTERVAL = 600 



def get_db_connection():
    """Tạo kết nối đến CSDL MySQL."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Lỗi khi kết nối đến MySQL: {e}")
        return None

def generate_fake_data(sensor_id):
    """Tạo ra một bộ dữ liệu giả ngẫu nhiên nhưng hợp lý."""
    
    # Tạo dữ liệu ngẫu nhiên
    if sensor_id == 1: # Công viên Thống Nhất (mát hơn, sạch hơn)
        temperature = round(random.uniform(26.0, 32.0), 2)
        humidity = round(random.uniform(70.0, 90.0), 2)
        dust = round(random.uniform(5.0, 40.0), 2)
    elif sensor_id == 3: # KCN Bắc Thăng Long (nóng hơn, ô nhiễm hơn)
        temperature = round(random.uniform(28.0, 36.0), 2)
        humidity = round(random.uniform(60.0, 80.0), 2)
        dust = round(random.uniform(30.0, 120.0), 2)
    else: # Các khu vực dân cư và trung tâm khác
        temperature = round(random.uniform(27.0, 34.0), 2)
        humidity = round(random.uniform(65.0, 85.0), 2)
        dust = round(random.uniform(15.0, 80.0), 2)
        
    return {
        "temperature": temperature,
        "humidity": humidity,
        "dust": dust
    }

def insert_sensor_datas(connection, sensor_id, data):
    """Ghi một bộ dữ liệu vào bảng sensor_data."""
    cursor = None
    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO sensor_datas (sensor_id, temperature, humidity, dust) 
            VALUES (%s, %s, %s, %s)
        """
        values = (
            sensor_id, 
            data['temperature'], 
            data['humidity'],
            data['dust']
        )
        cursor.execute(sql, values)
        connection.commit()
        print(f"-> Đã ghi dữ liệu cho Cảm biến #{sensor_id}: "
              f"Nhiệt độ={data['temperature']}°C, Độ ẩm={data['humidity']}%, Bụi={data['dust']}")
    except Error as e:
        print(f"Lỗi khi ghi dữ liệu cho Cảm biến #{sensor_id}: {e}")
    finally:
        if cursor:
            cursor.close()

def main():
    """Vòng lặp chính để liên tục tạo và ghi dữ liệu."""
    print("--- Bắt đầu chương trình tạo dữ liệu giả (sử dụng DUST) ---")
    print(f"Sẽ ghi dữ liệu cho {len(SENSOR_IDS)} cảm biến mỗi {INSERT_INTERVAL} giây.")
    print("Nhấn Ctrl+C để dừng chương trình.")
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bắt đầu ghi dữ liệu...")
            
            connection = get_db_connection()
            
            if connection:
                # Chỉ ghi dữ liệu nếu kết nối thành công
                for sensor_id in SENSOR_IDS:
                    fake_data = generate_fake_data(sensor_id)
                    insert_sensor_datas(connection, sensor_id, fake_data)
                
                connection.close()
                print("Đã ghi dữ liệu thành công")
            else:
                print("Không thể kết nối đến CSDL")

        except KeyboardInterrupt:
            print("\nDừng")
            break
        except Exception as e:
            print(f"Lỗi khi gặp: {e}")
        
        try:
            print(f"{INSERT_INTERVAL}"+"giây ghi lần nữa")
            time.sleep(INSERT_INTERVAL)
        except KeyboardInterrupt:
    
            print("\nDừng")
            break

if __name__ == "__main__":
    main()