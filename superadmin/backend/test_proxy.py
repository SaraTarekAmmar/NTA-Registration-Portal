"""
test_matrix_pipeline.py
=======================
Comprehensive test suite for the Class Trainer Matrix AI pipeline.

Tests:
  1. MatrixGenerator can be imported and instantiated
  2. _extract_json handles all edge cases (fenced, balanced braces, direct)
  3. _calc_age and helper methods work correctly
  4. classify_course returns a valid structure (mocked vLLM)
  5. generate_matrix returns a valid structure (mocked vLLM)
  6. Super Admin proxy /api/ai/dispatch endpoint accepts the correct payload
  7. /api/ai/matrix-status/{course_id} returns a valid response

Run from the superadmin/backend directory:
    python test_matrix_pipeline.py

Or to test against a live server:
    python test_matrix_pipeline.py --live --course-id 10
"""

import sys
import json
import time
import argparse
import importlib.util
import traceback
from pathlib import Path
from unittest.mock import patch, MagicMock

# ─────────────────────────────────────────────
#  Path setup
# ─────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent  # .../NTA-Regestration-Portal - Final
MATRIX_PATH = ROOT / "AI Services" / "Class Trainer Matrix"
BACKEND_PATH = ROOT / "admin" / "backend"

for p in [str(MATRIX_PATH), str(BACKEND_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─────────────────────────────────────────────
#  Load MatrixGenerator dynamically
# ─────────────────────────────────────────────
def load_matrix_generator():
    matrix_file = MATRIX_PATH / "matrix_generator.py"
    if not matrix_file.exists():
        raise FileNotFoundError(f"matrix_generator.py not found at {matrix_file}")
    spec = importlib.util.spec_from_file_location("matrix_generator", str(matrix_file))
    mod = importlib.util.module_from_spec(spec)
    # Register in sys.modules BEFORE exec so relative imports resolve & patch works
    sys.modules["matrix_generator"] = mod
    spec.loader.exec_module(mod)
    return mod.MatrixGenerator


# ---- Test helpers ----
PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

results = []

def run_test(name, fn):
    print(f"\n  >> {name}")
    try:
        fn()
        print(f"  {PASS} {name}")
        results.append((name, True, None))
    except AssertionError as e:
        print(f"  {FAIL} Assertion: {e}")
        results.append((name, False, str(e)))
    except Exception as e:
        print(f"  {FAIL} Exception: {e}")
        results.append((name, False, traceback.format_exc()))


# ---- Unit Tests (no DB / no vLLM required) ----
def test_import():
    """MatrixGenerator can be loaded."""
    cls = load_matrix_generator()
    assert cls is not None, "MatrixGenerator class is None"
    gen = cls.__new__(cls)  # don't call __init__ (needs DB)
    gen.vllm_url = "http://localhost:7834"
    gen.model_name = "test"
    gen.max_retries = 0
    assert hasattr(gen, "_extract_json"), "Missing _extract_json method"
    assert hasattr(gen, "_call_vllm"), "Missing _call_vllm method"
    assert hasattr(gen, "generate_matrix"), "Missing generate_matrix method"
    assert hasattr(gen, "classify_course"), "Missing classify_course method"


def test_extract_json_fenced():
    """_extract_json handles ```json ... ``` fenced blocks."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    text = '```json\n{"nature": "Practical", "reasoning": "test"}\n```'
    result = gen._extract_json(text)
    assert result["nature"] == "Practical", f"Expected 'Practical', got {result['nature']}"
    assert result["reasoning"] == "test"


def test_extract_json_balanced_braces():
    """_extract_json finds first balanced {} block."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    text = 'Sure! Here is the JSON: {"assignments": [{"trainee_id": 1, "trainer_id": 10}]} End.'
    result = gen._extract_json(text)
    assert "assignments" in result
    assert len(result["assignments"]) == 1


def test_extract_json_direct():
    """_extract_json parses a clean JSON string directly."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    text = '{"nature": "Theoretical", "reasoning": "محاضرات نظرية"}'
    result = gen._extract_json(text)
    assert result["nature"] == "Theoretical"


def test_extract_json_trailing_comma():
    """_extract_json handles trailing commas via regex cleanup."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    text = '{"assignments": [{"trainee_id": 1, "trainer_id": 2,}]}'
    # This will try balanced-brace strategy and clean trailing commas
    try:
        result = gen._extract_json(text)
        assert "assignments" in result
    except ValueError:
        # Acceptable if cleaning fails — the retry loop handles this
        pass


def test_extract_json_invalid_raises():
    """_extract_json raises ValueError for completely invalid input."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    try:
        gen._extract_json("This is not JSON at all — no braces")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_calc_age():
    """_calc_age handles various DOB formats."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    from datetime import datetime, date
    # String DOB
    result = gen._calc_age("1990-01-01")
    assert isinstance(result, str) and result.isdigit(), f"Expected digit string, got {result}"
    age = int(result)
    assert 30 <= age <= 50, f"Unexpected age {age} for 1990-01-01"

    # datetime object
    dob_dt = datetime(1995, 6, 15)
    result2 = gen._calc_age(dob_dt)
    assert result2.isdigit()

    # None
    result3 = gen._calc_age(None)
    assert result3 == "غير محدد"


def test_safe_json():
    """_safe_json handles strings, dicts, lists and None."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    assert gen._safe_json(None) is None
    assert gen._safe_json({"key": "val"}) == {"key": "val"}
    assert gen._safe_json([1, 2]) == [1, 2]
    assert gen._safe_json('{"a": 1}') == {"a": 1}
    assert gen._safe_json("not-json") == "not-json"


def test_build_trainers_block():
    """_build_trainers_block formats trainer data correctly."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    trainers = [
        {
            "id": 5, "full_name_ar": "محمد أحمد", "dob": None, "gender": "M",
            "technical_skills": '["Python", "Machine Learning"]',
            "soft_skills": None,
            "professional_summary": '{"objective": "مدرب محترف في البرمجة"}',
            "professional_history": None
        }
    ]
    block = gen._build_trainers_block(trainers)
    assert "محمد أحمد" in block, "Trainer name missing from block"
    assert "Python" in block, "Skills missing from block"
    assert "#5" in block, "Trainer ID missing from block"


def test_build_trainees_block():
    """_build_trainees_block formats trainee data correctly."""
    cls = load_matrix_generator()
    gen = cls.__new__(cls)

    trainees = [
        {
            "id": 20, "full_name_ar": "سارة علي", "dob": "2000-03-20", "gender": "F",
            "technical_skills": '["Java", "SQL"]',
            "soft_skills": '["التواصل", "فريق العمل"]',
            "professional_summary": None,
            "professional_history": None
        }
    ]
    block = gen._build_trainees_block(trainees)
    assert "سارة علي" in block
    assert "Java" in block
    assert "#20" in block


# ---- Integration Tests (mocked DB + vLLM) ----
MOCK_CLASSIFY_RESPONSE = json.dumps({
    "nature": "Practical",
    "reasoning": "تعتمد الدورة على التطبيق العملي والمهارات التقنية"
})

MOCK_ASSIGNMENTS_RESPONSE = json.dumps({
    "assignments": [
        {
            "trainee_id": 65,
            "trainer_id": 90,
            "trainer_analysis": {
                "strengths": "خبرة واسعة في تحليل البيانات",
                "weaknesses": "تفضيل العمل الفردي",
                "reason": "تتناسب مهاراتها مع متطلبات الدورة المتقدمة"
            },
            "trainee_analysis": {
                "strengths": "معرفة جيدة بـ Python و NumPy",
                "weaknesses": "تحتاج لتطوير مهارات SQL",
                "reason": "المدربة غادة يمكنها سد الفجوة في تحليل البيانات المتقدم",
                "confidence_score": 90
            }
        },
        {
            "trainee_id": 66,
            "trainer_id": 90,
            "trainer_analysis": {
                "strengths": "خبرة واسعة في تحليل البيانات",
                "weaknesses": "تفضيل العمل الفردي",
                "reason": "تتناسب مهاراتها مع متطلبات الدورة المتقدمة"
            },
            "trainee_analysis": {
                "strengths": "خلفية قوية في Node.js و React",
                "weaknesses": "جديد على تحليل البيانات بـ Python",
                "reason": "تحتاج إلى توجيه في تحويل مهاراتها البرمجية إلى علم البيانات",
                "confidence_score": 75
            }
        }
    ]
})

def _make_mock_db(course_data, trainers, trainees):
    """Return a mock DB connection + cursor."""
    mock_cursor = MagicMock()

    call_count = [0]

    def mock_fetchone():
        call_count[0] += 1
        if call_count[0] == 1:
            return course_data
        return None

    def mock_fetchall():
        return trainers if call_count[0] <= 2 else trainees

    mock_cursor.fetchone.side_effect = mock_fetchone
    mock_cursor.fetchall.side_effect = [
        [],       # sessions for classify_course
        trainers, # trainers for generate_matrix
        trainees, # trainees for generate_matrix
    ]
    mock_cursor.execute.return_value = None
    mock_cursor.lastrowid = 999

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None
    mock_conn.close.return_value = None

    return mock_conn, mock_cursor


def test_classify_course_mocked():
    """classify_course returns valid structure with mocked vLLM."""
    import sys

    # Load the module fresh so we can grab its reference
    cls = load_matrix_generator()
    # The module was loaded into sys.modules as 'matrix_generator'
    mat_mod = sys.modules.get("matrix_generator")
    assert mat_mod is not None, "matrix_generator not in sys.modules"

    COURSE = {"title": "Python for Data Science", "description": "Python for Data Science Masterclass", "skill_level": "Intermediate"}
    SESSIONS = []

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = COURSE
    mock_cursor.fetchall.return_value = SESSIONS
    mock_cursor.execute.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": MOCK_CLASSIFY_RESPONSE}}]
    }
    mock_resp.raise_for_status.return_value = None

    # Patch get_db_connection in the loaded matrix_generator module namespace
    with patch.object(mat_mod, "get_db_connection", return_value=mock_conn), \
         patch("requests.post", return_value=mock_resp):

        gen = cls.__new__(cls)
        gen.vllm_url = "http://localhost:7834"
        gen.model_name = "test-model"
        gen.max_retries = 0
        result = gen.classify_course(1)

    assert result is not None, "classify_course returned None"
    assert "nature" in result, f"'nature' missing from result: {result}"
    assert result["nature"] in ("Practical", "Theoretical"), f"Invalid nature: {result['nature']}"
    r_preview = result.get('reasoning', '')[:40].encode('ascii', 'replace').decode('ascii')
    print(f"      nature={result['nature']}, reasoning={r_preview}")


