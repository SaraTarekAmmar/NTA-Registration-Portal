import os
import json
import requests
import sys
from pathlib import Path

# Add backend to path to use core utilities if needed
# Add backend to path to use core utilities
current_dir = Path(__file__).resolve().parent
ROOT = current_dir.parent.parent
sys.path.append(str(ROOT / "admin" / "backend"))

try:
    from core.database import get_db_connection
except ImportError:
    # Fallback for different execution environments
    sys.path.append(str(ROOT))
    from admin.backend.core.database import get_db_connection

class RequirementAnalyzer:
    def __init__(self):
        # Load config from centralized documentation or env
        self.vllm_url = os.getenv("VLLM_BASE_URL", "http://localhost:7834")
        self.model_name = os.getenv("VLLM_MODEL", "google/gemma-4-31B-it")
        self.data_dir = ROOT / "data"
        self.max_retries = 2

    def _call_vllm(self, system_prompt, user_prompt, attempt=0):
        try:
            response = requests.post(
                f"{self.vllm_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.05,  # Deterministic
                    "top_p": 0.9
                },
                timeout=180
            )
            response.raise_for_status()
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            raise ValueError(f"Unexpected response format: {json.dumps(data)[:200]}")
        except Exception as e:
            if attempt < self.max_retries:
                return self._call_vllm(system_prompt, user_prompt, attempt + 1)
            return f"Error calling vLLM: {str(e)}"

    def _extract_json(self, text):
        """Robustly extract JSON from LLM response."""
        import re
        # Strategy 1: Fenced code block
        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.DOTALL)
        if fence_match:
            try: return json.loads(fence_match.group(1).strip())
            except: pass

        # Strategy 2: First balanced { ... }
        start = text.find("{")
        if start != -1:
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try: return json.loads(candidate)
                        except:
                            # Try simple cleaning
                            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
                            try: return json.loads(cleaned)
                            except: break
        
        # Strategy 3: Direct parse
        try: return json.loads(text.strip())
        except:
            raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}...")


    def extract_text_from_file(self, file_path):
        """Reads content from .txt, .pdf, or .docx."""
        abs_path = ROOT / file_path.lstrip("/")
        if not abs_path.exists():
            return ""
        
        ext = abs_path.suffix.lower()
        if ext == ".txt":
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        # Add PDF/DOCX extraction here in the future
        return ""

    def get_course_context(self, course_id):
        """Aggregates Course Name, Description and Material text."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            # 1. Fetch Course Meta
            cursor.execute("SELECT title, description FROM courses WHERE id = %s", (course_id,))
            course = cursor.fetchone()
            if not course: return None

            # 2. Fetch Material Files from sessions
            cursor.execute("SELECT topic, materials FROM course_sessions WHERE course_id = %s", (course_id,))
            sessions = cursor.fetchall()
            
            material_text = ""
            for s in sessions:
                if s['materials']:
                    mats = json.loads(s['materials']) if isinstance(s['materials'], str) else s['materials']
                    if mats.get('file_path'):
                        material_text += f"\n\n--- Session: {s['topic']} ---\n"
                        material_text += self.extract_text_from_file(mats['file_path'])
            
            return {
                "name": course['title'],
                "description": course['description'],
                "material": material_text[:10000] # Limit context for stability
            }
        finally:
            cursor.close()
            db.close()

    def analyze_trainee(self, trainee_id, course_id):
        """Main pipeline: Step 1 (Quantify) -> Step 2 (Summarize)."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            # 1. Fetch Trainee Profile
            cursor.execute("""
                SELECT u.full_name_ar, u.national_id, tp.professional_summary_text
                FROM users u
                JOIN trainee_profiles tp ON u.id = tp.user_id
                WHERE u.id = %s
            """, (trainee_id,))
            trainee = cursor.fetchone()
            if not trainee: return {"success": False, "error": "Trainee not found"}

            # Fetch Child Tables for AI Context
            cursor.execute("SELECT skill_name, proficiency FROM trainee_skills WHERE trainee_id = %s", (trainee_id,))
            trainee['technical_skills'] = ", ".join([f"{r['skill_name']} ({r['proficiency']})" for r in cursor.fetchall() if r['skill_name']])

            cursor.execute("SELECT institution, major, degree, grad_year FROM trainee_education WHERE trainee_id = %s", (trainee_id,))
            trainee['academic_history'] = "; ".join([f"{r['degree']} in {r['major']} from {r['institution']} ({r['grad_year']})" for r in cursor.fetchall()])

            cursor.execute("SELECT organization, title, responsibilities FROM trainee_experience WHERE trainee_id = %s", (trainee_id,))
            trainee['professional_history'] = "; ".join([f"{r['title']} at {r['organization']}: {r['responsibilities']}" for r in cursor.fetchall()])

            cursor.execute("SELECT award_title, achievement FROM trainee_awards WHERE trainee_id = %s", (trainee_id,))
            trainee['awards'] = ", ".join([f"{r['award_title']} ({r['achievement']})" for r in cursor.fetchall()])

            cursor.execute("SELECT language_name, proficiency FROM trainee_languages WHERE trainee_id = %s", (trainee_id,))
            trainee['languages'] = ", ".join([f"{r['language_name']} ({r['proficiency']})" for r in cursor.fetchall()])

            # 2. Fetch Course Context
            course_ctx = self.get_course_context(course_id)
            if not course_ctx: return {"success": False, "error": "Course not found"}

            # ── STEP 1: QUANTITATIVE ANALYSIS ──
            sys1, user1 = self._build_analysis_prompt(trainee, course_ctx)
            response1 = self._call_vllm(sys1, user1)
            
            try:
                analysis_data = self._extract_json(response1)
            except Exception as e:
                return {"success": False, "error": f"Failed to parse AI Analysis: {str(e)}", "raw": response1}

            # ── STEP 2: SUMMARY GENERATION ──
            sys2, user2 = self._build_summary_prompt(analysis_data)
            summary_text = self._call_vllm(sys2, user2)

            score = analysis_data.get('overall_match_percentage', 0)
            
            # ── PERSIST TO DATABASE ──
            cursor.execute("""
                INSERT INTO cv_matching_results (course_id, national_id, match_score, evidence)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    match_score = VALUES(match_score), 
                    evidence = VALUES(evidence)
            """, (
                course_id, 
                trainee['national_id'], 
                score,
                summary_text.strip()
            ))
            
            cursor.execute("SELECT id FROM cv_matching_results WHERE course_id = %s AND national_id = %s", (course_id, trainee['national_id']))
            match_id = cursor.fetchone()['id']
            
            cursor.execute("DELETE FROM cv_matching_requirements WHERE match_id = %s", (match_id,))
            reqs = analysis_data.get('requirement_matches', [])
            for r in reqs:
                cursor.execute("""
                    INSERT INTO cv_matching_requirements (match_id, requirement_topic, score, evidence)
                    VALUES (%s, %s, %s, %s)
                """, (match_id, r.get('requirement', ''), r.get('score', 0), r.get('evidence', '')))
            
            # --- AUTOMATED STAGE ADVANCEMENT (Threshold > 95%) ---
            if score > 95:
                # Advance from Stage 1 to 2 if currently at Stage 1
                cursor.execute("""
                    UPDATE pipeline_state 
                    SET current_stage_id = 2 
                    WHERE trainee_id = %s AND current_stage_id = 1
                """, (trainee_id,))
                
                if cursor.rowcount > 0:
                    # Record Automated Review
                    cursor.execute("SELECT id, full_name_ar FROM users WHERE role = 'superadmin' ORDER BY id ASC LIMIT 1")
                    sys_admin = cursor.fetchone()
                    sys_id = sys_admin['id'] if sys_admin else 1
                    
                    cursor.execute("""
                        INSERT INTO stage_reviews (trainee_id, stage_id, reviewer_id, result, reviewer_name, review_date, notes) 
                        VALUES (%s, %s, %s, 'Active', 'النظام الآلي (Requirement Analyzer)', CURDATE(), %s)
                    """, (
                        trainee_id, 
                        1, # Stage 1
                        sys_id, 
                        f'تم اجتياز مرحلة الفرز الإلكتروني تلقائياً بناءً على درجة مطابقة عالية ({score}%).'
                    ))
            
            db.commit()

            return {
                "success": True,
                "radar_chart": analysis_data,
                "summary": summary_text.strip()
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            db.close()

    def _build_analysis_prompt(self, trainee, course):
        system = "You are an expert NTA Admissions Reviewer. You must output ONLY valid JSON. No comments, no conversational filler."
        user = f"""
Task: Analyze the Trainee against the Course Syllabus.
1. Identify 5 specific technical/academic requirements from the Syllabus.
2. Score the trainee (0-100) on each.
3. Provide a 1-sentence evidence for each.

COURSE: {course['name']}
SYLLABUS: {course['material'][:4000]}

TRAINEE: {trainee['full_name_ar']}
SUMMARY: {trainee['professional_summary_text']}
SKILLS: {trainee['technical_skills']}
EDUCATION: {trainee['academic_history']}
EXPERIENCE: {trainee['professional_history']}
AWARDS: {trainee['awards']}
LANGUAGES: {trainee['languages']}

OUTPUT FORMAT (JSON):
{{
  "requirement_matches": [
    {{"requirement": "Topic Name", "score": 85, "evidence": "Short justification"}},
    {{"requirement": "Topic Name", "score": 70, "evidence": "Short justification"}},
    {{"requirement": "Topic Name", "score": 90, "evidence": "Short justification"}},
    {{"requirement": "Topic Name", "score": 60, "evidence": "Short justification"}},
    {{"requirement": "Topic Name", "score": 75, "evidence": "Short justification"}}
  ],
  "overall_match_percentage": 76
}}
"""
        return system, user

    def _build_summary_prompt(self, analysis_data):
        system = "You are a professional Arabic summary writer for NTA Academy."
        user = f"""
Based on this technical analysis:
{json.dumps(analysis_data, indent=2)}

Write a professional 2-3 sentence summary in Arabic. 
Mention the most impressive skill and the area needing improvement.
"""
        return system, user

    def _call_vllm(self, system_prompt, user_prompt):
        try:
            response = requests.post(
                f"{self.vllm_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.1
                },
                timeout=180
            )
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            return f"Error: Unexpected response format: {json.dumps(data)}"
        except Exception as e:
            return f"Error calling vLLM: {str(e)}"

    def _clean_json(self, text):
        # Deprecated: use _extract_json
        return text.strip()

# Test execution if run directly
if __name__ == "__main__":
    analyzer = RequirementAnalyzer()
    # Replace with real IDs for manual testing
    # result = analyzer.analyze_trainee(trainee_id=1, course_id=10)
    # print(json.dumps(result, indent=2))
