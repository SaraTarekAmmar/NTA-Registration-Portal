import os
import json
import re
import requests
import sys
import time
from pathlib import Path
from datetime import datetime

# Resolve project root for imports
current_dir = Path(__file__).resolve().parent
ROOT = current_dir.parent.parent
sys.path.append(str(ROOT / "admin" / "backend"))

try:
    from core.database import get_db_connection
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(ROOT))
    from admin.backend.core.database import get_db_connection


class MatrixGenerator:
    def __init__(self):
        self.vllm_url = "http://localhost:7834"
        self.model_name = "google/gemma-4-31B-it"
        self.max_retries = 2

    # ------------------------------------------------------------------ #
    #  LLM Call with retry
    # ------------------------------------------------------------------ #
    def _call_vllm(self, system_prompt: str, user_prompt: str, attempt: int = 0) -> str:
        """Call the vLLM endpoint. Returns the raw text content."""
        try:
            response = requests.post(
                f"{self.vllm_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.05,   # Very low for deterministic JSON
                    "top_p": 0.9,
                    "repetition_penalty": 1.1
                },
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
            raise ValueError(f"Unexpected vLLM response structure: {json.dumps(data)[:200]}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"vLLM unreachable at {self.vllm_url}: {str(e)}")

    # ------------------------------------------------------------------ #
    #  JSON extraction — multiple strategies
    # ------------------------------------------------------------------ #
    def _extract_json(self, text: str) -> dict:
        """
        Robustly extract a JSON object from an LLM response.
        Tries multiple strategies in order:
          1. ```json ... ``` fenced block
          2. First {...} balanced block
          3. Direct parse
        Raises ValueError if all strategies fail.
        """
        # Strategy 1: fenced code block
        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.DOTALL)
        if fence_match:
            candidate = fence_match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass  # Fall through

        # Strategy 2: find first balanced { … }
        start = text.find("{")
        if start != -1:
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            # Try to clean trailing commas / JS-style comments
                            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
                            cleaned = re.sub(r"//[^\n]*", "", cleaned)
                            try:
                                return json.loads(cleaned)
                            except json.JSONDecodeError:
                                break  # Give up on this strategy

        # Strategy 3: direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            raise ValueError(
                f"Could not extract valid JSON from LLM response. "
                f"First 300 chars: {text[:300]}"
            )

    # ------------------------------------------------------------------ #
    #  Step 1 — Classify course
    # ------------------------------------------------------------------ #
    def classify_course(self, course_id: int) -> dict | None:
        """Classify the course as Practical or Theoretical and persist the result."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT title, description, skill_level FROM courses WHERE id = %s",
                (course_id,)
            )
            course = cursor.fetchone()
            if not course:
                return None

            cursor.execute(
                "SELECT topic, materials FROM course_sessions WHERE course_id = %s",
                (course_id,)
            )
            sessions = cursor.fetchall()

            session_lines = "\n".join(
                f"  - موضوع الجلسة: {s['topic']}" for s in sessions
            ) if sessions else "  - لا توجد جلسات محددة"

            # ---- Robust system prompt ----
            system = (
                "أنت خبير تعليمي متخصص في أكاديمية NTA. مهمتك تصنيف الدورات التدريبية.\n"
                "يجب أن تُخرج JSON صحيحاً فقط — لا نص إضافي، لا شرح قبل أو بعد JSON.\n"
                "التنسيق المطلوب بالضبط:\n"
                '{"nature": "Practical" | "Theoretical", "reasoning": "جملة واحدة بالعربية"}'
            )

            user = f"""صنّف هذه الدورة:

الاسم: {course['title']}
الوصف: {course['description'] or 'غير متوفر'}
المستوى: {course['skill_level'] or 'غير محدد'}
الجلسات:
{session_lines}

القاعدة:
- "Practical": دورة تعتمد على التطبيق العملي، الورش، المهارات اليدوية أو التقنية.
- "Theoretical": دورة تعتمد على المحاضرات، المفاهيم النظرية، والمعرفة العامة.