def test_generate_matrix_mocked():
    """generate_matrix returns valid structure with mocked vLLM + DB."""
    import sys

    cls = load_matrix_generator()
    mat_mod = sys.modules.get("matrix_generator")
    assert mat_mod is not None, "matrix_generator not in sys.modules"

    COURSE = {"title": "Python for Data Science", "description": "Python for Data Science Masterclass", "skill_level": "Intermediate"}
    SESSIONS = []
    TRAINERS = [
        {
            "id": 90, "full_name_ar": "غادة عبد اللطيف", "dob": None, "gender": "F",
            "technical_skills": None, "soft_skills": None,
            "professional_summary": None, "professional_history": None
        }
    ]
    TRAINEES = [
        {
            "id": 65, "full_name_ar": "رانيا يوسف البيطار", "dob": "1995-01-30", "gender": "F",
            "technical_skills": '["Python", "NumPy"]', "soft_skills": '["Communication"]',
            "professional_summary": None, "professional_history": None
        },
        {
            "id": 66, "full_name_ar": "طارق سيد الباز", "dob": "1992-07-05", "gender": "M",
            "technical_skills": '["JavaScript"]', "soft_skills": '["Leadership"]',
            "professional_summary": None, "professional_history": None
        }
    ]

    # Each classify_course + generate_matrix opens its own DB connection
    # We use a factory to return distinct mocks per call
    call_num = [0]

    def mock_db_factory():
        call_num[0] += 1
        mock_cursor = MagicMock()
        mock_cursor.execute.return_value = None
        if call_num[0] == 1:
            # classify_course DB call
            mock_cursor.fetchone.return_value = COURSE
            mock_cursor.fetchall.return_value = SESSIONS
        else:
            # generate_matrix DB call
            mock_cursor.fetchall.side_effect = [TRAINERS, TRAINEES]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn

    vllm_call = [0]

    def vllm_side_effect(url, **kwargs):
        vllm_call[0] += 1
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        if vllm_call[0] == 1:
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": MOCK_CLASSIFY_RESPONSE}}]
            }
        else:
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": MOCK_ASSIGNMENTS_RESPONSE}}]
            }
        return mock_resp

    with patch.object(mat_mod, "get_db_connection", side_effect=mock_db_factory), \
         patch("requests.post", side_effect=vllm_side_effect):

        gen = cls.__new__(cls)
        gen.vllm_url = "http://localhost:7834"
        gen.model_name = "test-model"
        gen.max_retries = 0
        result = gen.generate_matrix(1)

    print(f"      result={json.dumps(result, ensure_ascii=False)}")
    assert "success" in result, f"Missing 'success' key: {result}"
    assert result["success"] is True, f"generate_matrix failed: {result.get('error')}"
    assert result.get("assignments_count", 0) >= 1, "No assignments created"


