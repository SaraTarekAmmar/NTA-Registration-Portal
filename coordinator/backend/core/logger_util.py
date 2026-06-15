import json
import traceback as tb_module
from datetime import datetime
from .database import get_db_connection
from pathlib import Path
import os


def log_activity(category, event_type, level="INFO", component="Coordinator",
                 user_id=None, national_id=None, role=None,
                 ip_address=None, user_agent=None, request_path=None,
                 status_code=None, details=None, session_id=None,
                 trace_id=None, traceback=None, payload_json=None,
                 status="Logged", duration_ms=None):
    """
    Logs activity into the shared activity_logs table.
    Lightweight copy of admin logger_util — coordinator-specific.
    """
    event_type = str(event_type)[:100] if event_type else "UNKNOWN"
    national_id = str(national_id)[:14] if national_id else None
    role = str(role)[:50] if role else None
    ip_address = str(ip_address)[:45] if ip_address else None
    request_path = str(request_path)[:255] if request_path else None
    user_agent = str(user_agent)[:2000] if user_agent else None
    component = str(component)[:100] if component else "Coordinator"
    status = str(status)[:50] if status else "Logged"

    if status_code and level == "INFO":
        if status_code >= 500:
            level = "CRITICAL"
        elif status_code >= 400:
            level = "WARNING"

    level = level.upper() if level in ["INFO", "WARNING", "CRITICAL"] else "INFO"

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO activity_logs
               (category, level, component, event_type, user_id, national_id, role,
                ip_address, user_agent, request_path, status_code, trace_id,
                details, traceback, payload_json, status, duration_ms)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                category, level, component, event_type, user_id, national_id, role,
                ip_address, user_agent, request_path, status_code, trace_id,
                json.dumps(details) if details else None,
                traceback,
                json.dumps(payload_json) if payload_json else None,
                status, duration_ms,
            ),
        )
        db.commit()

        # JSON file logging for coordinator sessions
        if session_id and role == "coordinator":
            try:
                root = Path(__file__).parent.parent.parent.parent
                log_base = root / "data" / "log" / "coordinator"
                os.makedirs(log_base, exist_ok=True)
                existing = list(log_base.glob(f"Session_{session_id}_*.json"))
                if existing:
                    log_file = existing[0]
                else:
                    now = datetime.now()
                    filename = f"Session_{session_id}_{now.strftime('%Y-%m-%d_%H-%M')}.json"
                    log_file = log_base / filename
                actions = []
                if log_file.exists():
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            actions = json.load(f)
                    except Exception:
                        actions = []
                actions.append({
                    "timestamp": datetime.now().isoformat(),
                    "category": category,
                    "event_type": event_type,
                    "details": details,
                })
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
    return tb_module.format_exc()
