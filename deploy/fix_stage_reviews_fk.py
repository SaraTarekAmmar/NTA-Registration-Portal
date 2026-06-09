import os
import mysql.connector
from dotenv import load_dotenv

def fix_stage_reviews_fk():
    """
    Converts stage_reviews.trainee_id FK from ON DELETE CASCADE to ON DELETE SET NULL.
    This preserves the audit trail when a rejected trainee's user row is deleted.
    Safe to run multiple times — drops and recreates the constraint idempotently.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, 'admin', 'backend', '.env')

    if not os.path.exists(env_path):
        print(f"[ERROR] .env file not found at {env_path}")
        return False

    load_dotenv(env_path)

    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "nta_portal")

    print(f"[*] Connecting to MySQL at {db_host} as {db_user}, database '{db_name}'...")

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        steps = [
            (
                "Drop existing FK (ON DELETE CASCADE)",
                "ALTER TABLE stage_reviews DROP FOREIGN KEY stage_reviews_ibfk_1"
            ),
            (
                "Allow NULL on trainee_id",
                "ALTER TABLE stage_reviews MODIFY trainee_id INT NULL"
            ),
            (
                "Re-add FK with ON DELETE SET NULL",
                "ALTER TABLE stage_reviews ADD CONSTRAINT stage_reviews_ibfk_1 "
                "FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE SET NULL"
            ),
        ]

        for description, sql in steps:
            print(f"[*] {description}...")
            try:
                cursor.execute(sql)
                conn.commit()
                print(f"    [OK]")
            except mysql.connector.Error as err:
                # If the FK doesn't exist yet (fresh schema already fixed), skip gracefully
                if err.errno == 1091:  # ER_CANT_DROP_FIELD_OR_KEY
                    print(f"    [SKIP] Constraint not found — already removed or never existed.")
                else:
                    raise

        cursor.close()
        conn.close()
        print("\n[SUCCESS] stage_reviews FK updated to ON DELETE SET NULL.")
        print("          Audit trail rows will now be preserved when trainees are deleted.")
        return True

    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL error: {err}")
        return False


if __name__ == "__main__":
    if not fix_stage_reviews_fk():
        exit(1)
