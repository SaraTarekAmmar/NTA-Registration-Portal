import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

# Load environment variables from the parent directory of this file (backend/.env)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal"),
    "charset": "utf8mb4",
    "connection_timeout": int(os.getenv("DB_CONNECTION_TIMEOUT", "10")),
}

connection_pool = None
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="nta_pool",
        pool_size=30,  # Increased for concurrent dashboard & background AI tasks
        pool_reset_session=True,
        **DB_CONFIG
    )
    print("MySQL Connection Pool created successfully")
except mysql.connector.Error as err:
    print(f"Error creating connection pool: {err}")

def get_db_connection():
    if connection_pool is None:
        raise RuntimeError("Database connection pool is not available")
    return connection_pool.get_connection()
