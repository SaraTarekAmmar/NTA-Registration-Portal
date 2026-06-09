import os
import mysql.connector
from dotenv import load_dotenv

# Path to the SQL files folder
SQL_DIR = r"C:\Users\Lenovo\Desktop\NTA-Regestration-Portal - Final\New folder"

# Load dotenv if present
load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "OmarNour@Work161996",
}
DB_NAME = "nta_portal"

def split_sql_statements(sql_text):
    """
    Splits SQL script text into individual statements, ignoring semicolons inside
    comments, quotes, and backticks.
    """
    statements = []
    current_stmt = []
    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    in_line_comment = False
    in_block_comment = False
    
    chars = list(sql_text)
    length = len(chars)
    i = 0
    while i < length:
        c = chars[i]
        
        # Handle escape characters inside strings
        if c == '\\' and (in_single_quote or in_double_quote):
            current_stmt.append(c)
            if i + 1 < length:
                current_stmt.append(chars[i+1])
                i += 2
                continue
        
        # Check block comment start/end
        if not in_single_quote and not in_double_quote and not in_backtick and not in_line_comment:
            if c == '/' and i + 1 < length and chars[i+1] == '*':
                in_block_comment = True
                current_stmt.append(c)
                current_stmt.append(chars[i+1])
                i += 2
                continue
            elif c == '*' and i + 1 < length and chars[i+1] == '/':
                in_block_comment = False
                current_stmt.append(c)
                current_stmt.append(chars[i+1])
                i += 2
                continue
                
        # Check line comment start
        if not in_single_quote and not in_double_quote and not in_backtick and not in_block_comment:
            if (c == '-' and i + 1 < length and chars[i+1] == '-') or c == '#':
                in_line_comment = True
                
        # Check line comment end
        if in_line_comment and c == '\n':
            in_line_comment = False
            
        # Toggle quotes/backticks
        if not in_line_comment and not in_block_comment:
            if c == "'" and not in_double_quote and not in_backtick:
                in_single_quote = not in_single_quote
            elif c == '"' and not in_single_quote and not in_backtick:
                in_double_quote = not in_double_quote
            elif c == '`' and not in_single_quote and not in_double_quote:
                in_backtick = not in_backtick
                
        current_stmt.append(c)
        
        # Check statement end (semicolon outside of comments and quotes)
        if c == ';' and not in_single_quote and not in_double_quote and not in_backtick and not in_line_comment and not in_block_comment:
            stmt_str = "".join(current_stmt).strip()
            if stmt_str:
                statements.append(stmt_str)
            current_stmt = []
            
        i += 1
        
    # Append any remaining content as a statement
    if current_stmt:
        stmt_str = "".join(current_stmt).strip()
        if stmt_str:
            statements.append(stmt_str)
            
    return statements

def import_sql_files():
    # Connect without database first to ensure it exists
    print("Connecting to MySQL server...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Could not connect to MySQL server: {e}")
        return
        
    cursor = conn.cursor()
    
    print(f"Creating database if not exists: {DB_NAME}")
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE `{DB_NAME}`;")
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        cursor.close()
        conn.close()
        return
    
    # Disable foreign key checks
    print("Disabling foreign key checks...")
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("SET UNIQUE_CHECKS = 0;")
        cursor.execute("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';")
        conn.commit()
    except Exception as e:
        print(f"Warning: could not set modes/foreign key checks: {e}")
    
    # Get all .sql files
    if not os.path.exists(SQL_DIR):
        print(f"Error: SQL directory '{SQL_DIR}' does not exist.")
        cursor.close()
        conn.close()
        return

    sql_files = [f for f in os.listdir(SQL_DIR) if f.endswith('.sql')]
    # Sort files to have a clean order
    sql_files.sort()
    
    total = len(sql_files)
    print(f"Found {total} SQL files to import.")
    
    success_count = 0
    failed_files = []
    
    for idx, filename in enumerate(sql_files, 1):
        filepath = os.path.join(SQL_DIR, filename)
        print(f"[{idx}/{total}] Importing {filename} ... ", end="", flush=True)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                sql_content = f.read()
            
            # Split SQL file into statements
            statements = split_sql_statements(sql_content)
            
            # Execute statements one by one
            for statement in statements:
                # Skip comments or empty statements
                clean_stmt = statement.strip()
                if not clean_stmt or clean_stmt.startswith(('--', '#', '/*')):
                    continue
                cursor.execute(clean_stmt)
                
            conn.commit()
            print("SUCCESS")
            success_count += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed_files.append((filename, str(e)))
            conn.rollback()
            
    # Re-enable foreign key checks
    print("Re-enabling foreign key checks...")
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cursor.execute("SET UNIQUE_CHECKS = 1;")
        conn.commit()
    except Exception as e:
        print(f"Warning: could not re-enable foreign key checks: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n--- Import Summary ---")
    print(f"Total files found: {total}")
    print(f"Successfully imported: {success_count}")
    print(f"Failed to import: {len(failed_files)}")
    if failed_files:
        print("\nFailed Files Details:")
        for name, err in failed_files:
            print(f" - {name}: {err}")

if __name__ == "__main__":
    import_sql_files()
