
import os
import json
import requests
import sys
import base64
from pathlib import Path
import fitz  # PyMuPDF
from docx import Document

# Resolve project root
current_dir = Path(__file__).resolve().parent
ROOT = current_dir.parent.parent
sys.path.append(str(ROOT / "admin" / "backend"))

try:
    from core.database import get_db_connection
    from core.notifications import send_rejection_email, send_stage_pass_email
except ImportError:
    # Try another relative path if needed
    sys.path.append(str(ROOT))
    from admin.backend.core.database import get_db_connection
    from admin.backend.core.notifications import send_rejection_email, send_stage_pass_email

class AdmissionAnalyzer:
    def __init__(self):
        self.vllm_url = os.getenv("VLLM_BASE_URL", "http://localhost:7834")
        self.model_name = os.getenv("VLLM_MODEL", "google/gemma-4-31B-it")
        self.max_retries = 2

    def _call_vllm(self, system_prompt, user_prompt, image_b64=None, attempt=0):
        try:
            content = [{"type": "text", "text": user_prompt}]
            if image_b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                })

            response = requests.post(
                f"{self.vllm_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    "max_tokens": 2500,
                    "temperature": 0.05
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
            return f"Error: {str(e)}"

    def _extract_json(self, text):
        if not isinstance(text, str):
            return text # Already parsed?
        import re
        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.DOTALL)
        if fence_match:
            try: return json.loads(fence_match.group(1).strip())
            except: pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try: return json.loads(text[start:end+1])
            except: pass
        raise ValueError("Could not extract valid JSON")

    def get_document_data(self, file_path):
        abs_path = ROOT / file_path.lstrip("/")
        if not abs_path.exists():
            return None, "File not found"
        
        ext = abs_path.suffix.lower()
        
        if ext == ".pdf":
            # Convert first page to image for Vision AI
            with fitz.open(abs_path) as doc:
                if len(doc) == 0: return None, "Empty PDF"
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better OCR
                img_data = pix.tobytes("jpg")
                return base64.b64encode(img_data).decode('utf-8'), "image"
        
        elif ext in [".jpg", ".jpeg", ".png"]:
            with open(abs_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8'), "image"
        
        elif ext == ".docx":
            doc = Document(abs_path)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text, "text"
            
        elif ext == ".txt":
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read(), "text"
                
        return None, "Unsupported format"

    def run_full_check(self, trainee_id, course_id, update_progress=None):
        """Main pipeline: Phase 1 -> 2 -> 3 -> 4."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            # 1. Fetch Trainee Profile & Raw Data
            if update_progress: update_progress("Fetching trainee profile data...", 10)
            cursor.execute("""
                SELECT u.full_name_ar, u.national_id, u.email, u.gender, u.dob,
                       tp.address, tp.nationality as country_of_stay,
                       tp.professional_summary_text, tp.documents
                FROM users u
                JOIN trainee_profiles tp ON u.id = tp.user_id
                WHERE u.id = %s
            """, (trainee_id,))
            user = cursor.fetchone()
            if not user: return {"success": False, "error": "Trainee not found"}
            
            docs = json.loads(user['documents']) if user['documents'] else {}
            
            # Fetch experience, skills, education
            cursor.execute("SELECT organization, title, responsibilities, start_date, end_date FROM trainee_experience WHERE trainee_id = %s", (trainee_id,))
            experience = cursor.fetchall()
            cursor.execute("SELECT skill_name, proficiency FROM trainee_skills WHERE trainee_id = %s", (trainee_id,))
            skills = cursor.fetchall()
            cursor.execute("SELECT institution, major, degree, grad_year FROM trainee_education WHERE trainee_id = %s", (trainee_id,))
            education = cursor.fetchall()

            # --- PHASE 1: IDENTITY ---
            if update_progress: update_progress("Phase 1: Verifying Identity (ID/Passport Image)...", 25)
            id_path = docs.get('idScan') or docs.get('passportScan')
            id_content, id_type = self.get_document_data(id_path) if id_path else (None, None)
            
            p1_system = """You are a professional Identity Auditor for the National Training Academy (NTA).
            Your task is to verify the authenticity and accuracy of the applicant's Identity Document (ID or Passport).
            Compare the image provided against the Database Data.
            Return JSON ONLY:
            {
                "match_results": {
                    "full_name": {"score": 0-100, "ai": "extracted name in Arabic", "comment": "detailed check result"}, 
                    "national_id": {"score": 0-100, "ai": "extracted 14-digit id", "comment": ""}, 
                    "gender": {"score": 0-100, "ai": "Male/Female", "comment": ""}, 
                    "dob": {"score": 0-100, "ai": "YYYY-MM-DD", "comment": ""}}, 
                "overall_status": "Matched/Mismatched", 
                "confidence": 0-100,
                "rejection_reason": "Arabic text explaining precisely what didn't match (e.g., 'رقم الهوية غير مطابق' or 'الاسم لا يتطابق مع المستند المرفوع'). Keep it professional."
            }"""
            p1_user = f"DB DATA: {json.dumps(user, default=str)}"
            p1_raw = self._call_vllm(p1_system, p1_user, image_b64=id_content if id_type == "image" else None)
            p1_res = self._extract_json(p1_raw)

            # Save Phase 1 Results to dedicated table
            mr = p1_res.get('match_results', {})
            cursor.execute("""
                INSERT INTO admission_stage_1_identity 
                (trainee_id, full_name_score, full_name_ai, national_id_score, national_id_ai, 
                 gender_score, gender_ai, dob_score, dob_ai, overall_status, confidence, rejection_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                trainee_id,
                mr.get('full_name', {}).get('score', 0), mr.get('full_name', {}).get('ai', ''),
                mr.get('national_id', {}).get('score', 0), mr.get('national_id', {}).get('ai', ''),
                mr.get('gender', {}).get('score', 0), mr.get('gender', {}).get('ai', ''),
                mr.get('dob', {}).get('score', 0), mr.get('dob', {}).get('ai', ''),
                p1_res.get('overall_status', 'Flagged'),
                p1_res.get('confidence', 0),
                p1_res.get('rejection_reason', '')
            ))

            # --- PHASE 2: PROFESSIONAL ---
            if update_progress: update_progress("Phase 2: Verifying CV & Experience...", 50)
            cv_path = docs.get('cvResume')
            cv_content, cv_type = self.get_document_data(cv_path) if cv_path else (None, None)
            
            p2_system = """Analyze the Trainee's CV against their declared Experience and Skills. 
            Identify discrepancies in dates, job titles, or skill proficiencies.
            Return JSON ONLY: {"experience_match": [...], "skills_match": [...], "status": "Matched/Partial/Mismatched", "confidence": 0-100}"""
            p2_user = f"DECLARED EXP: {json.dumps(experience, default=str)}\nSKILLS: {json.dumps(skills)}"
            p2_raw = self._call_vllm(p2_system, p2_user, image_b64=cv_content if cv_type == "image" else None)
            p2_res = self._extract_json(p2_raw)

            # --- PHASE 3: EDUCATION ---
            if update_progress: update_progress("Phase 3: Verifying Education Certificates...", 75)
            edu_path = docs.get('graduationCertificate')
            edu_content, edu_type = self.get_document_data(edu_path) if edu_path else (None, None)
            
            p3_system = """Verify the Graduation Certificate. Confirm the degree, major, and graduation year.
            Return JSON ONLY: {"education_match": [...], "status": "Verified/Inconsistent", "confidence": 0-100}"""
            p3_user = f"DECLARED EDU: {json.dumps(education, default=str)}"
            p3_raw = self._call_vllm(p3_system, p3_user, image_b64=edu_content if edu_type == "image" else None)
            p3_res = self._extract_json(p3_raw)

            # --- PHASE 4: SUMMARY & VERDICT ---
            if update_progress: update_progress("Phase 4: Generating Final Assessment...", 90)
            p4_system = """Summarize the overall assessment of the applicant based on Identity, Professional, and Education checks.
            Your summary must be in Arabic and highly professional. 
            Conclude with a clear verdict: 'Accepted' or 'Rejected'.
            If rejected, clearly state the reasons in a way that can be shared with the applicant."""
            p4_user = f"P1 Results: {json.dumps(p1_res)}\nP2 Results: {json.dumps(p2_res)}\nP3 Results: {json.dumps(p3_res)}"
            p4_res_raw = self._call_vllm(p4_system, p4_user)
            
            # Simple heuristic for final judge if LLM doesn't format JSON
            final_judge = "Accepted" if "Accepted" in p4_res_raw or "مقبول" in p4_res_raw else "Rejected"
            avg_confidence = (p1_res.get('confidence', 0) + p2_res.get('confidence', 0) + p3_res.get('confidence', 0)) // 3

            # --- PERSIST RESULTS ---
            cursor.execute("""
                INSERT INTO admission_sorting_results 
                (trainee_id, course_id, identity_status, professional_status, education_status, final_judge, confidence_score, ai_summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                trainee_id, course_id,
                p1_res.get('overall_status', 'Flagged'),
                p2_res.get('status', 'Partial'),
                p3_res.get('status', 'Inconsistent'),
                final_judge, avg_confidence, p4_res_raw
            ))
            sorting_id = cursor.lastrowid
            
            # Insert child records for Experience and Education
            for exp in p2_res.get('experience_match', []):
                cursor.execute("""
                    INSERT INTO admission_sorting_experience (sorting_id, item_description, match_status, ai_comment)
                    VALUES (%s, %s, %s, %s)
                """, (sorting_id, str(exp.get('item', '')), exp.get('status', ''), exp.get('comment', '')))
                
            for edu in p3_res.get('education_match', []):
                cursor.execute("""
                    INSERT INTO admission_sorting_education (sorting_id, degree_info, match_status)
                    VALUES (%s, %s, %s)
                """, (sorting_id, str(edu.get('item', '')), edu.get('status', '')))
            
            # Update Pipeline State
            new_stage = 2 if final_judge == "Accepted" else 1
            new_status = 'active' if final_judge == "Accepted" else 'rejected'
            
            cursor.execute("""
                UPDATE pipeline_state 
                SET current_stage_id = %s, status = %s 
                WHERE trainee_id = %s
            """, (new_stage, new_status, trainee_id))
            
            # --- SEND AUTOMATED NOTIFICATION ---
            if final_judge == "Accepted":
                send_stage_pass_email(user['email'], user['full_name_ar'], "الفرز الإلكتروني (المرحلة الأولى)", user['gender'])
            else:
                # --- REJECTION RESET (Hard Reset) ---
                # 1. Determine Rejection reason (P1 results)
                rej_reason = p1_res.get('rejection_reason', 'لم يتم اجتياز معايير الفرز الإلكتروني الأولية.')
                
                # 2. Send Notification Email
                send_rejection_email(user['email'], user['full_name_ar'], rej_reason, user['gender'])
                
                # 3. Delete Physical Folder
                from core.upload_manager import delete_trainee_folder
                delete_trainee_folder(user['full_name_ar'], user['national_id'])
                
                # 4. Log Activity (Before deletion, though we use general category)
                from core.logger_util import log_activity
                log_activity(
                    category="ADMIN",
                    event_type="AUTO_REJECTION_PURGE",
                    component="Admission AI",
                    details={"trainee_id": trainee_id, "reason": rej_reason}
                )

                # 5. Delete Database Records (Cascades from users)
                cursor.execute("DELETE FROM users WHERE id = %s", (trainee_id,))
                
                db.commit() # Commit deletion early
                if update_progress: update_progress(f"Applicant {trainee_id} rejected and purged.", 100)
                return {"success": True, "judge": "Rejected", "purged": True}
            
            # Audit Log
            cursor.execute("""
                INSERT INTO stage_reviews (trainee_id, stage_id, reviewer_id, result, reviewer_name, review_date, notes, details, attachment_path) 
                VALUES (%s, 1, 1, %s, 'النظام الآلي (Admission AI)', CURDATE(), %s, %s, '')
            """, (trainee_id, 'Active' if final_judge == "Accepted" else 'Rejected', p4_res_raw[:500], json.dumps(p4_res_raw)))

            db.commit()
            if update_progress: update_progress("Completed successfully", 100)

            return {
                "success": True,
                "judge": final_judge,
                "confidence": avg_confidence,
                "summary": p4_res_raw,
                "details": {
                    "identity": p1_res,
                    "professional": p2_res,
                    "education": p3_res
                }
            }

        except Exception as e:
            if db: db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            db.close()

if __name__ == "__main__":
    analyzer = AdmissionAnalyzer()
    # Test call
    # res = analyzer.run_full_check(65, 10, lambda msg, prog: print(f"[{prog}%] {msg}"))
    # print(json.dumps(res, indent=2))
