# test_db.py
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

try:
    print("Tentando conectar...")
    print(f"Host: {os.getenv('DBHOST')}")
    print(f"User: {os.getenv('DBUSER')}")
    print(f"Database: {os.getenv('DBNAME')}")

    conn = pymysql.connect(
        host=os.getenv('DBHOST'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWORD'),
        database=os.getenv('DBNAME'),
        charset='utf8mb4'
    )
    print("✅ Conexão bem sucedida!")

    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"MariaDB Version: {version[0]}")

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"Tabelas encontradas: {len(tables)}")

    conn.close()

except Exception as e:
    print(f"❌ Erro: {e}")
