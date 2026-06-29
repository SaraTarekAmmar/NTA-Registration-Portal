import mysql.connector
import os

def run_migration():
    db_pass = "sara@16112000"
    db_name = "nta_portal"
    db_user = "root"
    db_host = "localhost"

    migration_file = os.path.join(os.path.dirname(__file__), "migrations", "20260630_interview_evaluation_flow.sql")
    
    print(f"Reading migration file: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Strip line comments and reconstruct statements
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('--'):
            clean_lines.append(line)
            
    content = "".join(clean_lines)
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]

    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        database=db_name
    )
    cursor = conn.cursor()

    for stmt in statements:
        print(f"Executing: {stmt[:100]}...")
        try:
            cursor.execute(stmt)
            print("  [SUCCESS]")
        except mysql.connector.Error as err:
            # If the column/constraint already exists, we print a warning and continue
            print(f"  [WARNING/ERROR] {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration execution complete.")

if __name__ == "__main__":
    run_migration()
