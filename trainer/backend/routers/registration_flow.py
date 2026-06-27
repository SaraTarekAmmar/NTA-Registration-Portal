from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from core.auth import get_current_user
from core.database import get_db_connection
from datetime import date
import json

router = APIRouter(prefix="/api/registration-flow", tags=["Registration Flow"])


def _calculate_age(dob_val) -> Optional[int]:
    if not dob_val:
        return None
    try:
        if isinstance(dob_val, str):
            parts = dob_val.split("-")
            dob = date(int(parts[0]), int(parts[1]), int(parts[2][:2]))
        elif hasattr(dob_val, "year"):
            dob = dob_val
        else:
            return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def _parse_json(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {}
    return val or {}


def _normalize_course_type(value: Optional[str]) -> str:
    value = (value or "").strip()
    return value or "default"


def _get_applicant_course_type(cursor, applicant_id: int) -> Optional[str]:
    cursor.execute(
        """
        SELECT COALESCE(NULLIF(c.classification, ''), NULLIF(c.short_name, '')) AS course_type
        FROM applications a
        LEFT JOIN courses c ON c.id = a.course_id
        WHERE a.user_id = %s
        ORDER BY a.id DESC
        LIMIT 1
        """,
        (applicant_id,),
    )
    row = cursor.fetchone()
    if row and row.get("course_type"):
        return _normalize_course_type(row["course_type"])
    return None


def _get_user_age(cursor, user_id: int) -> Optional[int]:
    cursor.execute("SELECT dob FROM users WHERE id=%s", (user_id,))
    row = cursor.fetchone()
    return _calculate_age(row["dob"] if row else None)


def _resolve_effective_course_type(cursor, applicant_id: int, requested_course_type: Optional[str]) -> str:
    return _get_applicant_course_type(cursor, applicant_id) or _normalize_course_type(requested_course_type)


def _resolve_flow(cursor, applicant_id: int, course_type: str, age: Optional[int]):
    course_type = _normalize_course_type(course_type)
    cursor.execute("SELECT * FROM flow_templates WHERE course_type=%s AND is_active=1 LIMIT 1", (course_type,))
    tmpl = cursor.fetchone()
    if not tmpl:
        cursor.execute("SELECT * FROM flow_templates WHERE course_type='default' AND is_active=1 LIMIT 1")
        tmpl = cursor.fetchone()
    if not tmpl:
        return []

    cursor.execute("SELECT * FROM flow_steps WHERE flow_template_id=%s AND is_active=1 ORDER BY step_order", (tmpl["id"],))
    steps = cursor.fetchall()
    for s in steps:
        s["visibility_rules"] = _parse_json(s.get("visibility_rules"))
        s["unlock_rules"] = _parse_json(s.get("unlock_rules"))
        s["config_json"] = _parse_json(s.get("config_json"))

    cursor.execute("SELECT * FROM applicant_step_overrides WHERE applicant_id=%s", (applicant_id,))
    overrides = {row["step_id"]: row for row in cursor.fetchall()}

    cursor.execute("SELECT * FROM applicant_step_status WHERE applicant_id=%s", (applicant_id,))
    statuses = {row["step_id"]: row for row in cursor.fetchall()}
    done_step_keys = set()
    for sid, rec in statuses.items():
        if rec["status"] in ("submitted", "approved", "skipped"):
            for step in steps:
                if step["id"] == sid:
                    done_step_keys.add(step["step_key"])
                    break

    result = []
    for step in steps:
        vis_rules = step["visibility_rules"]
        unl_rules = step["unlock_rules"]
        is_visible = True
        if age is not None:
            if vis_rules.get("age_min") and age < vis_rules["age_min"]:
                is_visible = False
            if vis_rules.get("age_max") and age > vis_rules["age_max"]:
                is_visible = False

        ov = overrides.get(step["id"])
        if ov and ov["is_visible"] is not None:
            is_visible = bool(ov["is_visible"])
        if not is_visible:
            continue

        is_locked = False
        locked_reason = None
        req_key = unl_rules.get("requires_step_key")
        if req_key and req_key not in done_step_keys:
            is_locked = True
            locked_reason = "Previous step must be completed first"
        if unl_rules.get("manual_only"):
            admin_unlocked = ov and ov["is_locked"] is not None and not bool(ov["is_locked"])
            if not admin_unlocked:
                is_locked = True
                locked_reason = "Manual admin unlock required"
        if ov and ov["is_locked"] is not None:
            is_locked = bool(ov["is_locked"])
            locked_reason = ov.get("reason") or ("Locked by admin" if is_locked else None)

        rec = statuses.get(step["id"])
        current_status = rec["status"] if rec else "pending"
        if current_status in ("submitted", "approved"):
            is_locked = False
            locked_reason = None

        result.append({
            "id": step["id"],
            "step_key": step["step_key"],
            "step_type": step["step_type"],
            "title_ar": step["title_ar"],
            "description_ar": step.get("description_ar"),
            "step_order": step["step_order"],
            "is_required": bool(ov["is_required"]) if ov and ov.get("is_required") is not None else bool(step["is_required"]),
            "is_locked": is_locked,
            "status": current_status,
            "locked_reason": locked_reason,
            "config": _parse_json(ov.get("custom_config")) if ov and ov.get("custom_config") else step["config_json"],
        })
    return result


@router.get("")
async def get_my_flow(course_type: str = "default", current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        age = _get_user_age(cursor, current_user["id"])
        effective_course_type = _resolve_effective_course_type(cursor, current_user["id"], course_type)
        steps = _resolve_flow(cursor, current_user["id"], effective_course_type, age)
        return {"course_type": effective_course_type, "age": age, "steps": steps}
    finally:
        cursor.close()
        db.close()


class StepSubmit(BaseModel):
    step_id: int
    submitted_data: Optional[dict] = None
    course_type: Optional[str] = None


@router.post("/submit")
async def submit_step(body: StepSubmit, current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM flow_steps WHERE id=%s AND is_active=1", (body.step_id,))
        step = cursor.fetchone()
        if not step:
            raise HTTPException(404, "Step not found or inactive")
        age = _get_user_age(cursor, current_user["id"])
        effective_course_type = _resolve_effective_course_type(cursor, current_user["id"], body.course_type)
        flow = _resolve_flow(cursor, current_user["id"], effective_course_type, age)
        step_in_flow = next((s for s in flow if s["id"] == body.step_id), None)
        if not step_in_flow:
            raise HTTPException(403, "Step is not assigned to your registration flow")
        if step_in_flow["is_locked"]:
            raise HTTPException(403, step_in_flow["locked_reason"] or "Step is locked")

        # Basic presence validation for required fields
        if step_in_flow.get("is_required") and not body.submitted_data:
            raise HTTPException(400, "هذه الخطوة تتطلب إدخال بيانات (Step requires data)")
            
        if body.submitted_data and step_in_flow.get("config") and isinstance(step_in_flow["config"], dict) and "fields" in step_in_flow["config"]:
            missing_fields = []
            for field in step_in_flow["config"]["fields"]:
                if field.get("is_required") and field.get("is_active", True):
                    field_id = field.get("field_id")
                    if field_id:
                        val = body.submitted_data.get(field_id)
                        if val is None or str(val).strip() == "":
                            missing_fields.append(field_id)
            if missing_fields:
                raise HTTPException(400, f"الحقول التالية مطلوبة: {', '.join(missing_fields)}")

        data_json = json.dumps(body.submitted_data, ensure_ascii=False) if body.submitted_data else None
        cursor.execute(
            """
            INSERT INTO applicant_step_status
              (applicant_id, step_id, status, completed_at, submitted_data)
            VALUES (%s, %s, 'submitted', NOW(), %s)
            ON DUPLICATE KEY UPDATE
              status='submitted', completed_at=NOW(), submitted_data=VALUES(submitted_data)
            """,
            (current_user["id"], body.step_id, data_json),
        )
        db.commit()
        return {"submitted": True, "step_id": body.step_id, "course_type": effective_course_type}
    finally:
        cursor.close()
        db.close()


@router.get("/my-status")
async def get_my_status(current_user: dict = Depends(get_current_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT st.*, s.title_ar, s.step_key, s.step_order, s.step_type
            FROM applicant_step_status st
            JOIN flow_steps s ON s.id = st.step_id
            WHERE st.applicant_id=%s
            ORDER BY s.step_order
            """,
            (current_user["id"],),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()
