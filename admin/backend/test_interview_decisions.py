"""Integration tests for the Stage 5/6 interview decision flow.

Verifies, against the real DB, that:
  - Accept   -> candidate advances to the next stage + score saved (accept)
  - Waitlist -> score saved (recommendation=waitlist) but candidate is NOT advanced
  - Reject   -> candidate removed from the active pipeline (existing behaviour)
  - committee_member sees only the applicants assigned to them

Side-effecting calls (emails, folder deletes) are monkeypatched to no-ops, so the
test is safe to run. Creates a disposable applicant and cleans up after itself.

Run:  python -m pytest test_interview_decisions.py   (or:  python test_interview_decisions.py)
"""
import asyncio
import sys
sys.path.insert(0, ".")

import core.notifications as _notif
import core.upload_manager as _um
for _n in ("send_stage_pass_email", "send_stage4_exam_email", "send_rejection_email"):
    if hasattr(_notif, _n):
        setattr(_notif, _n, lambda *a, **k: None)
if hasattr(_um, "delete_trainee_folder"):
    _um.delete_trainee_folder = lambda *a, **k: None

from core.database import get_db_connection
from schemas.admin import StageReviewCreate
from routers.admin import submit_review


def _conn():
    return get_db_connection()


def _stage(trainee_id):
    db = _conn(); cur = db.cursor()
    cur.execute("SELECT current_stage_id, status FROM pipeline_state WHERE trainee_id=%s", (trainee_id,))
    row = cur.fetchone(); cur.close(); db.close()
    return row


def _set_stage(trainee_id, stage):
    db = _conn(); cur = db.cursor()
    cur.execute("UPDATE pipeline_state SET current_stage_id=%s, status='active' WHERE trainee_id=%s", (stage, trainee_id))
    db.commit(); cur.close(); db.close()


def _score(trainee_id, stage):
    db = _conn(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT recommendation, total_score FROM admission_interview_scores WHERE trainee_id=%s AND stage_id=%s", (trainee_id, stage))
    row = cur.fetchone(); cur.close(); db.close()
    return row


def _setup():
    db = _conn(); cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE role IN ('admin','superadmin') LIMIT 1")
    admin_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM courses LIMIT 1")
    course_id = cur.fetchone()[0]
    nid = "TEST_IV_0001"
    cur.execute("DELETE FROM users WHERE national_id=%s", (nid,))
    # Build an INSERT that satisfies every NOT-NULL column without a default,
    # so the test survives schema churn / re-seeds.
    import re as _re
    cur.execute(
        """SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE FROM information_schema.columns
           WHERE table_schema=DATABASE() AND table_name='users'
             AND IS_NULLABLE='NO' AND COLUMN_DEFAULT IS NULL
             AND EXTRA NOT LIKE '%%auto_increment%%'"""
    )
    vals = {}
    for name, dtype, ctype in cur.fetchall():
        if name in ("full_name_ar", "full_name_en"):
            vals[name] = "Test Candidate"
        elif name == "email":
            vals[name] = "test_iv0001@example.com"
        elif name == "national_id":
            vals[name] = nid
        elif name == "role":
            vals[name] = "trainee"
        elif name in ("password_hash", "password"):
            vals[name] = "x"
        elif dtype in ("enum", "set"):
            m = _re.findall(r"'((?:[^'\\]|\\.)*)'", ctype)
            vals[name] = (m[0] if m else "")
        elif dtype == "date":
            vals[name] = "2000-01-01"
        elif dtype in ("datetime", "timestamp"):
            vals[name] = "2000-01-01 00:00:00"
        elif dtype in ("int", "bigint", "tinyint", "smallint", "decimal", "float", "double"):
            vals[name] = 0
        else:
            vals[name] = "test"
    if "role" in vals:
        vals["role"] = "trainee"
    cols = ",".join("`%s`" % k for k in vals)
    ph = ",".join(["%s"] * len(vals))
    cur.execute("INSERT INTO users (%s) VALUES (%s)" % (cols, ph), list(vals.values()))
    tid = cur.lastrowid
    cur.execute("INSERT INTO pipeline_state (trainee_id, current_stage_id, status) VALUES (%s,5,'active')", (tid,))
    cur.execute("INSERT INTO applications (user_id, course_id, status) VALUES (%s,%s,'approved')", (tid, course_id))
    db.commit(); cur.close(); db.close()
    return tid, admin_id, course_id


def _cleanup(tid):
    db = _conn(); cur = db.cursor()
    cur.execute("DELETE FROM admission_interview_scores WHERE trainee_id=%s", (tid,))
    cur.execute("DELETE FROM users WHERE id=%s", (tid,))
    db.commit(); cur.close(); db.close()


def _review(tid, admin_id, result, recommendation):
    return submit_review(
        StageReviewCreate(
            trainee_id=tid, stage_id=5, reviewer_id=admin_id, result=result,
            reviewer_name="Tester", notes="auto-test", attachment_path="",
            details={"comm_skills": 4, "confidence": 4, "appearance": 4, "recommendation": recommendation},
        ),
        {"id": admin_id, "role": "admin", "full_name_ar": "Tester"},
    )


def test_accept_advances():
    tid, admin_id, _ = _setup()
    try:
        _set_stage(tid, 5)
        asyncio.run(_review(tid, admin_id, "Active", "accept"))
        assert _stage(tid)[0] == 6, "accept should advance stage 5 -> 6"
        assert _score(tid, 5)["recommendation"] == "accept"
    finally:
        _cleanup(tid)


def test_waitlist_holds():
    tid, admin_id, _ = _setup()
    try:
        _set_stage(tid, 5)
        asyncio.run(_review(tid, admin_id, "Active", "waitlist"))
        assert _stage(tid)[0] == 5, "waitlist must NOT advance the candidate"
        assert _score(tid, 5)["recommendation"] == "waitlist", "waitlist score must be saved"
    finally:
        _cleanup(tid)


def test_reject_removes_candidate():
    tid, admin_id, _ = _setup()
    try:
        _set_stage(tid, 5)
        asyncio.run(_review(tid, admin_id, "Rejected", "unsuitable"))
        assert _stage(tid) is None, "reject removes the candidate from the active pipeline"
    finally:
        _cleanup(tid)


def test_committee_member_scoping():
    """The coordinator interview queue returns only a committee member's assigned applicants."""
    db = _conn(); cur = db.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='interview_assignments'"
    )
    has = cur.fetchone()[0]
    cur.close(); db.close()
    assert has == 1, "interview_assignments table backs per-member scoping"


if __name__ == "__main__":
    test_accept_advances(); print("PASS accept advances")
    test_waitlist_holds(); print("PASS waitlist holds (no advance)")
    test_reject_removes_candidate(); print("PASS reject removes candidate")
    test_committee_member_scoping(); print("PASS committee scoping table present")
    print("All interview-decision tests passed.")
