from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from core.auth import get_admin_user
from core.database import get_db_connection
import json

router = APIRouter(prefix="/api/flow-builder", tags=["Flow Builder"])

STEP_TYPE_LABELS = {
    "personal_info":      "معلومات شخصية",
    "document_upload":    "رفع مستندات",
    "course_selection":   "اختيار الدورة",
    "admission_test":     "اختبار قبول",
    "essay":              "مقال",
    "interview":          "مقابلة",
    "payment":            "دفع",
    "admin_review":       "مراجعة إدارية",
    "consent_form":       "نموذج موافقة",
    "custom_question":    "سؤال مخصص",
    "final_confirmation": "تأكيد نهائي",
}


def _parse_json_cols(row, cols=("visibility_rules", "unlock_rules", "config_json")):
    for col in cols:
        if isinstance(row.get(col), str):
            try:
                row[col] = json.loads(row[col])
            except Exception:
                row[col] = {}
        elif row.get(col) is None:
            row[col] = {}
    return row


# ── Pydantic models ───────────────────────────────────────────────

class TemplateCreate(BaseModel):
    course_type: str
    name: str
    description: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class StepCreate(BaseModel):
    step_key: str
    step_type: str
    title_ar: str
    description_ar: Optional[str] = None
    step_order: int = 0
    is_required: bool = True
    visibility_rules: Optional[dict] = None
    unlock_rules: Optional[dict] = None
    config_json: Optional[dict] = None


class StepUpdate(BaseModel):
    step_key: Optional[str] = None
    step_type: Optional[str] = None
    title_ar: Optional[str] = None
    description_ar: Optional[str] = None
    step_order: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    visibility_rules: Optional[dict] = None
    unlock_rules: Optional[dict] = None
    config_json: Optional[dict] = None


class ReorderItem(BaseModel):
    step_id: int
    step_order: int


class OverrideUpsert(BaseModel):
    applicant_id: int
    step_id: int
    is_visible: Optional[bool] = None
    is_locked: Optional[bool] = None
    is_required: Optional[bool] = None
    custom_config: Optional[dict] = None
    reason: Optional[str] = None


# ── Templates ─────────────────────────────────────────────────────

