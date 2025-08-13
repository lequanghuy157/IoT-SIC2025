

import mysql.connector
from mysql.connector import Error
import time
from datetime import datetime
import geocoder # Thư viện để lấy vị trí dựa trên IP

#kết nối database
DB_CONFIG = {
    "host": "localhost",
    "port": "3307",
    "user": "root",
    "password": "",
    "database": "iot_data"
}

# Thông tin định danh của con Pi này
PI_SENSOR_ID = 6 
SENSOR_NAME = "Cảm biến Pi (Văn phòng)"

# Tọa độ mặc định để sử dụng nếu không thể tự động lấy được
DEFAULT_LATITUDE = 21.027764
DEFAULT_LONGITUDE = 105.834160

# Thời gian (giây) chờ giữa mỗi lần kiểm tra và đồng bộ
SYNC_INTERVAL = 10 



def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Lỗi kết nối CSDL: {e}")
        return None

# lấy tọa độ bằng IP (chính xác thấp)
def get_real_location():
    """
    Cố gắng lấy kinh độ, vĩ độ thật dựa trên địa chỉ IP công cộng.
    Nếu thất bại, sử dụng tọa độ mặc định đã cấu hình.
    """
    print("-> Đang thử lấy tọa độ thực tế từ địa chỉ IP...")
    g = geocoder.ip('me')
    if g.ok and g.latlng:
        latitude, longitude = g.latlng
        print(f"-> Lấy tọa độ thành công: Lat={latitude}, Lon={longitude}")
        return latitude, longitude
    else:
        print(f"-> Không thể lấy tọa độ tự động. Sử dụng giá trị mặc định: Lat={DEFAULT_LATITUDE}, Lon={DEFAULT_LONGITUDE}")
        return DEFAULT_LATITUDE, DEFAULT_LONGITUDE

def register_or_update_sensor(connection, latitude, longitude):
    """
    Sử dụng tọa độ đã lấy được để đăng ký hoặc cập nhật thông tin
    của Pi trong bảng 'sensors'.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO sensors (id, name, latitude, longitude) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name), 
                latitude = VALUES(latitude), 
                longitude = VALUES(longitude)
        """
        values = (PI_SENSOR_ID, SENSOR_NAME, latitude, longitude)
        cursor.execute(sql, values)
        connection.commit()
        print(f"-> Đã đảm bảo thông tin cho Cảm biến #{PI_SENSOR_ID} là mới nhất trong bảng 'sensors'.")
    except Error as e:
        print(f"Lỗi khi đăng ký/cập nhật cảm biến: {e}")
    finally:
        if cursor:
            cursor.close()

def sync_latest_data():
    """Đọc bản ghi mới nhất từ 'sensor_data' và ghi vào 'sensor_datas'."""
    connection = get_db_connection()
    if not connection: return

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)


        sql_read = """
            SELECT 
                temperature_C AS temperature, humidity, dust, timestamp 
            FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        """

        cursor.execute(sql_read) 


        latest_real_data = cursor.fetchone()

        if not latest_real_data:
            print(f"-> Không tìm thấy dữ liệu trong 'sensor_data' để đồng bộ.")
            return

        sql_write = """
            INSERT INTO sensor_datas (sensor_id, temperature, humidity, dust, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """


        values = (
            PI_SENSOR_ID,
            latest_real_data['temperature'],
            latest_real_data['humidity'],
            latest_real_data['dust'],
            latest_real_data['timestamp']
        )
        cursor.execute(sql_write, values)
        connection.commit()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Đã đồng bộ thành công dữ liệu từ timestamp: {latest_real_data['timestamp']}")

    except Error as e:
        print(f"Lỗi trong quá trình đồng bộ: {e}")
    finally:
        if cursor: cursor.close()
        if connection.is_connected(): connection.close()

def main():
    """Vòng lặp chính của Dịch vụ Đồng bộ hóa."""
    print("--- Bắt đầu Dịch vụ Đồng bộ Dữ liệu Pi ---")
    
    # Lấy tọa độ thực tế từ IP
    latitude, longitude = get_real_location()
    
    # 2. Sử dụng tọa độ đó để đăng ký thông tin cảm biến
    connection = get_db_connection()
    if connection:
        register_or_update_sensor(connection, latitude, longitude)
        connection.close()
    else:
        print("CẢNH BÁO: Không thể kết nối CSDL để đăng ký. Dịch vụ có thể không hoạt động đúng.")

    print(f"Sẽ kiểm tra và đồng bộ dữ liệu mỗi {SYNC_INTERVAL} giây. Nhấn Ctrl+C để dừng.")
    
    while True:
        try:
            sync_latest_data()
            time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            print("\n--- Dừng Dịch vụ Đồng bộ. ---")
            break
        except Exception as e:
            print(f"Lỗi không mong muốn: {e}")
            time.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    main()