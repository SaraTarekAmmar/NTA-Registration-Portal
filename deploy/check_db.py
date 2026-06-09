"""
NTA Portal - Pre-Launch Database Connectivity Check
====================================================
Run this to verify your MySQL connection is working before starting the servers.
"""
import sys
import os

# Force stdout to flush immediately so output is never cut off
import functools
print = functools.partial(print, flush=True)


def check_connection(env_path, label="Database"):
    """Try to connect to MySQL using the given .env file. Returns True on success."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(f"  [ERROR] python-dotenv not installed. Run: pip install python-dotenv")
        return False

    try:
        import mysql.connector
    except ImportError:
        print(f"  [ERROR] mysql-connector-python not installed. Run: pip install mysql-connector-python")
        return False

    if not os.path.exists(env_path):
        print(f"  [ERROR] .env file not found at: {env_path}")
        print(f"  >>> Create the .env file with your DB credentials.")
        return False

    load_dotenv(env_path, override=True)

    host     = os.getenv("DB_HOST", "localhost")
    port_str = os.getenv("DB_PORT", "3306")
    user     = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db_name  = os.getenv("DB_NAME", "nta_portal")

    try:
        port = int(port_str)
    except ValueError:
        port = 3306

    print(f"  Connecting to MySQL at {host}:{port} as '{user}' (db: {db_name})...")

    # ---- Try connecting WITH the database ----
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            auth_plugin="mysql_native_password",
        )
        # Check for core tables
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        log_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"  [OK] {label}: Connection successful! (Found {log_count} activity logs)")
        return True

    except mysql.connector.Error as e:
        err_code = e.errno
        print(f"  [FAIL] {label}: MySQL Error {err_code}: {e.msg}")

        # Provide actionable guidance
        if err_code == 1045:
            print()
            print("  >>> FIX: Wrong username or password.")
            print(f"  >>> Current password in .env: {'(blank)' if not password else '(set)'}")
            print("  >>> Open 'deploy/credentials.txt' and set the correct DB_PASSWORD.")
            print("  >>> Then re-run deploy/RUN_SYSTEM.bat")
        elif err_code == 1049:
            print()
            print("  >>> FIX: Database 'nta_portal' does not exist yet.")
            print("  >>> Run deploy/RUN_SYSTEM.bat - it will create it automatically.")
        elif err_code in (2003, 2002):
            print()
            print("  >>> FIX: Cannot connect to MySQL server on localhost.")
            print("  >>> Run this in CMD as Admin:  net start MySQL80")
        elif err_code == 2005:
            print()
            print("  >>> FIX: MySQL host not found. Check DB_HOST in your .env file.")
        elif err_code == 1130:
            print()
            print("  >>> FIX: This host is not allowed to connect.")
            print("  >>> Run in MySQL:  GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';")
        else:
            print()
            print("  >>> Check your MySQL installation and .env credentials.")
        return False

    except Exception as e:
        # Catch ANYTHING else (SSL errors, auth plugin errors, etc.)
        print(f"  [FAIL] {label}: Unexpected error: {type(e).__name__}: {e}")

        if "auth" in str(e).lower() or "plugin" in str(e).lower() or "caching_sha2" in str(e).lower():
            print()
            print("  >>> FIX: MySQL 8.0 authentication plugin issue.")
            print("  >>> Open MySQL Workbench and run:")
            print("  >>>   ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password")
            print(f"  >>>     BY 'your_password';")
            print("  >>>   FLUSH PRIVILEGES;")
        return False


def check_connection_no_db(env_path, label="Database"):
    """Try connecting WITHOUT specifying a database (to verify server/credentials only)."""
    try:
        from dotenv import load_dotenv
        import mysql.connector
    except ImportError:
        return False

    if not os.path.exists(env_path):
        return False

    load_dotenv(env_path, override=True)
    host     = os.getenv("DB_HOST", "localhost")
    port     = int(os.getenv("DB_PORT", "3306"))
    user     = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")

    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password,
            auth_plugin="mysql_native_password",
        )
        conn.close()
        print(f"  [OK] Server reachable (credentials correct, but database may not exist yet)")
        return True
    except mysql.connector.Error as e:
        print(f"  [FAIL] Server check: MySQL Error {e.errno}: {e.msg}")
        if e.errno == 1045:
            print()
            print("  >>> FIX: Wrong password! Edit 'deploy/credentials.txt'")
            print("  >>> Set DB_PASSWORD= to your MySQL root password and re-run RUN_SYSTEM.bat")
        return False
    except Exception as e:
        print(f"  [FAIL] Server check: {type(e).__name__}: {e}")
        return False


def main():
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    admin_env = os.path.join(project_root, "admin", "backend", ".env")
    user_env  = os.path.join(project_root, "user",  "backend", ".env")

    print("=" * 55, flush=True)
    print("NTA PORTAL - DATABASE CONNECTION CHECK")
    print("=" * 55)
    print()

    # First try: connect WITH database
    ok_admin = check_connection(admin_env, "Admin Portal DB")

    # If it failed, try without the database to isolate server vs. DB issue
    if not ok_admin:
        print()
        print("  [Trying server-only connection to isolate the issue...]")
        check_connection_no_db(admin_env, "Admin Portal")

    print()
    ok_user = check_connection(user_env, "User Portal DB")

    if not ok_user:
        print()
        print("  [Trying server-only connection to isolate the issue...]")
        check_connection_no_db(user_env, "User Portal")

    print()
    print("=" * 55)
    if ok_admin and ok_user:
        print("[SUCCESS] Both portals can reach the database.")
        print("          You may now run RUN_SYSTEM.bat")
        sys.exit(0)
    else:
        print("[FAILED]  Fix the errors above, then try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
