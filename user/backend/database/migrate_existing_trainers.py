import mysql.connector
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Resolve environment
env_path = r"d:\Work\NTA\NTA-Regestration-Portal - Final\admin\backend\.env"
load_dotenv(dotenv_path=env_path)

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

def run_migration():
    print("--- 1. Creating Trainer Isolated Tables ---")
    sql_file_path = r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\backend\database\create_trainer_tables.sql"
    
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql_script = f.read()

    # Connect and run DDL statements
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        # Split sql script by semicolons (simple parser)
        statements = sql_script.split(";")
        for stmt in statements:
            cleaned = stmt.strip()
            if cleaned:
                cursor.execute(cleaned)
        conn.commit()
        print("Trainer isolated tables created/verified successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error executing DDL: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    print("\n--- 2. Migrating Existing Trainer Data ---")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    try:
        # Get all trainers
        cursor.execute("SELECT id, full_name_ar, email FROM users WHERE role = 'trainer'")
        trainers = cursor.fetchall()
        print(f"Found {len(trainers)} users with role='trainer'.")

        # Map of trainee child table -> trainer child table (and column mapper for user/trainee foreign key)
        migration_map = {
            "trainee_profiles": ("trainer_profiles", "user_id"),
            "trainee_education": ("trainer_education", "trainee_id"),
            "trainee_experience": ("trainer_experience", "trainee_id"),
            "trainee_skills": ("trainer_skills", "trainee_id"),
            "trainee_languages": ("trainer_languages", "trainee_id"),
            "trainee_awards": ("trainer_awards", "trainee_id"),
            "trainer_community": ("trainer_community", "trainee_id"), # note: trainee_community doesn't prefix source but we map it
            "trainee_references": ("trainer_references", "trainee_id"),
            "trainee_social_media": ("trainer_social_media", "trainee_id"),
            "trainee_standardized_tests": ("trainer_standardized_tests", "trainee_id")
        }
        
        # Override source table for community extracurriculars if needed
        source_tables = {
            "trainee_profiles": "trainee_profiles",
            "trainee_education": "trainee_education",
            "trainee_experience": "trainee_experience",
            "trainee_skills": "trainee_skills",
            "trainee_languages": "trainee_languages",
            "trainee_awards": "trainee_awards",
            "trainer_community": "trainee_community", # Source is trainee_community
            "trainee_references": "trainee_references",
            "trainee_social_media": "trainee_social_media",
            "trainee_standardized_tests": "trainee_standardized_tests"
        }

        for trainer in trainers:
            t_id = trainer["id"]
            name = trainer["full_name_ar"]
            print(f"\nProcessing Trainer ID={t_id} ({name}):")

            for key, (dest_table, fk_col) in migration_map.items():
                src_table = source_tables[key]
                # Check for source rows
                cursor.execute(f"SELECT * FROM {src_table} WHERE {fk_col} = %s", (t_id,))
                rows = cursor.fetchall()
                if not rows:
                    continue

                print(f"  Found {len(rows)} row(s) in '{src_table}'. Migrating to '{dest_table}'...")

                for row in rows:
                    # Filter out 'id' primary key so it auto-increments in target
                    row_data = {k: v for k, v in row.items() if k != 'id'}
                    
                    # Convert trainee_id column name to trainer_id in child tables if necessary
                    if fk_col == "trainee_id":
                        row_data["trainer_id"] = row_data.pop("trainee_id")

                    # Construct INSERT statement
                    columns = ", ".join(f"`{c}`" for c in row_data.keys())
                    placeholders = ", ".join(["%s"] * len(row_data))
                    insert_sql = f"INSERT INTO `{dest_table}` ({columns}) VALUES ({placeholders})"
                    
                    cursor.execute(insert_sql, tuple(row_data.values()))

                # Delete from source table to complete the move/isolation
                cursor.execute(f"DELETE FROM {src_table} WHERE {fk_col} = %s", (t_id,))
                print(f"  Successfully moved and cleaned up '{src_table}'.")

        conn.commit()
        print("\nTrainer data migration completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error during data migration: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
