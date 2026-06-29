import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306))
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            # Read schema file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(script_dir, 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as file:
                sql_script = file.read()

            # Execute multi-statement script
            # Note: We split by ; to execute one by one for better error tracking
            commands = sql_script.split(';')
            for command in commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                    except Error as e:
                        print(f"Error executing command: {e}")
            
            connection.commit()
            print("Database 'nta_portal' initialized and seeded successfully.")

    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    init_db()
