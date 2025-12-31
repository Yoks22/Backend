import pymysql

print("Trying direct MySQL connection...")

conn = pymysql.connect(
    host="127.0.0.1",
    user="vdi",
    password="Qwerty$123",
    port=3306,
    database="zoho_db"
)

print("CONNECTED SUCCESSFULLY")
conn.close()
