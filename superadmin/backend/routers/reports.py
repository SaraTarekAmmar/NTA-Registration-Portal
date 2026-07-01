from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from core.database import get_db_connection
from core.security import get_superadmin_user
from typing import List, Dict, Any
import io
import csv
import json
import re
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["System Reports"])

REPORT_TARGETS = {
    "trainees": {"table": "users", "filter": "role = 'trainee'", "label": "Trainees"},
    "trainers": {"table": "users", "filter": "role = 'trainer'", "label": "Trainers"},
    "admins": {"table": "users", "filter": "role = 'admin'", "label": "Admins"},
    "editors": {"table": "users", "filter": "role = 'editor'", "label": "Editors"},
    "courses": {"table": "courses", "filter": "1=1", "label": "Courses"},
    "sessions": {"table": "course_sessions", "filter": "1=1", "label": "Course Sessions"},
    "quizzes": {"table": "quizzes", "filter": "1=1", "label": "Quizzes"},
    "logs": {"table": "activity_logs", "filter": "1=1", "label": "Activity Logs"},
    "ip_tracking": {"table": "activity_logs", "fields": "ip_address, user_agent, timestamp, request_path, status_code", "label": "IP Tracking"},
    
    # --- NEW PRESETS ---
    "academic_360": {
        "label": "Academic 360° Audit",
        "query": """
            SELECT 
                u.full_name_ar as "Name", 
                u.national_id as "National ID", 
                u.role as "Role",
                (SELECT COUNT(*) FROM attendance_logs al WHERE al.national_id = u.national_id) as "Attendance Count",
                COALESCE(cv.match_score, 0) as "CV Match Score",
                (SELECT ROUND(AVG(score), 2) FROM quiz_attempts qa WHERE qa.user_id = u.id) as "Avg Quiz Score",
                COALESCE(ps.status, 'idle') as "Pipeline Status"
            FROM users u
            LEFT JOIN cv_matching_results cv ON u.national_id = cv.national_id
            LEFT JOIN pipeline_state ps ON u.id = ps.trainee_id
            WHERE u.role = 'trainee'
        """
    },
    "forensic_security": {
        "label": "Forensic Security Audit",
        "query": """
            SELECT 
                timestamp as "Time", 
                category as "Category", 
                event_type as "Event", 
                national_id as "Subject ID", 
                ip_address as "IP", 
                user_agent as "User Agent", 
                request_path as "Path", 
                status_code as "Status", 
                details as "Extra Details"
            FROM activity_logs
            WHERE category IN ('AUTH', 'SYSTEM', 'ADMIN')
            ORDER BY timestamp DESC
        """
    },
    "resource_engagement": {
        "label": "Resource Engagement Report",
        "query": """
            SELECT 
                c.title as "Course",
                (SELECT COUNT(*) FROM course_sessions cs WHERE cs.course_id = c.id) as "Sessions",
                (SELECT COUNT(*) FROM course_sessions cs WHERE cs.course_id = c.id AND cs.materials IS NOT NULL) as "Sessions with Materials",
                (SELECT ROUND(AVG(qa.score), 2) FROM quiz_attempts qa WHERE qa.course_id = c.id) as "Avg Course Quiz Score"
            FROM courses c
        """
    }
}

@router.get("/targets")
async def get_report_targets(current_user: dict = Depends(get_superadmin_user)):
    return [{"id": k, "label": v["label"]} for k, v in REPORT_TARGETS.items()]

from pydantic import BaseModel
from typing import Optional, List

class ReportPayload(BaseModel):
    targets: List[str] = []
    dateRange: Optional[Dict[str, str]] = {}

@router.post("/generate")
async def generate_report(payload: ReportPayload, current_user: dict = Depends(get_superadmin_user)):
    targets = payload.targets
    if not targets:
        raise HTTPException(status_code=400, detail="No report targets selected")
    
    date_range = payload.dateRange or {}
    start = date_range.get("start")
    end = date_range.get("end")

    output = io.StringIO()
    writer = csv.writer(output)
    
    if start and end:
        writer.writerow([f"REPORT FILTER: From {start} to {end}"])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        for target_id in targets:
            if target_id not in REPORT_TARGETS:
                continue
            
            target_cfg = REPORT_TARGETS[target_id]
            
            # Write target header
            writer.writerow([])
            writer.writerow([f"--- REPORT DATA: {target_cfg['label']} ---"])
            
            if "query" in target_cfg:
                sql = target_cfg["query"]
                # Apply date filter to Forensic Security Audit
                if target_id == "forensic_security" and start and end:
                    # SECURITY FIX: Validate date format before interpolation to prevent SQL injection.
                    # Only allow ISO date strings (YYYY-MM-DD).
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', start) or not re.match(r'^\d{4}-\d{2}-\d{2}$', end):
                        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
                    sql = sql.replace("WHERE", f"WHERE (timestamp BETWEEN '{start} 00:00:00' AND '{end} 23:59:59') AND")
                cursor.execute(sql)
            else:
                table = target_cfg["table"]
                where = target_cfg.get("filter", "1=1")
                fields = target_cfg.get("fields", "*")
                
                # Apply date filter to standard tables if they have timestamp
                if table in ["activity_logs", "login_sessions"] and start and end:
                    # SECURITY FIX: Validate date format before interpolation.
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', start) or not re.match(r'^\d{4}-\d{2}-\d{2}$', end):
                        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
                    where += f" AND timestamp BETWEEN '{start} 00:00:00' AND '{end} 23:59:59'"
                
                cursor.execute(f"SELECT {fields} FROM {table} WHERE {where}")
            
            rows = cursor.fetchall()
            
            if rows:
                # Write column headers
                headers = list(rows[0].keys())
                writer.writerow(headers)
                
                # Write rows
                for row in rows:
                    values = []
                    for h in headers:
                        val = row[h]
                        if isinstance(val, (dict, list)):
                            val = json.dumps(val, ensure_ascii=False)
                        elif isinstance(val, datetime):
                            val = val.isoformat()
                        values.append(val)
                    writer.writerow(values)
            else:
                writer.writerow(["No data found for this category"])

        output.seek(0)
        filename = f"NTA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        print(f"Report Generation Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cursor.close()
        conn.close()
