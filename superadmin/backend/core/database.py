import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

# Load environment variables from .env in the same directory or parent
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

connection_pool = None

try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="superadmin_pool",
        pool_size=5,
        pool_reset_session=True,
        **DB_CONFIG
    )
    print("[SUCCESS] SuperAdmin MySQL Connection Pool created successfully")
except mysql.connector.Error as err:
    print(f"[ERROR] Connection pool creation failed: {err}")

def get_db_connection():
    if connection_pool is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500, 
            detail="Database connection pool not initialized. Please check DB_HOST and DB_PASSWORD in .env"
        )
    try:
        return connection_pool.get_connection()
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to get database connection: {str(e)}")