أخرج JSON فقط بدون أي نص آخر:
{{"nature": "Practical أو Theoretical", "reasoning": "سبب التصنيف بالعربية"}}"""

            last_error = None
            for attempt in range(self.max_retries + 1):
                try:
                    raw = self._call_vllm(system, user, attempt)
                    analysis = self._extract_json(raw)

                    # Validate required fields
                    if "nature" not in analysis:
                        raise ValueError("Missing 'nature' field in response")
                    if analysis["nature"] not in ("Practical", "Theoretical"):
                        # Try to normalise
                        n = analysis["nature"].strip().capitalize()
                        if n not in ("Practical", "Theoretical"):
                            raise ValueError(f"Invalid nature value: {analysis['nature']}")
                        analysis["nature"] = n

                    # Persist
                    cursor.execute(
                        """
                        INSERT INTO course_ai_analysis (course_id, nature, reasoning)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            nature = VALUES(nature),
                            reasoning = VALUES(reasoning)
                        """,
                        (course_id, analysis["nature"], analysis.get("reasoning", ""))
                    )
                    db.commit()
                    return analysis

                except Exception as e:
                    last_error = e
                    print(f"[MatrixGenerator] classify_course attempt {attempt + 1} failed: {e}")

            raise RuntimeError(
                f"classify_course failed after {self.max_retries + 1} attempts. "
                f"Last error: {last_error}"
            )

        finally:
            cursor.close()
            db.close()

    # ------------------------------------------------------------------ #
    #  Step 2 — Generate trainer-trainee matrix
    # ------------------------------------------------------------------ #
    def generate_matrix(self, course_id: int) -> dict:
        """
        Full pipeline:
          1. Classify course
          2. Fetch trainers & trainees from DB
          3. Ask LLM to generate assignments
          4. Persist results
        """
        # -- Step 1: classify
        try:
            nature_data = self.classify_course(course_id)
        except Exception as e:
            return {"success": False, "error": f"Course classification failed: {str(e)}"}

        if not nature_data:
            return {"success": False, "error": f"Course #{course_id} not found in database."}

        nature = nature_data["nature"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            # -- Fetch Trainers (joining trainer_profiles instead of trainee_profiles)
            cursor.execute(
                """
                SELECT u.id, u.full_name_ar, u.dob, u.gender,
                       tp.professional_summary_text
                FROM users u
                JOIN course_trainers ct ON u.national_id = ct.trainer_national_id
                LEFT JOIN trainer_profiles tp ON u.id = tp.user_id
                WHERE ct.course_id = %s
                """,
                (course_id,)
            )
            trainers = cursor.fetchall()
            if not trainers:
                return {"success": False, "error": "لا يوجد مدربون مسجلون في هذه الدورة."}

            # Proactively enrich trainers with normalized skills & professional summary
            for t in trainers:
                cursor.execute(
                    "SELECT skill_name FROM trainer_skills WHERE trainer_id = %s AND category_id = 1",
                    (t["id"],)
                )
                t["technical_skills"] = [row["skill_name"] for row in cursor.fetchall()]
                
                cursor.execute(
                    "SELECT skill_name FROM trainer_skills WHERE trainer_id = %s AND category_id = 3",
                    (t["id"],)
                )
                t["soft_skills"] = [row["skill_name"] for row in cursor.fetchall()]
                
                t["professional_summary"] = t["professional_summary_text"] or "غير متوفر"

            # -- Fetch Trainees (approved applications)
            cursor.execute(
                """
                SELECT u.id, u.full_name_ar, u.dob, u.gender,
                       tp.professional_summary_text
                FROM users u
                JOIN applications a ON u.id = a.user_id
                LEFT JOIN trainee_profiles tp ON u.id = tp.user_id
                WHERE a.course_id = %s AND a.status = 'approved'
                """,
                (course_id,)
            )
            trainees = cursor.fetchall()
            if not trainees:
                return {"success": False, "error": "لا يوجد متدربون مقبولون في هذه الدورة."}

            # Proactively enrich trainees with normalized skills & professional summary
            for t in trainees:
                cursor.execute(
                    "SELECT skill_name FROM trainee_skills WHERE trainee_id = %s AND category_id = 1",
                    (t["id"],)
                )
                t["technical_skills"] = [row["skill_name"] for row in cursor.fetchall()]
                
                cursor.execute(
                    "SELECT skill_name FROM trainee_skills WHERE trainee_id = %s AND category_id = 3",
                    (t["id"],)
                )
                t["soft_skills"] = [row["skill_name"] for row in cursor.fetchall()]
                
                t["professional_summary"] = t["professional_summary_text"] or "غير متوفر"

            # -- Build prompt sections
            trainers_block = self._build_trainers_block(trainers)
            trainees_block = self._build_trainees_block(trainees)

            system = (
                "أنت نظام ذكاء اصطناعي متخصص في مطابقة المتدربين مع المدربين لأكاديمية NTA.\n"
                "يجب أن تُخرج JSON صحيحاً فقط — لا نص قبل JSON أو بعده.\n"
                "كل حقل نصي يجب أن يكون باللغة العربية.\n"
                "لا تُكرر نفس المتدرب مرتين في القائمة.\n"
                "يجب أن يحتوي JSON على مفتاح 'assignments' وهو قائمة."
            )

            nature_rule = (
                "- إذا كانت الدورة عملية (Practical): وزّع المتدربين بالتساوي على المدربين بناءً على المهارات التقنية."
                if nature == "Practical"
                else
                "- إذا كانت الدورة نظرية (Theoretical): طابق المدربين الذين يتمتعون بأسلوب تفاعلي وجذاب مع المتدربين الأقل خبرة أو الأكبر سناً."
            )

            user = f"""قم بتوزيع {len(trainees)} متدرباً على {len(trainers)} مدرب لدورة من نوع '{nature}'.

