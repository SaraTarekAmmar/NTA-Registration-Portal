from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import mysql.connector
import os
from .auth import get_current_user
from core.security import get_superadmin_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])

from core.database import get_db_connection

class AlertCreate(BaseModel):
    alert_text: str
    target_type: str # 'course', 'user', 'global'
    target_id: Optional[int] = None

class AlertOut(BaseModel):
    id: int
    alert_text: str
    target_type: str
    target_id: Optional[int]
    is_active: bool
    created_at: datetime
    created_by: int
    creator_name: Optional[str] = None

@router.post("/", response_model=AlertOut)
async def create_alert(alert: AlertCreate, current_user: dict = Depends(get_superadmin_user)):
    if current_user["role"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        INSERT INTO system_alerts (alert_text, target_type, target_id, created_by)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (alert.alert_text, alert.target_type, alert.target_id, current_user["id"]))
        conn.commit()
        alert_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM system_alerts WHERE id = %s", (alert_id,))
        new_alert = cursor.fetchone()
        return new_alert
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/", response_model=List[AlertOut])
async def list_alerts(current_user: dict = Depends(get_superadmin_user)):
    if current_user["role"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT a.*, u.full_name_en as creator_name 
        FROM system_alerts a
        LEFT JOIN users u ON a.created_by = u.id
        ORDER BY a.created_at DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, current_user: dict = Depends(get_superadmin_user)):
    if current_user["role"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM system_alerts WHERE id = %s", (alert_id,))
        conn.commit()
        return {"message": "Alert deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
