"""
One-off importer for the external student quiz-result JSON exports.

Usage:
    python deploy/import_quiz_results.py "C:\\path\\to\\student_results"

Defaults to the known "المكاتب الفنية\\student_results" folder under Downloads.
Idempotent — safe to run repeatedly (already-imported attempts are skipped).
Auto-creates a trainee user per national_id and one batch course.
"""
import sys
import os
import json
import glob
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "admin" / "backend"))
from core.database import get_db_connection          # noqa: E402
from core.quiz_import import ingest_records, flatten_payload  # noqa: E402

DEFAULT_FOLDER = os.path.join(
    os.path.expanduser("~"), "Downloads", "المكاتب الفنية", "student_results"
)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FOLDER
    if not os.path.isdir(folder):
        print(f"[ERROR] Folder not found: {folder}")
        sys.exit(1)

    files = glob.glob(os.path.join(folder, "*.json"))
    print(f"[IMPORT] {len(files)} JSON file(s) in {folder}")

    records = []
    bad = 0
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                records.extend(flatten_payload(json.load(fh)))
        except Exception as exc:
            bad += 1
            print(f"  [skip] {os.path.basename(f)} — {exc}")

    print(f"[IMPORT] {len(records)} attempt record(s) parsed ({bad} unreadable file(s))")

    db = get_db_connection()
    try:
        summary = ingest_records(db, records)
    finally:
        db.close()

    print("[DONE] inserted=%(inserted)d skipped=%(skipped)d "
          "new_trainees=%(created_users)d course_id=%(course_id)d" % summary)


if __name__ == "__main__":
    main()