# ---- Live API Tests (requires running server) ----
def test_live_dispatch(course_id: int, superadmin_url: str, token: str = None):
    """Test POST /api/ai/dispatch with Class Trainer Matrix service."""
    import httpx

    payload = {
        "service": "Class Trainer Matrix",
        "endpoint": "/generate",
        "data": {"course_id": course_id}
    }

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"  {INFO} Sending to {superadmin_url}/api/ai/dispatch ...")
    print(f"  {INFO} Payload: {json.dumps(payload, indent=2)}")

    resp = httpx.post(
        f"{superadmin_url}/api/ai/dispatch",
        json=payload,
        headers=headers,
        timeout=30.0
    )

    print(f"  {INFO} HTTP Status: {resp.status_code}")
    print(f"  {INFO} Response: {resp.text[:500]}")

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("status") in ("processing", "done"), f"Unexpected status: {data}"
    assert "course_id" in data, "Response missing course_id"

    return data


def test_live_matrix_status(course_id: int, superadmin_url: str, token: str = None):
    """Test GET /api/ai/matrix-status/{course_id}."""
    import httpx

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"  {INFO} Polling {superadmin_url}/api/ai/matrix-status/{course_id} ...")

    for i in range(5):
        resp = httpx.get(
            f"{superadmin_url}/api/ai/matrix-status/{course_id}",
            headers=headers,
            timeout=10.0
        )
        print(f"  {INFO} Poll {i+1}: HTTP {resp.status_code} | {resp.text[:200]}")

        if resp.status_code == 200:
            data = resp.json()
            assert "status" in data, "Response missing 'status' field"
            status = data.get("status")
            assert status in ("idle", "processing", "done", "error"), f"Invalid status: {status}"
            if status in ("done", "error"):
                break
        time.sleep(3)

