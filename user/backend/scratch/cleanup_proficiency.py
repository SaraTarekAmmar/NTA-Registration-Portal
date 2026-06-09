import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(r'c:\Users\Lenovo\Desktop\NTA-Regestration-Portal - Final\user\backend\.env')

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'nta_portal')
)
cursor = conn.cursor(dictionary=True)

# 1. Update references in trainee_languages if any exist with string representation of ID > 5
cursor.execute("SELECT id, proficiency FROM trainee_languages")
rows = cursor.fetchall()
for r in rows:
    prof = r['proficiency']
    if prof and prof.isdigit():
        val = int(prof)
        if val > 5:
            new_val = str((val - 1) % 5 + 1)
            cursor.execute("UPDATE trainee_languages SET proficiency = %s WHERE id = %s", (new_val, r['id']))
            print(f"Updated trainee_languages ID {r['id']} proficiency from {prof} to {new_val}")

# 2. Update references in trainer_languages if any exist with string representation of ID > 5
try:
    cursor.execute("SELECT id, proficiency FROM trainer_languages")
    rows = cursor.fetchall()
    for r in rows:
        prof = r['proficiency']
        if prof and prof.isdigit():
            val = int(prof)
            if val > 5:
                new_val = str((val - 1) % 5 + 1)
                cursor.execute("UPDATE trainer_languages SET proficiency = %s WHERE id = %s", (new_val, r['id']))
                print(f"Updated trainer_languages ID {r['id']} proficiency from {prof} to {new_val}")
except mysql.connector.Error as err:
    print(f"Skipping trainer_languages update (maybe table doesn't exist yet): {err}")

# 3. Update english_proficiency in trainee_profiles if any exist with string representation of ID > 5
cursor.execute("SELECT id, english_proficiency FROM trainee_profiles")
rows = cursor.fetchall()
for r in rows:
    prof = r['english_proficiency']
    if prof and prof.isdigit():
        val = int(prof)
        if val > 5:
            new_val = str((val - 1) % 5 + 1)
            cursor.execute("UPDATE trainee_profiles SET english_proficiency = %s WHERE id = %s", (new_val, r['id']))
            print(f"Updated trainee_profiles ID {r['id']} english_proficiency from {prof} to {new_val}")

# 4. Delete duplicates from language_proficiency_master where ID > 5
cursor.execute("DELETE FROM language_proficiency_master WHERE id > 5")
deleted = cursor.rowcount
print(f"Deleted {deleted} duplicate rows from language_proficiency_master.")

conn.commit()
cursor.close()
conn.close()
print("Database cleanup completed successfully.")
