"""
Coordinator Attendance API — migrated from admin/backend/routers/admin.py.
Provides attendance data (logs, photos, analytics) for coordinator role only.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse, RedirectResponse
from typing import Optional
from pathlib import Path
from core.auth import require_coordinator
from core.database import get_db_connection

router = APIRouter(prefix="/api/coordinator/attendance", tags=["Coordinator Attendance"])


@router.get("/summary")
async def attendance_summary(coordinator: dict = Depends(require_coordinator)):
    """Dashboard KPI summary: today's attendance, absent, pending excuses."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Today's attendance count
        cursor.execute(
            """SELECT COUNT(DISTINCT national_id) AS present_today
               FROM attendance_logs
               WHERE DATE(recorded_at) = CURDATE() AND event_type = 'ENTER'"""
        )
        present = cursor.fetchone()["present_today"]

        # Total enrolled trainees (approved applications)
        cursor.execute("SELECT COUNT(DISTINCT user_id) AS total FROM applications WHERE status = 'approved'")
        total_enrolled = cursor.fetchone()["total"]

        absent_today = max(0, total_enrolled - present)

        # Pending excuses
        cursor.execute("SELECT COUNT(*) AS pending FROM attendance_permissions WHERE status = 'pending'")
        pending = cursor.fetchone()["pending"]

        # Accepted excuses
        cursor.execute("SELECT COUNT(*) AS accepted FROM attendance_permissions WHERE status = 'accepted'")
        accepted = cursor.fetchone()["accepted"]

        # Rejected excuses
        cursor.execute("SELECT COUNT(*) AS rejected FROM attendance_permissions WHERE status = 'rejected'")
        rejected = cursor.fetchone()["rejected"]

        return {
            "present_today": present,
            "absent_today": absent_today,
            "total_enrolled": total_enrolled,
            "pending_excuses": pending,
            "accepted_excuses": accepted,
            "rejected_excuses": rejected,
        }
    finally:
        cursor.close()
        db.close()


@router.get("")
async def get_attendance(
    course_id: int,
    coordinator: dict = Depends(require_coordinator),
):
    """Full attendance grid for a course — sessions × students."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Fetch Course Sessions
        cursor.execute(
            """SELECT id, topic AS name, DATE_FORMAT(session_date, '%%e %%M %%Y') AS date
               FROM course_sessions
               WHERE course_id = %s
               ORDER BY session_date ASC""",
            (course_id,),
        )
        sessions = cursor.fetchall()

        # 2. Enrolled Students
        cursor.execute(
            """SELECT u.id, u.full_name_ar AS name, u.national_id AS nationalId
               FROM users u
               JOIN applications a ON u.id = a.user_id
               WHERE a.course_id = %s AND a.status = 'approved'""",
            (course_id,),
        )
        students = cursor.fetchall()

        if not students:
            return {"sessions": sessions, "students": []}

        session_ids = [s["id"] for s in sessions]
        if not session_ids:
            return {"sessions": [], "students": students}

        # 3. Attendance Logs
        placeholders = ", ".join(["%s"] * len(session_ids))
        cursor.execute(
            f"""SELECT national_id, session_id, event_type, recorded_at, match_score
                FROM attendance_logs
                WHERE session_id IN ({placeholders})
                ORDER BY recorded_at ASC""",
            tuple(session_ids),
        )
        logs = cursor.fetchall()

        # 4. Excuses
        cursor.execute(
            """SELECT user_id,
                      type AS permission_type,
                      reason AS permission_reason,
                      DATE_FORMAT(date, '%%e %%M %%Y') AS date,
                      status
               FROM attendance_permissions
               WHERE course_id = %s AND status = 'accepted'""",
            (course_id,),
        )
        permissions = cursor.fetchall()

        # Build lookup maps
        log_map = {}
        for log in logs:
            nid = log["national_id"]
            sid = str(log["session_id"])
            etype = log["event_type"]
            log_map.setdefault(nid, {}).setdefault(sid, {})
            if etype == "ENTER" and "ENTER" not in log_map[nid][sid]:
                log_map[nid][sid]["ENTER"] = log
            elif etype == "LEAVE":
                log_map[nid][sid]["LEAVE"] = log

        perm_map = {}
        for p in permissions:
            perm_map.setdefault(p["user_id"], {})[p["date"]] = p

        # Merge into student objects
        for st in students:
            st["attendance"] = {}
            st_logs = log_map.get(st["nationalId"], {})
            st_perms = perm_map.get(st["id"], {})
            for s in sessions:
                sid = str(s["id"])
                s_date = s["date"]
                log_entry = st_logs.get(sid, {})
                perm_entry = st_perms.get(s_date)
                if "ENTER" in log_entry:
                    enter_log = log_entry["ENTER"]
                    exit_log = log_entry.get("LEAVE")
                    att = {
                        "status": "present",
                        "entry_time": enter_log["recorded_at"]
                        .strftime("%I:%M %p")
                        .replace("AM", "ص")
                        .replace("PM", "م"),
                        "entry_photo": f"/api/coordinator/attendance/photo/{st['nationalId']}/{sid}/ENTER",
                        "match_score": float(enter_log["match_score"] or 0),
                    }
                    if exit_log:
                        att["exit_time"] = (
                            exit_log["recorded_at"]
                            .strftime("%I:%M %p")
                            .replace("AM", "ص")
                            .replace("PM", "م")
                        )
                        att["exit_photo"] = f"/api/coordinator/attendance/photo/{st['nationalId']}/{sid}/LEAVE"
                    st["attendance"][sid] = att
                elif perm_entry:
                    st["attendance"][sid] = {
                        "status": "excused",
                        "permission_type": perm_entry["permission_type"],
                        "permission_reason": perm_entry["permission_reason"],
                    }
                else:
                    st["attendance"][sid] = {"status": "absent"}

        return {"sessions": sessions, "students": students}
    finally:
        cursor.close()
        db.close()


@router.get("/courses")
async def list_courses_for_attendance(coordinator: dict = Depends(require_coordinator)):
    """Returns courses that have sessions (for the course dropdown filter)."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT DISTINCT c.id, c.title, c.title_ar
               FROM courses c
               JOIN course_sessions cs ON c.id = cs.course_id
               ORDER BY c.title_ar"""
        )
        return cursor.fetchall() or []
    finally:
        cursor.close()
        db.close()


@router.get("/photo/{national_id}/{session_id}/{event_type}")
async def get_attendance_photo(
    national_id: str,
    session_id: int,
    event_type: str,
    coordinator: dict = Depends(require_coordinator),
):
    """Serve check-in/check-out face photos from attendance_logs."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT image_path FROM attendance_logs
               WHERE national_id = %s AND session_id = %s AND event_type = %s
               ORDER BY recorded_at DESC LIMIT 1""",
            (national_id, session_id, event_type),
        )
        row = cursor.fetchone()
        if row and row.get("image_path"):
            project_root = Path(__file__).parent.parent.parent.parent
            abs_path = project_root / row["image_path"]
            if abs_path.exists():
                return FileResponse(str(abs_path))
    except Exception as e:
        print(f"Error retrieving attendance photo: {e}")
    finally:
        cursor.close()
        db.close()

    return RedirectResponse(url=f"https://i.pravatar.cc/300?u={national_id}")
