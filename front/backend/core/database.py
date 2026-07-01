import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal"),
    "charset": "utf8mb4"
}

try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="front_pool",
        pool_size=10,
        pool_reset_session=True,
        **DB_CONFIG
    )
    print("Front Portal — MySQL Connection Pool created successfully")
except mysql.connector.Error as err:
    print(f"Front Portal — Error creating connection pool: {err}")

def get_db_connection():
    return connection_pool.get_connection()
