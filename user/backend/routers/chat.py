from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from core.database import get_db_connection
from core.auth import get_current_user, get_optional_user
from core.chat_engine import chat_engine
import json
import time

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    reply: str
    # id can be negative or 0 for guest messages to indicate they aren't stored
    id: int

class HistoryItem(BaseModel):
    id: int
    question: str
    reply: str
    created_at: str

CHAT_RATE_LIMIT = {}

@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(req: Request, request: ChatRequest, current_user: Optional[dict] = Depends(get_optional_user)):
    # Identify user by ID if logged in, otherwise by IP
    client_ip = req.client.host if req.client else "unknown"
    rate_limit_key = current_user["id"] if current_user else f"guest_{client_ip}"
    
    now = time.time()
    today = time.strftime("%Y-%m-%d")

    if rate_limit_key in CHAT_RATE_LIMIT:
        record = CHAT_RATE_LIMIT[rate_limit_key]
        if record["day"] != today:
            record["daily"] = 0
            record["day"] = today
        
        if record["daily"] >= 50:
            raise HTTPException(status_code=429, detail="لقد تجاوزت الحد اليومي للأسئلة (50).")
            
        timestamps = record.get("minute_hits", [])
        timestamps = [t for t in timestamps if now - t < 60]
        if len(timestamps) >= 5:
            raise HTTPException(status_code=429, detail="يرجى الانتظار، لا يمكنك طرح أكثر من 5 أسئلة في الدقيقة.")
            
        timestamps.append(now)
        record["minute_hits"] = timestamps
        record["daily"] += 1
    else:
        CHAT_RATE_LIMIT[rate_limit_key] = {"day": today, "daily": 1, "minute_hits": [now]}
    
    # role is 'trainee_authenticated' if logged in, 'trainee_guest' otherwise
    role = "trainee_authenticated" if current_user else "trainee_guest"
    
    # 0. Fetch history context (only if authenticated)
    history = []
    if current_user:
        user_id = current_user["id"]
        db = get_db_connection()
        cursor = db.cursor(dictionary=True, buffered=True)
        try:
            hist_query = "SELECT question, reply FROM chat_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 5"
            cursor.execute(hist_query, (user_id,))
            history = cursor.fetchall()
            history.reverse()
        except Exception as e:
            print(f"History Fetch Error: {e}")
        finally:
            cursor.close()
            db.close()

    # 1. Get response from LLM Engine
    reply = await chat_engine.get_reply(role, request.question, history)
    
    # 2. Save to Database (only if authenticated)
    if current_user:
        user_id = current_user["id"]
        db = get_db_connection()
        cursor = db.cursor(buffered=True)
        try:
            query = "INSERT INTO chat_history (user_id, role, question, reply) VALUES (%s, %s, %s, %s)"
            # Use basic 'trainee' for DB role to match ENUM
            db_role = current_user["role"] 
            cursor.execute(query, (user_id, db_role, request.question, reply))
            db.commit()
            chat_id = cursor.lastrowid
            return {"reply": reply, "id": chat_id}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()
            db.close()
    else:
        # Guest response: chat_id 0
        return {"reply": reply, "id": 0}

@router.get("/history", response_model=List[HistoryItem])
async def get_chat_history(current_user: Optional[dict] = Depends(get_optional_user)):
    if not current_user:
        return []
        
    user_id = current_user["id"]
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        query = "SELECT id, question, reply, created_at FROM chat_history WHERE user_id = %s ORDER BY created_at ASC"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        for item in results:
            item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            
        return results
    finally:
        cursor.close()
        db.close()
