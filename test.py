import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="iot_data"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM sensor_data LIMIT 5")
for row in cursor.fetchall():
    print(row)
