import random
import time
from datetime import datetime
import mysql.connector
import sys
sys.stdout.reconfigure(encoding='utf-8')


# Kết nối tới MySQL
conn = mysql.connector.connect(
    host="localhost",
    port='3307',
    user="root",
    password="",
    database="iot_data"
)
cursor = conn.cursor()

try:
    while True:
        # Sinh dữ liệu ngẫu nhiên
        temp = round(random.uniform(25.0, 35.0), 1)        # Nhiệt độ °C
        humi = round(random.uniform(60.0, 90.0), 1)        # Độ ẩm %
        dust = round(random.uniform(5.0, 80.0), 1)         # PM2.5 µg/m³
        now = datetime.now()

        # Lệnh SQL
        query = """
            INSERT INTO sensor_data (temperature_C,temperature_F, humidity, dust, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (temp, temp*1.8+32, humi, dust, now)

        cursor.execute(query, values)
        conn.commit()

        print(f" {now} - Temp: {temp}°C | Humi: {humi}% | dust: {dust} µg/m³")

        # Chờ 60s
        time.sleep(60)

except KeyboardInterrupt:
    print(" Dừng ghi dữ liệu.")
    cursor.close()
    conn.close()