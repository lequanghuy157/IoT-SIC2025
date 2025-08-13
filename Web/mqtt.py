import paho.mqtt.client as mqtt
import mysql.connector
import json
from datetime import datetime


MQTT_BROKER = "192.168.0.104"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/sensor"

DB_CONFIG = {
    "host": "100.127.125.125",    
    "user": "nhom3",          
    "password": "nhom3iot@",  
    "database": "iot_data"
}


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print("📩 Nhận dữ liệu MQTT:", payload)

        data = json.loads(payload)

        # Xỷ lý dữ liệu thô
        tempC = float(data["temperature_C"].replace(" °C", ""))
        tempF = float(data["temperature_F"].replace(" °F", ""))
        humidity = float(data["humidity"].replace(" %", ""))
        dust = float(data["dust"].replace(" µg/m³", ""))

        # Lấy thời gian
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ghi vào Database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
            INSERT INTO sensor_data (temperature_C, temperature_F, humidity, dust, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (tempC, tempF, humidity, dust, timestamp)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print("Đã lưu dữ liệu vào MySQL.")

    except Exception as e:
        print("Lỗi xử lý dữ liệu:", e)

# Khi kết nối thành công
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Kết nối MQTT thành công.")
        client.subscribe(MQTT_TOPIC)
    else:
        print("Lỗi kết nối MQTT. Mã:", rc)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Đang kết nối đến MQTT broker...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
