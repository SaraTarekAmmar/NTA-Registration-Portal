import json
import traceback as tb_module
from datetime import datetime
from .database import get_db_connection
from pathlib import Path
import os
from contextvars import ContextVar

# Context vars for distributed tracing (mirrors other portals)
session_context: ContextVar[str] = ContextVar("session_id", default=None)
trace_context: ContextVar[str] = ContextVar("trace_id", default=None)

def log_activity(category, event_type, level="INFO", component="System",
                 user_id=None, national_id=None, role=None,
                 ip_address=None, user_agent=None, request_path=None,
                 status_code=None, details=None, session_id=None,
                 trace_id=None, traceback=None, payload_json=None,
                 status="Logged", duration_ms=None):
    """
    Logs an activity into the activity_logs table.
    Identical contract to other portals — same DB table, same schema.
    """
    event_type   = str(event_type)[:100]  if event_type   else "UNKNOWN"
    national_id  = str(national_id)[:14]  if national_id  else None
    role         = str(role)[:50]          if role         else None
    ip_address   = str(ip_address)[:45]   if ip_address   else None
    request_path = str(request_path)[:255] if request_path else None
    user_agent   = str(user_agent)[:2000]  if user_agent   else None
    component    = str(component)[:100]    if component    else "System"
    status       = str(status)[:50]        if status       else "Logged"

    if status_code and level == "INFO":
        if status_code >= 500: level = "CRITICAL"
        elif status_code >= 400: level = "WARNING"
    level = level.upper() if level in ["INFO", "WARNING", "CRITICAL"] else "INFO"

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        query = """
            INSERT INTO activity_logs
            (category, level, component, event_type, user_id, national_id, role,
             ip_address, user_agent, request_path, status_code, trace_id,
             details, traceback, payload_json, status, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        details_str = json.dumps(details, ensure_ascii=False) if details else None
        payload_str = json.dumps(payload_json, ensure_ascii=False) if payload_json else None
        cursor.execute(query, (
            category, level, component, event_type, user_id, national_id, role,
            ip_address, user_agent, request_path, status_code, trace_id,
            details_str, traceback, payload_str, status, duration_ms
        ))
        db.commit()
    except Exception as e:
        print(f"[FRONT LOG ERROR] {e}")
    finally:
        if cursor: cursor.close()
        if db:     db.close()

def get_traceback():
    return tb_module.format_exc()