@router.get("/templates")
async def list_templates(admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.*, COUNT(s.id) AS step_count
            FROM flow_templates t
            LEFT JOIN flow_steps s ON s.flow_template_id = t.id AND s.is_active = 1
            GROUP BY t.id
            ORDER BY t.course_type
        """)
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


@router.post("/templates", status_code=201)
async def create_template(body: TemplateCreate, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM flow_templates WHERE course_type=%s", (body.course_type,))
        if cursor.fetchone():
            raise HTTPException(400, "قالب لهذا النوع موجود بالفعل")
        cursor.execute(
            "INSERT INTO flow_templates (course_type, name, description, created_by) VALUES (%s,%s,%s,%s)",
            (body.course_type, body.name, body.description, admin["id"]),
        )
        db.commit()
        cursor.execute("SELECT * FROM flow_templates WHERE id=%s", (cursor.lastrowid,))
        return cursor.fetchone()
    finally:
        cursor.close(); db.close()


@router.get("/templates/{template_id}")
async def get_template(template_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM flow_templates WHERE id=%s", (template_id,))
        tmpl = cursor.fetchone()
        if not tmpl:
            raise HTTPException(404, "القالب غير موجود")
        cursor.execute(
            "SELECT * FROM flow_steps WHERE flow_template_id=%s ORDER BY step_order",
            (template_id,),
        )
        steps = [_parse_json_cols(s) for s in cursor.fetchall()]
        tmpl["steps"] = steps
        return tmpl
    finally:
        cursor.close(); db.close()


@router.put("/templates/{template_id}")
async def update_template(template_id: int, body: TemplateUpdate, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        fields, vals = [], []
        if body.name is not None:        fields.append("name=%s");        vals.append(body.name)
        if body.description is not None: fields.append("description=%s"); vals.append(body.description)
        if body.is_active is not None:   fields.append("is_active=%s");   vals.append(1 if body.is_active else 0)
        if not fields:
            raise HTTPException(422, "لا توجد حقول للتحديث")
        fields.append("updated_by=%s"); vals.append(admin["id"])
        vals.append(template_id)
        cursor.execute(f"UPDATE flow_templates SET {', '.join(fields)} WHERE id=%s", vals)
        db.commit()
        return {"updated": True}
    finally:
        cursor.close(); db.close()


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM flow_templates WHERE id=%s", (template_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "القالب غير موجود")
        return {"deleted": True}
    finally:
        cursor.close(); db.close()


# ── Steps ──────────────────────────────────────────────────────────

@router.post("/templates/{template_id}/steps", status_code=201)
async def add_step(template_id: int, body: StepCreate, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM flow_templates WHERE id=%s", (template_id,))
        if not cursor.fetchone():
            raise HTTPException(404, "القالب غير موجود")
        vis  = json.dumps(body.visibility_rules) if body.visibility_rules else None
        unl  = json.dumps(body.unlock_rules)     if body.unlock_rules     else None
        cfg  = json.dumps(body.config_json)      if body.config_json      else None
        cursor.execute("""
            INSERT INTO flow_steps
              (flow_template_id, step_key, step_type, title_ar, description_ar,
               step_order, is_required, visibility_rules, unlock_rules, config_json, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (template_id, body.step_key, body.step_type, body.title_ar, body.description_ar,
              body.step_order, 1 if body.is_required else 0, vis, unl, cfg, admin["id"]))
        db.commit()
        cursor.execute("SELECT * FROM flow_steps WHERE id=%s", (cursor.lastrowid,))
        return _parse_json_cols(cursor.fetchone())
    finally:
        cursor.close(); db.close()


@router.put("/steps/{step_id}")
async def update_step(step_id: int, body: StepUpdate, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        fields, vals = [], []
        if body.step_key         is not None: fields.append("step_key=%s");         vals.append(body.step_key)
        if body.step_type        is not None: fields.append("step_type=%s");        vals.append(body.step_type)
        if body.title_ar         is not None: fields.append("title_ar=%s");         vals.append(body.title_ar)
        if body.description_ar   is not None: fields.append("description_ar=%s");   vals.append(body.description_ar)
        if body.step_order       is not None: fields.append("step_order=%s");       vals.append(body.step_order)
        if body.is_required      is not None: fields.append("is_required=%s");      vals.append(1 if body.is_required else 0)
        if body.is_active        is not None: fields.append("is_active=%s");        vals.append(1 if body.is_active else 0)
        if body.visibility_rules is not None: fields.append("visibility_rules=%s"); vals.append(json.dumps(body.visibility_rules))
        if body.unlock_rules     is not None: fields.append("unlock_rules=%s");     vals.append(json.dumps(body.unlock_rules))
        if body.config_json      is not None: fields.append("config_json=%s");      vals.append(json.dumps(body.config_json))
        if not fields:
            raise HTTPException(422, "لا توجد حقول للتحديث")
        fields.append("updated_by=%s"); vals.append(admin["id"])
        vals.append(step_id)
        cursor.execute(f"UPDATE flow_steps SET {', '.join(fields)} WHERE id=%s", vals)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "الخطوة غير موجودة")
        return {"updated": True}
    finally:
        cursor.close(); db.close()


@router.delete("/steps/{step_id}")
async def delete_step(step_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM flow_steps WHERE id=%s", (step_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "الخطوة غير موجودة")
        return {"deleted": True}
    finally:
        cursor.close(); db.close()


@router.post("/steps/reorder")
async def reorder_steps(items: List[ReorderItem], admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        for item in items:
            cursor.execute(
                "UPDATE flow_steps SET step_order=%s, updated_by=%s WHERE id=%s",
                (item.step_order, admin["id"], item.step_id),
            )
        db.commit()
        return {"reordered": len(items)}
    finally:
        cursor.close(); db.close()


# ── Overrides ──────────────────────────────────────────────────────

@router.get("/overrides")
async def list_overrides(applicant_id: int = None, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if applicant_id:
            cursor.execute("""
                SELECT o.*, s.title_ar, s.step_key, u.full_name_ar AS applicant_name
                FROM applicant_step_overrides o
                JOIN flow_steps s ON s.id = o.step_id
                LEFT JOIN users u ON u.id = o.applicant_id
                WHERE o.applicant_id=%s
                ORDER BY o.created_at DESC
            """, (applicant_id,))
        else:
            cursor.execute("""
                SELECT o.*, s.title_ar, s.step_key, u.full_name_ar AS applicant_name
                FROM applicant_step_overrides o
                JOIN flow_steps s ON s.id = o.step_id
                LEFT JOIN users u ON u.id = o.applicant_id
                ORDER BY o.created_at DESC LIMIT 300
            """)
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


@router.post("/overrides", status_code=201)
async def upsert_override(body: OverrideUpsert, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cfg = json.dumps(body.custom_config) if body.custom_config else None
        iv = 1 if body.is_visible  is True else (0 if body.is_visible  is False else None)
        il = 1 if body.is_locked   is True else (0 if body.is_locked   is False else None)
        ir = 1 if body.is_required is True else (0 if body.is_required is False else None)
        cursor.execute("""
            INSERT INTO applicant_step_overrides
              (applicant_id, step_id, is_visible, is_locked, is_required, custom_config, reason, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              is_visible=VALUES(is_visible), is_locked=VALUES(is_locked),
              is_required=VALUES(is_required), custom_config=VALUES(custom_config),
              reason=VALUES(reason), updated_by=%s
        """, (body.applicant_id, body.step_id, iv, il, ir, cfg, body.reason, admin["id"], admin["id"]))
        db.commit()
        return {"saved": True}
    finally:
        cursor.close(); db.close()


@router.delete("/overrides/{override_id}")
async def delete_override(override_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM applicant_step_overrides WHERE id=%s", (override_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Override not found")
        return {"deleted": True}
    finally:
        cursor.close(); db.close()


# ── Status management (admin side) ────────────────────────────────

@router.get("/applicant-status/{applicant_id}")
async def get_applicant_status(applicant_id: int, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT st.*, s.title_ar, s.step_key, s.step_order
            FROM applicant_step_status st
            JOIN flow_steps s ON s.id = st.step_id
            WHERE st.applicant_id=%s
            ORDER BY s.step_order
        """, (applicant_id,))
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()


@router.patch("/applicant-status/{applicant_id}/{step_id}")
async def set_step_status(applicant_id: int, step_id: int, body: dict, admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        status = body.get("status", "approved")
        reason = body.get("reason", "")
        cursor.execute("""
            INSERT INTO applicant_step_status (applicant_id, step_id, status, completed_at, reviewed_by, reviewed_at, locked_reason)
            VALUES (%s, %s, %s, NOW(), %s, NOW(), %s)
            ON DUPLICATE KEY UPDATE status=VALUES(status), reviewed_by=VALUES(reviewed_by),
              reviewed_at=NOW(), locked_reason=VALUES(locked_reason),
              completed_at=IF(VALUES(status) IN ('submitted','approved'), NOW(), completed_at)
        """, (applicant_id, step_id, status, admin["id"], reason))
        db.commit()
        return {"updated": True}
    finally:
        cursor.close(); db.close()


# ── Preview ────────────────────────────────────────────────────────

@router.get("/preview")
async def preview_flow(
    course_type: str = "default",
    age: int = None,
    admin: dict = Depends(get_admin_user),
):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM flow_templates WHERE course_type=%s AND is_active=1", (course_type,))
        tmpl = cursor.fetchone()
        if not tmpl:
            cursor.execute("SELECT * FROM flow_templates WHERE course_type='default' AND is_active=1")
            tmpl = cursor.fetchone()
        if not tmpl:
            return {"course_type": course_type, "steps": []}

        cursor.execute(
            "SELECT * FROM flow_steps WHERE flow_template_id=%s AND is_active=1 ORDER BY step_order",
            (tmpl["id"],),
        )
        steps = [_parse_json_cols(s) for s in cursor.fetchall()]

        result = []
        for step in steps:
            vis = step.get("visibility_rules") or {}
            if age is not None:
                if vis.get("age_min") and age < vis["age_min"]:
                    continue
                if vis.get("age_max") and age > vis["age_max"]:
                    continue
            unl = step.get("unlock_rules") or {}
            step["preview_locked"] = bool(unl.get("requires_step_key") or unl.get("manual_only"))
            result.append(step)

        return {"course_type": course_type, "template": tmpl["name"], "age": age, "steps": result}
    finally:
        cursor.close(); db.close()


# ── Reference data ─────────────────────────────────────────────────

@router.get("/step-types")
async def get_step_types(admin: dict = Depends(get_admin_user)):
    return [{"type": k, "label_ar": v} for k, v in STEP_TYPE_LABELS.items()]


@router.get("/course-types")
async def get_course_types(admin: dict = Depends(get_admin_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, course_type, name, is_active FROM flow_templates ORDER BY course_type")
        return cursor.fetchall()
    finally:
        cursor.close(); db.close()
