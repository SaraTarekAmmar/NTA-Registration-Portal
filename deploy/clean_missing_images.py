import os
import sys
import logging
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

# Set up logging
log_file = os.path.join(os.path.dirname(__file__), "image_cleanup.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def main():
    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / "admin" / "backend" / ".env"
    load_dotenv(env_path)

    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "nta_portal")
        )
        cursor = db.cursor(dictionary=True)
        
        logging.info("Connected to database.")
        
        cursor.execute("SELECT id, email, profile_photo FROM users WHERE profile_photo IS NOT NULL")
        users = cursor.fetchall()
        
        updated_count = 0
        invalid_values = ["null", "undefined", ""]
        
        for user in users:
            photo = user["profile_photo"]
            if not photo:
                continue
                
            photo_str = str(photo).strip()
            
            is_invalid = False
            if photo_str.lower() in invalid_values:
                is_invalid = True
            else:
                # Check file existence
                clean_path = photo_str
                if clean_path.startswith("http"):
                    # Extract the path after the domain
                    parts = clean_path.split("/")
                    try:
                        idx = parts.index("data")
                        clean_path = "/".join(parts[idx:])
                    except ValueError:
                        is_invalid = True
                
                if clean_path.startswith("/"):
                    clean_path = clean_path[1:]
                    
                full_path = root_dir / clean_path
                
                if not is_invalid and not full_path.exists():
                    is_invalid = True
                    
            if is_invalid:
                logging.info(f"User ID {user['id']} ({user['email']}): Invalid/Missing photo '{photo_str}'. Setting to NULL.")
                cursor.execute("UPDATE users SET profile_photo = NULL WHERE id = %s", (user['id'],))
                updated_count += 1
                
        db.commit()
        logging.info(f"Cleanup complete. Updated {updated_count} records.")
        
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()

if __name__ == "__main__":
    main()
