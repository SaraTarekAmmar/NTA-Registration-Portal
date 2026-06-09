import os
import sys
from dotenv import load_dotenv
from mysql.connector import pooling

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

def clean_table_duplicates(cursor, table_name, group_by_cols):
    cols_str = ", ".join(group_by_cols)
    # Find groups with duplicates
    query = f"""
        SELECT {cols_str}, MIN(id) as keep_id, COUNT(*) as cnt 
        FROM {table_name} 
        GROUP BY {cols_str} 
        HAVING cnt > 1
    """
    cursor.execute(query)
    dup_groups = cursor.fetchall()
    
    deleted_total = 0
    for group in dup_groups:
        # Build where clause for group
        where_parts = []
        params = []
        for col in group_by_cols:
            val = group[col]
            if val is None:
                where_parts.append(f"{col} IS NULL")
            else:
                where_parts.append(f"{col} = %s")
                params.append(val)
        
        keep_id = group['keep_id']
        where_clause = " AND ".join(where_parts)
        
        # Delete duplicate rows that do not have the keep_id
        delete_query = f"DELETE FROM {table_name} WHERE {where_clause} AND id > %s"
        delete_params = params + [keep_id]
        
        cursor.execute(delete_query, delete_params)
        deleted_total += cursor.rowcount
        print(f"Table {table_name}: Cleaned duplicates for {dict((col, group[col]) for col in group_by_cols)}. Kept ID {keep_id}, deleted {cursor.rowcount} duplicate(s).")
    
    return deleted_total

def main():
    pool = pooling.MySQLConnectionPool(pool_name="cleanpool", pool_size=1, **db_config)
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Countries (grouped by name_ar)
        clean_table_duplicates(cursor, "countries_master", ["name_ar"])
        
        # 2. Degree Levels (grouped by name_ar, type)
        clean_table_duplicates(cursor, "degree_levels_master", ["name_ar", "type"])
        
        # 3. Grades (grouped by name_ar)
        clean_table_duplicates(cursor, "grades_master", ["name_ar"])
        
        # 4. Job Titles (grouped by name_ar)
        clean_table_duplicates(cursor, "job_titles_master", ["name_ar"])
        
        # 5. Languages (grouped by name_ar)
        clean_table_duplicates(cursor, "languages_master", ["name_ar"])
        
        conn.commit()
        print("\nAll database duplicate lookups successfully cleaned and committed!")
    except Exception as e:
        conn.rollback()
        print(f"Error during duplicate cleanup: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
