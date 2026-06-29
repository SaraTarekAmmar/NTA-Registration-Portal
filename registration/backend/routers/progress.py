from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from core.database import get_db_connection
from core.auth import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


# ── Steps Pool: list all steps for the builder UI ──────────────────────────
@router.get("/steps")
async def list_steps(step_type: Optional[str] = None):
    """Return all steps from steps_pool, optionally filtered by type."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        if step_type:
            cur.execute(
                "SELECT id, name, type, frontend_component_route FROM steps_pool WHERE type = %s ORDER BY id",
                (step_type,)
            )
        else:
            cur.execute(
                "SELECT id, name, type, frontend_component_route FROM steps_pool ORDER BY id"
            )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


# ── Course Workflow: save the DAG adjacency list ────────────────────────────
class WorkflowEdge(BaseModel):
    current_step_id: int
    next_step_id: Optional[int] = None      # None = terminal step
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None   # JSON string
    meta_data: Optional[str] = None         # JSON string


class SaveWorkflowRequest(BaseModel):
    course_id: int
    edges: List[WorkflowEdge]


@router.post("/workflow")
async def save_workflow(req: SaveWorkflowRequest):
    """Replace the entire DAG for a course with the submitted edge list."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        # Clear existing workflow for this course
        cur.execute("DELETE FROM course_workflows WHERE course_id = %s", (req.course_id,))

        for edge in req.edges:
            cur.execute(
                """
                INSERT INTO course_workflows
                    (course_id, current_step_id, next_step_id,
                     condition_type, condition_value, meta_data)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    req.course_id,
                    edge.current_step_id,
                    edge.next_step_id,
                    edge.condition_type,
                    edge.condition_value,
                    edge.meta_data,
                )
            )

        conn.commit()
        return {"status": "ok", "edges_saved": len(req.edges)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()



class AdvanceRequest(BaseModel):
    course_id: int
    current_step_id: int
    payload: Dict[str, Any]

@router.post("/advance")
async def advance_progress(req: AdvanceRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        # 1. Fetch current step validation rules
        cur.execute("SELECT validation_rule_schema FROM steps_pool WHERE id = %s", (req.current_step_id,))
        step_data = cur.fetchone()
        if not step_data:
            raise HTTPException(status_code=404, detail="Step not found")
        
        # 2. Query course_workflows for next routes
        cur.execute("""
            SELECT next_step_id, condition_type, condition_value, meta_data 
            FROM course_workflows 
            WHERE course_id = %s AND current_step_id = %s
        """, (req.course_id, req.current_step_id))
        routes = cur.fetchall()
        
        if not routes:
            raise HTTPException(status_code=404, detail="No workflow routes found from this step")
            
        next_step_id = None
        target_meta = None
        route_matched = False
        
        # 3. Evaluate Conditions
        for route in routes:
            c_type = route.get("condition_type")
            c_val_str = route.get("condition_value")
            
            if not c_type or c_type == 'null':
                # Default route if no condition
                if not route_matched: 
                    next_step_id = route['next_step_id']
                    target_meta = route.get('meta_data')
                    route_matched = True
                continue
                
            try:
                c_val = json.loads(c_val_str) if isinstance(c_val_str, str) else c_val_str
            except:
                c_val = {}
                
            if c_type == "field_equals":
                field = c_val.get("field")
                val = c_val.get("value")
                if req.payload.get(field) == val:
                    next_step_id = route['next_step_id']
                    target_meta = route.get('meta_data')
                    route_matched = True
                    break
            elif c_type == "score_above":
                field = c_val.get("field")
                val = c_val.get("value")
                # Ensure we have a valid float score to compare
                try:
                    payload_val = float(req.payload.get(field, 0))
                    target_val = float(val)
                    if payload_val > target_val:
                        next_step_id = route['next_step_id']
                        target_meta = route.get('meta_data')
                        route_matched = True
                        break
                except ValueError:
                    pass
                    
        if not route_matched:
            raise HTTPException(status_code=400, detail="Could not determine next step based on payload")
            
        # 4. Gatekeeping (Time-based)
        status = "pending"
        if target_meta:
            try:
                meta = json.loads(target_meta) if isinstance(target_meta, str) else target_meta
                exam_date_str = meta.get("exam_date")
                if exam_date_str:
                    exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d %H:%M:%S")
                    if exam_date > datetime.now():
                        status = "waiting_for_event"
            except Exception as e:
                pass
                
        if next_step_id is not None:
            cur.execute("SELECT type FROM steps_pool WHERE id = %s", (next_step_id,))
            next_step_data = cur.fetchone()
            
            if next_step_data and next_step_data['type'] == 'admission':
                # Fire an event for Staff/Admin Portal (e.g. notify assigned reviewer)
                print(f"[EVENT FIRED] Applicant {user_id} reached Admission Phase for Course {req.course_id} at Step {next_step_id}")
            
        # 6. Fetch existing application_data to merge
        cur.execute("SELECT application_data FROM applicant_progress WHERE applicant_id = %s AND course_id = %s", (user_id, req.course_id))
        row = cur.fetchone()
        existing_data = {}
        if row and row.get('application_data'):
            try:
                data = row['application_data']
                existing_data = json.loads(data) if isinstance(data, str) else data
            except:
                pass
        
        # Merge new payload
        existing_data.update(req.payload)
        new_app_data_str = json.dumps(existing_data, ensure_ascii=False)
            
        # 7. Update applicant_progress
        cur.execute("""
            UPDATE applicant_progress 
            SET current_step_id = %s, status = %s, application_data = %s
            WHERE applicant_id = %s AND course_id = %s
        """, (next_step_id, status, new_app_data_str, user_id, req.course_id))
        
        if cur.rowcount == 0:
            # If not exists, insert it
            cur.execute("""
                INSERT INTO applicant_progress (applicant_id, course_id, current_step_id, status, application_data)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, req.course_id, next_step_id, status, new_app_data_str))

        if next_step_id is None:
            # Terminal state reached: map to applications table
            cur.execute("SELECT id FROM applications WHERE user_id = %s AND course_id = %s", (user_id, req.course_id))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO applications (user_id, course_id, status)
                    VALUES (%s, %s, %s)
                """, (user_id, req.course_id, "idle"))
            
        conn.commit()
        return {"status": "success", "next_step_id": next_step_id, "new_status": status}
        
    finally:
        cur.close()
        conn.close()


@router.get("/status")
async def get_progress_status(course_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT ap.current_step_id, ap.status, sp.frontend_component_route, sp.type 
            FROM applicant_progress ap
            JOIN steps_pool sp ON ap.current_step_id = sp.id
            WHERE ap.applicant_id = %s AND ap.course_id = %s
        """, (user_id, course_id))
        
        progress = cur.fetchone()
        if not progress:
            return {"status": "not_started"}
            
        # JIT Check
        if progress['status'] == 'waiting_for_event':
            # Check meta_data in workflow for this step
            cur.execute("""
                SELECT meta_data FROM course_workflows
                WHERE course_id = %s AND next_step_id = %s
                LIMIT 1
            """, (course_id, progress['current_step_id']))
            wf = cur.fetchone()
            if wf and wf.get('meta_data'):
                meta_str = wf['meta_data']
                try:
                    meta = json.loads(meta_str) if isinstance(meta_str, str) else meta_str
                    exam_date_str = meta.get("exam_date")
                    if exam_date_str:
                        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d %H:%M:%S")
                        if exam_date <= datetime.now():
                            # Event passed, unlock
                            cur.execute("""
                                UPDATE applicant_progress 
                                SET status = 'pending' 
                                WHERE applicant_id = %s AND course_id = %s
                            """, (user_id, course_id))
                            conn.commit()
                            progress['status'] = 'pending'
                except:
                    pass
                    
        # RBAC Lockout for Applicant Portal
        if progress.get('type') == 'admission':
            progress['status'] = 'admission_phase'
            
        response_data = {
            "status": progress['status'],
            "current_step_id": progress['current_step_id'],
            "frontend_component_route": progress['frontend_component_route']
        }
        
        if progress['status'] == 'waiting_for_event' and 'wf' in locals() and wf and wf.get('meta_data'):
            try:
                response_data['meta_data'] = json.loads(wf['meta_data']) if isinstance(wf['meta_data'], str) else wf['meta_data']
            except:
                pass
                
        return response_data
    finally:
        cur.close()
        conn.close()
