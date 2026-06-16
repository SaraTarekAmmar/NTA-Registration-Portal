import json
from fastapi import APIRouter, Depends, Query, UploadFile, File
from typing import Optional, List
from core.database import get_db_connection
from core.auth import get_staff_user
from core.quiz_import import ingest_records, flatten_payload, PASS_THRESHOLD

router = APIRouter(prefix="/api/admin/quiz-results", tags=["Quiz Results"])


@router.get("")
async def get_all_quiz_results(course_id: Optional[int] = Query(None), staff: dict = Depends(get_staff_user)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT
                qa.id AS attempt_id,
                qa.score AS raw_score,
                qa.created_at,
                qa.details_json,
                u.full_name_ar AS trainee_name,
                u.national_id,
                u.email,
                c.title AS course_name
            FROM quiz_attempts qa
            JOIN users u ON qa.user_id = u.id
            JOIN courses c ON qa.course_id = c.id
            WHERE 1=1
        """
        params = []
        if course_id:
            query += " AND qa.course_id = %s"
            params.append(course_id)
        query += " ORDER BY qa.created_at DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        results = []
        for r in rows:
            d = r.get("details_json") or {}
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except Exception:
                    d = {}
            raw = float(r["raw_score"]) if r["raw_score"] is not None else None
            max_grade = d.get("max_grade")
            pct = d.get("percentage")
            if pct is None and raw is not None and max_grade:
                pct = (raw / float(max_grade)) * 100
            pct = round(float(pct), 2) if pct is not None else 0
            results.append({
                "attempt_id": r["attempt_id"],
                "raw_score": raw,
                "created_at": r["created_at"],
                "trainee_name": r["trainee_name"],
                "national_id": r["national_id"],
                "email": r["email"],
                "course_name": r["course_name"],
                "quiz_name": d.get("exam_name") or "اختبار الدورة",
                "max_grade": max_grade or 100,
                "percentage": pct,
                "status": "pass" if pct >= PASS_THRESHOLD else "fail",
                "correct": d.get("correct"),
                "wrong": d.get("wrong"),
            })
        return results
    finally:
        cursor.close()
        db.close()


@router.post("/import")
async def import_quiz_results(files: List[UploadFile] = File(...), staff: dict = Depends(get_staff_user)):
    """Upload one or more result JSON files. Auto-creates trainees by national ID
    and attaches attempts to the batch course. Idempotent."""
    records = []
    errors = 0
    for f in files:
        try:
            records.extend(flatten_payload(json.loads(await f.read())))
        except Exception:
            errors += 1
    db = get_db_connection()
    try:
        summary = ingest_records(db, records)
    finally:
        db.close()
    summary["files"] = len(files)
    summary["unreadable_files"] = errors
    return summary
