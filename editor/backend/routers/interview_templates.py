import json
from fastapi import APIRouter, Depends, HTTPException, Query
from core.database import get_db_connection
from core.auth import require_editor
from schemas.interview import InterviewTemplate, InterviewTemplateCreate, InterviewTemplateUpdate
from typing import List

router = APIRouter(prefix="/api/interview-templates", tags=["Interview Templates"])

@router.get("", response_model=List[InterviewTemplate])
async def get_interview_templates(
    editor_data: dict = Depends(require_editor)
):
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        c.execute("SELECT * FROM interview_templates WHERE is_active = 1")
        rows = c.fetchall()
        for row in rows:
            if isinstance(row["criteria_json"], str):
                row["criteria_json"] = json.loads(row["criteria_json"])
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("", response_model=InterviewTemplate)
async def create_interview_template(
    template: InterviewTemplateCreate,
    editor_data: dict = Depends(require_editor)
):
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        c.execute("""
            INSERT INTO interview_templates (name, program_type, criteria_json, created_by)
            VALUES (%s, %s, %s, %s)
        """, (
            template.name,
            template.program_type,
            json.dumps([c.model_dump() for c in template.criteria_json], ensure_ascii=False),
            editor_data.get("sub")
        ))
        db.commit()
        template_id = c.lastrowid
        c.execute("SELECT * FROM interview_templates WHERE id = %s", (template_id,))
        row = c.fetchone()
        if isinstance(row["criteria_json"], str):
            row["criteria_json"] = json.loads(row["criteria_json"])
        return row
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.put("/{template_id}", response_model=InterviewTemplate)
async def update_interview_template(
    template_id: int,
    template: InterviewTemplateUpdate,
    editor_data: dict = Depends(require_editor)
):
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        c.execute("""
            UPDATE interview_templates 
            SET name = %s, program_type = %s, criteria_json = %s, is_active = %s, updated_by = %s
            WHERE id = %s
        """, (
            template.name,
            template.program_type,
            json.dumps([c.model_dump() for c in template.criteria_json], ensure_ascii=False),
            template.is_active,
            editor_data.get("sub"),
            template_id
        ))
        db.commit()
        
        c.execute("SELECT * FROM interview_templates WHERE id = %s", (template_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")
            
        if isinstance(row["criteria_json"], str):
            row["criteria_json"] = json.loads(row["criteria_json"])
        return row
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
