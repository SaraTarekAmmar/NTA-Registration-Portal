from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from core.database import get_db_connection
from core.auth import require_editor as get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

TARGETING_MATRIX = {
    "trainee": ["coordinator", "trainer"],
    "trainer": ["coordinator", "trainee"],
    "coordinator": ["trainee", "trainer", "editor"],
    "editor": ["coordinator", "admin", "trainer"],
    "admin": ["coordinator", "editor", "trainer", "superadmin"],
    "superadmin": ["trainee", "trainer", "coordinator", "editor", "admin"],
}

ROLE_LABELS = {
    "trainee": "متدرب",
    "trainer": "مدرب",
    "coordinator": "منسق",
    "editor": "محرر",
    "admin": "مسؤول النظام",
    "superadmin": "مدير النظام المتميز",
}


class TicketCreate(BaseModel):
    subject: str
    receiver_id: int
    receiver_role: str
    initial_message: str


class MessageCreate(BaseModel):
    message_text: str


@router.get("/allowed-roles")
def get_allowed_roles(current_user: dict = Depends(get_current_user)):
    allowed = TARGETING_MATRIX.get(current_user.get("role"), [])
    return [{"role": r, "label": ROLE_LABELS.get(r, r)} for r in allowed]


@router.get("/lookup-users")
def lookup_users(query: Optional[str] = None, target_role: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    allowed = TARGETING_MATRIX.get(current_user.get("role"), [])
    if target_role:
        if target_role not in allowed:
            return []
        allowed = [target_role]
    if not allowed:
        return []

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        placeholders = ",".join(["%s"] * len(allowed))
        sql = f"SELECT id, full_name_ar, full_name_en, role, email FROM users WHERE role IN ({placeholders})"
        params = list(allowed)
        if query:
            sql += " AND (full_name_ar LIKE %s OR email LIKE %s)"
            params += [f"%{query}%", f"%{query}%"]
        sql += " LIMIT 20"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


@router.post("/")
def create_ticket(ticket: TicketCreate, current_user: dict = Depends(get_current_user)):
    my_role = current_user.get("role")
    my_id = current_user.get("id")
    if ticket.receiver_role not in TARGETING_MATRIX.get(my_role, []):
        raise HTTPException(status_code=403, detail="Not authorized to target this role.")

    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id = %s AND role = %s", (ticket.receiver_id, ticket.receiver_role))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target user not found.")
        cursor.execute(
            "INSERT INTO support_tickets (subject, status, initiator_id, initiator_role, receiver_id, receiver_role) VALUES (%s, 'Open', %s, %s, %s, %s)",
            (ticket.subject, my_id, my_role, ticket.receiver_id, ticket.receiver_role),
        )
        ticket_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO support_ticket_messages (ticket_id, sender_id, message_text) VALUES (%s, %s, %s)",
            (ticket_id, my_id, ticket.initial_message),
        )
        db.commit()
        return {"ticket_id": ticket_id, "message": "Ticket created successfully."}
    finally:
        cursor.close()
        db.close()


@router.get("/")
def get_my_tickets(current_user: dict = Depends(get_current_user)):
    my_id = current_user.get("id")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT t.id, t.subject, t.status, t.created_at, t.updated_at,
                   u1.full_name_ar AS initiator_name, t.initiator_role,
                   u2.full_name_ar AS receiver_name, t.receiver_role
            FROM support_tickets t
            JOIN users u1 ON t.initiator_id = u1.id
            JOIN users u2 ON t.receiver_id = u2.id
            WHERE t.initiator_id = %s OR t.receiver_id = %s
            ORDER BY t.updated_at DESC
            """,
            (my_id, my_id),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


@router.get("/{ticket_id}")
def get_ticket_thread(ticket_id: int, current_user: dict = Depends(get_current_user)):
    my_id = current_user.get("id")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT initiator_id, receiver_id FROM support_tickets WHERE id = %s", (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found.")
        if my_id not in (ticket["initiator_id"], ticket["receiver_id"]):
            raise HTTPException(status_code=403, detail="Access denied.")
        cursor.execute(
            """
            SELECT m.id, m.message_text, m.created_at, u.full_name_ar AS sender_name, u.role AS sender_role
            FROM support_ticket_messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.ticket_id = %s
            ORDER BY m.created_at ASC
            """,
            (ticket_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


@router.post("/{ticket_id}/messages")
def reply_ticket(ticket_id: int, message: MessageCreate, current_user: dict = Depends(get_current_user)):
    my_id = current_user.get("id")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT initiator_id, receiver_id, status FROM support_tickets WHERE id = %s", (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found.")
        if my_id not in (ticket["initiator_id"], ticket["receiver_id"]):
            raise HTTPException(status_code=403, detail="Access denied.")
        if ticket["status"] == "Closed":
            raise HTTPException(status_code=400, detail="Cannot reply to a closed ticket.")
        cursor.execute(
            "INSERT INTO support_ticket_messages (ticket_id, sender_id, message_text) VALUES (%s, %s, %s)",
            (ticket_id, my_id, message.message_text),
        )
        cursor.execute("UPDATE support_tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = %s", (ticket_id,))
        db.commit()
        return {"message": "Reply sent successfully."}
    finally:
        cursor.close()
        db.close()