قواعد التوزيع:
{nature_rule}
- طابق نقاط قوة المدرب مع ثغرات المتدرب المعرفية.
- لا تُكرر أي متدرب في أكثر من سجل.
- يجب أن يظهر كل متدرب مرة واحدة بالضبط.

المدربون المتاحون:
{trainers_block}

المتدربون المراد توزيعهم:
{trainees_block}

أخرج JSON فقط بالتنسيق التالي (لا تضف أي نص خارج JSON):
{{
  "assignments": [
    {{
      "trainee_id": <رقم صحيح>,
      "trainer_id": <رقم صحيح>,
      "trainer_analysis": {{
        "strengths": "<نقاط القوة بالعربية>",
        "weaknesses": "<نقاط الضعف بالعربية>",
        "reason": "<سبب ملاءمة المدرب لهذه الدورة بالعربية>"
      }},
      "trainee_analysis": {{
        "strengths": "<نقاط القوة بالعربية>",
        "weaknesses": "<نقاط الضعف بالعربية>",
        "reason": "<سبب ملاءمة هذا المدرب للمتدرب بالعربية>",
        "confidence_score": <رقم من 0 إلى 100>
      }}
    }}
  ]
}}"""

            # -- Call LLM with retry
            assignments = []
            last_error = None
            for attempt in range(self.max_retries + 1):
                try:
                    raw = self._call_vllm(system, user, attempt)
                    result = self._extract_json(raw)
                    assignments = result.get("assignments", [])
                    if not isinstance(assignments, list):
                        raise ValueError("'assignments' must be a list")
                    if len(assignments) == 0:
                        raise ValueError("Empty assignments list returned by LLM")
                    break  # Success
                except Exception as e:
                    last_error = e
                    print(f"[MatrixGenerator] generate_matrix attempt {attempt + 1} failed: {e}")

            if not assignments:
                return {
                    "success": False,
                    "error": f"LLM failed to produce valid assignments after "
                             f"{self.max_retries + 1} attempts. Last: {last_error}"
                }

            # -- Validate & normalise assignments
            valid_trainer_ids = {t["id"] for t in trainers}
            valid_trainee_ids = {t["id"] for t in trainees}
            seen_trainees = set()
            clean_assignments = []

            for ass in assignments:
                try:
                    tid = int(ass.get("trainee_id", 0))
                    rid = int(ass.get("trainer_id", 0))

                    if tid not in valid_trainee_ids:
                        print(f"[MatrixGenerator] Skipping unknown trainee_id={tid}")
                        continue
                    if rid not in valid_trainer_ids:
                        print(f"[MatrixGenerator] Skipping unknown trainer_id={rid}")
                        continue
                    if tid in seen_trainees:
                        print(f"[MatrixGenerator] Duplicate trainee_id={tid}, skipping")
                        continue

                    # Ensure nested dicts exist
                    if "trainer_analysis" not in ass or not isinstance(ass["trainer_analysis"], dict):
                        ass["trainer_analysis"] = {
                            "strengths": "غير محدد",
                            "weaknesses": "غير محدد",
                            "reason": "تم التعيين تلقائياً"
                        }
                    if "trainee_analysis" not in ass or not isinstance(ass["trainee_analysis"], dict):
                        ass["trainee_analysis"] = {
                            "strengths": "غير محدد",
                            "weaknesses": "غير محدد",
                            "reason": "تم التعيين تلقائياً",
                            "confidence_score": 50
                        }

                    # Clamp confidence score
                    score = ass["trainee_analysis"].get("confidence_score", 50)
                    try:
                        score = max(0, min(100, int(score)))
                    except (TypeError, ValueError):
                        score = 50
                    ass["trainee_analysis"]["confidence_score"] = score

                    seen_trainees.add(tid)
                    clean_assignments.append(ass)
                except Exception as e:
                    print(f"[MatrixGenerator] Skipping malformed assignment: {e}")

            if not clean_assignments:
                return {"success": False, "error": "All assignments were invalid after validation."}

            # -- Persist
            cursor.execute(
                "DELETE FROM class_matrix_recommendations WHERE course_id = %s",
                (course_id,)
            )
            cursor.execute(
                "DELETE FROM class_matrix_summary WHERE course_id = %s",
                (course_id,)
            )

            trainer_stats: dict = {}  # trainer_id -> {sum, count}

            for ass in clean_assignments:
                trainer_id = int(ass["trainer_id"])
                trainee_id = int(ass["trainee_id"])
                t_conf = ass["trainee_analysis"].get("confidence_score", 50)

                cursor.execute(
                    """
                    INSERT INTO class_matrix_recommendations
                        (course_id, trainer_id, trainee_id, trainer_strengths, trainer_weaknesses, trainer_reason, 
                         trainee_strengths, trainee_weaknesses, trainee_reason, trainee_confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        course_id,
                        trainer_id,
                        trainee_id,
                        ass["trainer_analysis"].get("strengths", ""),
                        ass["trainer_analysis"].get("weaknesses", ""),
                        ass["trainer_analysis"].get("reason", ""),
                        ass["trainee_analysis"].get("strengths", ""),
                        ass["trainee_analysis"].get("weaknesses", ""),
                        ass["trainee_analysis"].get("reason", ""),
                        ass["trainee_analysis"].get("confidence_score", 50)
                    )
                )

                if trainer_id not in trainer_stats:
                    trainer_stats[trainer_id] = {"sum": 0, "count": 0}
                trainer_stats[trainer_id]["sum"] += t_conf
                trainer_stats[trainer_id]["count"] += 1

            for tid, stats in trainer_stats.items():
                avg = stats["sum"] / stats["count"] if stats["count"] > 0 else 0
                cursor.execute(
                    """
                    INSERT INTO class_matrix_summary
                        (course_id, trainer_id, avg_confidence, total_trainees)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (course_id, tid, round(avg, 2), stats["count"])
                )

            db.commit()
            return {
                "success": True,
                "assignments_count": len(clean_assignments),
                "trainers_count": len(trainer_stats),
                "course_nature": nature,
            }

        except Exception as e:
            db.rollback() if db else None
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            db.close()

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def _calc_age(self, dob) -> str:
        if not dob:
            return "غير محدد"
        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob, "%Y-%m-%d")
            except Exception:
                return "غير محدد"
        today = datetime.today()
        return str(
            today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        )

    def _safe_json(self, val):
        """Parse a JSON string field, returning it as-is if it's already a dict/list."""
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return str(val)

    def _build_trainers_block(self, trainers: list) -> str:
        lines = []
        for t in trainers:
            skills = self._safe_json(t.get("technical_skills"))
            if isinstance(skills, list):
                skills_str = "، ".join(str(s) for s in skills[:6]) or "غير محدد"
            else:
                skills_str = str(skills) if skills else "غير محدد"

            summary_raw = self._safe_json(t.get("professional_summary"))
            if isinstance(summary_raw, dict):
                summary = summary_raw.get("objective", "") or str(summary_raw)
            else:
                summary = str(summary_raw) if summary_raw else "غير متوفر"

            lines.append(
                f"  [المدرب #{t['id']}] الاسم: {t['full_name_ar']} | "
                f"المهارات: {skills_str} | "
                f"الملخص المهني: {summary[:120]}"
            )
        return "\n".join(lines)

    def _build_trainees_block(self, trainees: list) -> str:
        lines = []
        for t in trainees:
            skills = self._safe_json(t.get("technical_skills"))
            if isinstance(skills, list):
                skills_str = "، ".join(str(s) for s in skills[:6]) or "غير محدد"
            else:
                skills_str = str(skills) if skills else "غير محدد"

            soft = self._safe_json(t.get("soft_skills"))
            if isinstance(soft, list):
                soft_str = "، ".join(str(s) for s in soft[:4]) or "غير محدد"
            else:
                soft_str = str(soft) if soft else "غير محدد"

            lines.append(
                f"  [المتدرب #{t['id']}] الاسم: {t['full_name_ar']} | "
                f"العمر: {self._calc_age(t.get('dob'))} | "
                f"المهارات التقنية: {skills_str} | "
                f"المهارات الشخصية: {soft_str}"
            )
        return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test MatrixGenerator")
    parser.add_argument("--course-id", type=int, default=10, help="Course ID to test")
    parser.add_argument("--classify-only", action="store_true", help="Only run classification")
    args = parser.parse_args()

    gen = MatrixGenerator()
    print(f"\n{'='*60}")
    print(f"  NTA Class Trainer Matrix Generator")
    print(f"  Testing Course ID: {args.course_id}")
    print(f"{'='*60}\n")

    if args.classify_only:
        print("--- Step 1: Classifying course ---")
        result = gen.classify_course(args.course_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("--- Running full matrix generation ---")
        result = gen.generate_matrix(args.course_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
