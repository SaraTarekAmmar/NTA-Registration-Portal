from fastapi import APIRouter, HTTPException, Depends, Query
from core.database import get_db_connection
from core.security import get_superadmin_user
from typing import Optional, List
import mysql.connector
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/logs", tags=["Activity Logs"])

@router.get("/activity")
async def get_activity_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    current_user: dict = Depends(get_superadmin_user)
):
    """
    Fetch paginated activity logs from the database.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM activity_logs"
        params = []
        
        if category:
            query += " WHERE category = %s"
            params.append(category)
            
        query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        # Convert JSON strings to objects for structured response
        for log in logs:
            for field in ['details', 'payload_json']:
                if log.get(field) and isinstance(log[field], str):
                    try:
                        log[field] = json.loads(log[field])
                    except:
                        pass
            # Convert datetime to string for JSON serialization
            if log['timestamp']:
                log['timestamp'] = log['timestamp'].isoformat()
        
        cursor.close()
        conn.close()
        return {"logs": logs}
    except Exception as e:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_log_stats(current_user: dict = Depends(get_superadmin_user)):
    """
    Fetch aggregated log statistics for dashboard charts.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        stats = {}
        
        # 1. Logs by Category
        cursor.execute("SELECT category, COUNT(*) as count FROM activity_logs GROUP BY category")
        stats['by_category'] = cursor.fetchall()
        
        # 1.1 Logs by Level (NEW for Debugger)
        cursor.execute("SELECT level, COUNT(*) as count FROM activity_logs GROUP BY level")
        stats['by_level'] = cursor.fetchall()
        
        # 1.2 Logs by Component (NEW for Debugger)
        cursor.execute("SELECT component, COUNT(*) as count FROM activity_logs GROUP BY component")
        stats['by_component'] = cursor.fetchall()

        # 2. Logs Over Time (Last 7 Days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM activity_logs 
            WHERE timestamp >= %s 
            GROUP BY DATE(timestamp) 
            ORDER BY date ASC
        """, (seven_days_ago,))
        stats['over_time'] = cursor.fetchall()
        
        # 3. Status Code Distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN status_code >= 200 AND status_code < 300 THEN '2xx Success'
                    WHEN status_code >= 300 AND status_code < 400 THEN '3xx Redirection'
                    WHEN status_code >= 400 AND status_code < 500 THEN '4xx Client Error'
                    WHEN status_code >= 500 THEN '5xx Server Error'
                    ELSE 'Unknown'
                END as status_group,
                COUNT(*) as count
            FROM activity_logs
            GROUP BY status_group
        """)
        stats['status_codes'] = cursor.fetchall()
        
        # 4. Top Request Paths
        cursor.execute("""
            SELECT request_path, COUNT(*) as count 
            FROM activity_logs 
            WHERE request_path IS NOT NULL
            GROUP BY request_path 
            ORDER BY count DESC 
            LIMIT 5
        """)
        stats['top_paths'] = cursor.fetchall()

        # 5. Recent Activity Summary
        cursor.execute("SELECT COUNT(*) as total FROM activity_logs WHERE timestamp >= NOW() - INTERVAL 24 HOUR")
        stats['last_24h_count'] = cursor.fetchone()['total']

        cursor.close()
        conn.close()
        return stats
    except Exception as e:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications")
async def get_notifications(limit: int = 20, current_user: dict = Depends(get_superadmin_user)):
    """
    Fetch specific events for the notifications dashboard.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Events we care about for notifications
        event_types = [
            'COURSE_CREATED', 
            'TRAINEE_REGISTRATION', 
            'TRAINER_REGISTRATION',
            'ADMIN_FILE_UPLOAD', 
            'EXAM_COMPLETE', 
            'EXAM_GENERATED',
            'STAGE_7_APPROVAL',
            'APPLICATION_REJECTION',
            'OCR_MISMATCH',
            'BRUTE_FORCE_ALERT',
            'SERVICE_HEALTH_CHANGE',
            'COURSE_ARCHIVED',
            'MATERIAL_SYNC',
            'TRAINER_ASSIGNMENT',
            'SESSION_MATERIAL_UPDATE'
        ]
        
        placeholders = ', '.join(['%s'] * len(event_types))
        query = f"SELECT * FROM activity_logs WHERE event_type IN ({placeholders}) ORDER BY timestamp DESC LIMIT %s"
        
        cursor.execute(query, tuple(event_types + [limit]))
        logs = cursor.fetchall()
        
        # Convert details JSON string to object
        for log in logs:
            if log['details'] and isinstance(log['details'], str):
                try:
                    log['details'] = json.loads(log['details'])
                except:
                    pass
            if log['timestamp']:
                log['timestamp'] = log['timestamp'].isoformat()
        
        cursor.close()
        conn.close()
        return logs
    except Exception as e:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{trace_id}")
async def get_trace_details(trace_id: str, current_user: dict = Depends(get_superadmin_user)):
    """
    Fetch all related logs for a specific trace ID for cross-service debugging.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM activity_logs WHERE trace_id = %s ORDER BY timestamp ASC"
        cursor.execute(query, (trace_id,))
        logs = cursor.fetchall()
        
        for log in logs:
            for field in ['details', 'payload_json']:
                if log.get(field) and isinstance(log[field], str):
                    try: log[field] = json.loads(log[field])
                    except: pass
            if log['timestamp']:
                log['timestamp'] = log['timestamp'].isoformat()
        
        cursor.close()
        conn.close()
        return logs
    except Exception as e:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))
