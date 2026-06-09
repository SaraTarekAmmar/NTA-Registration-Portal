import mysql.connector
import os

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "OmarNour@Work161996",
    "database": "nta_portal"
}

def apply_sql_file(filename):
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Read the SQL file
        with open(filename, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        # Split script into individual commands
        # Note: This is a simple split by ';'. For complex scripts with triggers/procs, 
        # a more robust parser would be needed.
        commands = sql_script.split(';')
        
        for command in commands:
            cmd = command.strip()
            if cmd:
                try:
                    cursor.execute(cmd)
                except Exception as e:
                    print(f"Error executing command: {cmd[:50]}...")
                    print(f"Error: {e}")
                    
        conn.commit()
        print(f"Successfully applied {filename}")
        
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    sql_path = os.path.join(os.path.dirname(__file__), "lookups_update_p3.sql")
    apply_sql_file(sql_path)
