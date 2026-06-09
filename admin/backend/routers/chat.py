from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from core.database import get_db_connection
from core.auth import get_current_user
from core.chat_engine import chat_engine
from datetime import datetime
import json
import time

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    reply: str
    id: int

class HistoryItem(BaseModel):
    id: int
    question: str
    reply: str
    created_at: str

CHAT_RATE_LIMIT = {}

@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(req: Request, request: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    now = time.time()
    today = time.strftime("%Y-%m-%d")

    if user_id in CHAT_RATE_LIMIT:
        record = CHAT_RATE_LIMIT[user_id]
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
        CHAT_RATE_LIMIT[user_id] = {"day": today, "daily": 1, "minute_hits": [now]}

    role = current_user["role"]
    
    # 1. Get response from LLM Engine
    reply = await chat_engine.get_reply(role, request.question)
    
    # 2. Save to Database
    db = get_db_connection()
    cursor = db.cursor(buffered=True)
    try:
        query = "INSERT INTO chat_history (user_id, role, question, reply) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, role, request.question, reply))
        db.commit()
        chat_id = cursor.lastrowid
        return {"reply": reply, "id": chat_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@router.get("/history", response_model=List[HistoryItem])
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    try:
        query = "SELECT id, question, reply, created_at FROM chat_history WHERE user_id = %s ORDER BY created_at ASC"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        # Format date for JSON
        for item in results:
            if isinstance(item["created_at"], datetime):
                item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            else:
                item["created_at"] = str(item["created_at"])
            
        return results
    finally:
        cursor.close()
        db.close()