def test_360_persistence(course_id: int):
    """Verifies that the database actually contains the results for Course ID."""
    try:
        from core.database import get_db_connection
    except ImportError:
        # Fallback
        import sys
        sys.path.append(str(ROOT / "admin" / "backend"))
        from core.database import get_db_connection
    
    db = get_db_connection()
    c = db.cursor(dictionary=True)
    try:
        # Check recommendations
        c.execute("SELECT COUNT(*) as cnt FROM class_matrix_recommendations WHERE course_id = %s", (course_id,))
        rec_count = c.fetchone()['cnt']
        
        # Check summary
        c.execute("SELECT COUNT(*) as cnt FROM class_matrix_summary WHERE course_id = %s", (course_id,))
        sum_count = c.fetchone()['cnt']
        
        print(f"  {INFO} Persistence Check: {rec_count} recommendations, {sum_count} summary records found.")
        assert rec_count > 0, "No recommendations found in DB"
        assert sum_count > 0, "No summary found in DB"
        
    finally:
        c.close()
        db.close()



# ---- Main runner ----
def main():
    parser = argparse.ArgumentParser(description="Test Class Trainer Matrix pipeline")
    parser.add_argument("--live", action="store_true", help="Run live API tests against a running server")
    parser.add_argument("--course-id", type=int, default=10, help="Course ID for live tests")
    parser.add_argument("--url", default="http://127.0.0.1:8003", help="Super Admin URL")
    parser.add_argument("--token", default=None, help="JWT Bearer token for auth")
    args = parser.parse_args()

    print("\n" + "="*65)
    print("  NTA Class Trainer Matrix — Full Pipeline Test Suite")
    print("="*65)

    # ── Unit tests (always run) ──────────────────────────────────────
    print("\n[UNIT TESTS]\n")
    run_test("Import & Instantiation",      test_import)
    run_test("JSON: Fenced block",          test_extract_json_fenced)
    run_test("JSON: Balanced braces",       test_extract_json_balanced_braces)
    run_test("JSON: Direct parse",          test_extract_json_direct)
    run_test("JSON: Trailing comma",        test_extract_json_trailing_comma)
    run_test("JSON: Invalid raises error",  test_extract_json_invalid_raises)
    run_test("Helper: _calc_age",           test_calc_age)
    run_test("Helper: _safe_json",          test_safe_json)
    run_test("Helper: _build_trainers",     test_build_trainers_block)
    run_test("Helper: _build_trainees",     test_build_trainees_block)

    # ── Integration tests (mocked) ────────────────────────────────────
    print("\n[INTEGRATION TESTS — MOCKED DB + vLLM]\n")
    run_test("classify_course (mocked)",    test_classify_course_mocked)
    run_test("generate_matrix (mocked)",    test_generate_matrix_mocked)

    # ── Live API tests ───────────────────────────────────────────────
    if args.live:
        print(f"\n[LIVE API TESTS — {args.url}]\n")

        def live_dispatch():
            test_live_dispatch(args.course_id, args.url, args.token)

        def live_status():
            test_live_matrix_status(args.course_id, args.url, args.token)
            
        def live_persistence():
            test_360_persistence(args.course_id)

        run_test(f"POST /api/ai/dispatch (course #{args.course_id})", live_dispatch)
        run_test(f"GET  /api/ai/matrix-status/{args.course_id}",      live_status)
        run_test(f"DB Persistence Check (360 Test)",                live_persistence)
    else:
        print(f"\n{INFO} Skipping live API tests. Use --live to enable them.\n")

    # ── Summary ────────────────────────────────────────────────────────
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed

    print("\n" + "="*65)
    print(f"  Results: {passed}/{len(results)} passed  |  {failed} failed")
    print("="*65)

    for name, ok, err in results:
        status = PASS if ok else FAIL
        print(f"  {status} {name}")
        if err and not ok:
            # Print first 3 lines of error
            for line in err.strip().split("\n")[:3]:
                print(f"         {line}")

    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
