import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "user" / "backend"))

from core.database import get_db_connection
from core.auth import get_password_hash

def fix_user_password(national_id, raw_password):
    new_hash = get_password_hash(raw_password)
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, national_id, password_hash, role FROM users WHERE national_id = %s", (national_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"User {national_id} NOT FOUND!")
            return

        print(f"Found User ID: {user['id']}, Role: {user['role']}")
        print(f"Old Hash: {user['password_hash']}")
        print(f"New Hash: {new_hash}")
        
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user['id']))
        db.commit()
        print("Password updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    # Fix Admin
    print("Fixing Admin...")
    fix_user_password("29001011234567", "NTA@Admin2026")
    
    # Fix Editor
    print("\nFixing Editor...")
    fix_user_password("29505051234567", "NTA@Editor2026")

    # Fix Coordinator
    print("\nFixing Coordinator...")
    fix_user_password("29304041234567", "NTA@Coord2026")

    # Fix Admission Manager
    print("\nFixing Admission Manager...")
    fix_user_password("29703031234567", "NTA@Admission2026")

    # Fix Super Admin
    print("\nFixing Super Admin...")
    fix_user_password("10000000000000", "NTA@Super2026")
    
    # Fix Trainee
    print("\nFixing Trainee...")
    fix_user_password("29808081234567", "NTA@Trainee2026")

    # Fix Committee Members
    print("\nFixing Committee Members...")
    fix_user_password("29402021234567", "NTA@Member2026")
    fix_user_password("29403031234567", "NTA@Member2026")
