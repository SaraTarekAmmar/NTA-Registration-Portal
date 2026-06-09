import json
import uuid
import traceback as tb_module
from datetime import datetime
from .database import get_db_connection
from contextvars import ContextVar
from pathlib import Path

# Global context for session ID and Trace ID
session_context: ContextVar[int] = ContextVar("session_id", default=None)
trace_context: ContextVar[str] = ContextVar("trace_id", default=None)

def log_activity(category, event_type, level="INFO", component="System", 
                 user_id=None, national_id=None, role=None, 
                 ip_address=None, user_agent=None, request_path=None, 
                 status_code=None, details=None, session_id=None, 
                 trace_id=None, traceback=None, payload_json=None, 
                 status="Logged", duration_ms=None):
    """
    Logs an activity into the activity_logs table and optionally to a JSON file if it's an admin/editor session.
    Enhanced with distributed tracing, traceback capture, and component-level visibility.
    """
    import os
    
    # Auto-pickup from context if not passed
    if session_id is None:
        session_id = session_context.get()
    if trace_id is None:
        trace_id = trace_context.get()
    
    # Sanitization: Truncate strings to match database schema limits
    event_type = str(event_type)[:100] if event_type else "UNKNOWN"
    national_id = str(national_id)[:14] if national_id else None
    role = str(role)[:50] if role else None
    ip_address = str(ip_address)[:45] if ip_address else None
    request_path = str(request_path)[:255] if request_path else None
    user_agent = str(user_agent)[:2000] if user_agent else None
    component = str(component)[:100] if component else "System"
    status = str(status)[:50] if status else "Logged"
    
    # Map status code to level if not provided
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
        
        # Ensure complex types are JSON strings
        details_str = json.dumps(details) if details else None
        payload_str = json.dumps(payload_json) if payload_json else None
        
        cursor.execute(query, (
            category, 
            level, 
            component,
            event_type, 
            user_id, 
            national_id, 
            role, 
            ip_address, 
            user_agent, 
            request_path, 
            status_code,
            trace_id,
            details_str,
            traceback,
            payload_str,
            status,
            duration_ms
        ))
        db.commit()
        
        # ── JSON File Logging for Admins, Editors, Superadmins ──
        if session_id and role in ["admin", "editor", "superadmin"]:
            try:
                root = Path(__file__).parent.parent.parent.parent
                log_base = root / "data" / "log" / role
                os.makedirs(log_base, exist_ok=True)
                
                existing_files = list(log_base.glob(f"Session_{session_id}_*.json"))
                if existing_files:
                    log_file = existing_files[0]
                else:
                    now = datetime.now()
                    date_str = now.strftime("%Y-%m-%d")
                    time_str = now.strftime("%H-%M")
                    filename = f"Session_{session_id}_{date_str}_{time_str}.json"
                    log_file = log_base / filename
                
                actions = []
                if log_file.exists():
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            actions = json.load(f)
                    except:
                        actions = []
                
                new_action = {
                    "timestamp": datetime.now().isoformat(),
                    "trace_id": trace_id,
                    "level": level,
                    "component": component,
                    "category": category,
                    "event_type": event_type,
                    "ip_address": ip_address,
                    "request_path": request_path,
                    "status_code": status_code,
                    "details": details,
                    "traceback": traceback,
                    "payload": payload_json,
                    "duration_ms": duration_ms
                }
                actions.append(new_action)
                
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(actions, f, ensure_ascii=False, indent=2)
                    
            except Exception as fe:
                print(f"FAILED TO LOG TO JSON FILE: {fe}")

    except Exception as e:
        print(f"FAILED TO LOG ACTIVITY: {e}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def get_traceback():
    """Returns the current formatted stack trace with file paths and line numbers."""
    return tb_module.format_exc()
