import os
import random
from typing import List, Dict
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Load env in case it's not loaded elsewhere
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

class ChatEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        self.model = None
        if self.api_key and self.api_key != "dummy" and genai is not None:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                print(f"Gemini model init failed: {e}")

        self.system_prompts = {
            "trainee_guest": (
                "Persona:\n"
                "You are the NTA Registration Assistant (Guest Mode). Your mission is to help potential young applicants "
                "through the registration process. You are professional, bilingual, and encouraging.\n\n"
                "### Registration guidance\n"
                "Explain the active registration sections, required files, validation rules, and next steps without assuming every applicant sees the same flow.\n\n"
                "### Critical Validation Rules\n"
                "- National ID: 14 digits exactly.\n"
                "- LinkedIn: Mandatory in the final verification section when requested.\n"
                "- Age: usually 16 to 60 years unless the selected program says otherwise.\n"
                "- Files: keep uploads within the configured size limit.\n"
                "- Technical help: Suggest Ctrl+Shift+R for freezes."
            ),
            "trainee_authenticated": (
                "Persona:\n"
                "You are the NTA Success Coach. Your mission is to help registered young applicants and trainees navigate the portal, "
                "manage their profile, and track their courses. You are bilingual and professional.\n\n"
                "### Portal Features\n"
                "- Profile: You can update your skills and details via the profile screens.\n"
                "- Courses: Browse available programs in the Courses tab and track your status.\n"
                "- Documents: You can view or re-upload documents if requested by admins.\n\n"
                "### Guidance\n"
                "- Assist with finding relevant courses based on their skills.\n"
                "- Explain status badges clearly and avoid making final admission promises.\n"
                "- Tone: Motivational and community-focused."
            ),
            "admin": (
                "You are the NTA Admin Assistant. Your goal is to help administrators manage "
                "candidates, review stages, and understand system analytics. Be concise and technical."
            ),
            "editor": (
                "You are the NTA Content Assistant. Your goal is to help editors manage the "
                "Program Catalog, update course details, and maintain content quality."
            )
        }

    async def get_reply(self, role: str, question: str, history: List[Dict[str, str]] = None) -> str:
        if role == "trainee":
            role = "trainee_authenticated"

        if not self.model or role not in ["trainee_guest", "trainee_authenticated"]:
            return self._get_dummy_response(role, question)

        system_msg = self.system_prompts.get(role, "")
        formatted_history = []
        if history:
            recent_history = history[-5:]
            for item in recent_history:
                formatted_history.append({"role": "user", "parts": [item.get("question", "")]})
                formatted_history.append({"role": "model", "parts": [item.get("reply", "")]})

        try:
            chat = self.model.start_chat(history=formatted_history)
            full_prompt = f"{system_msg}\n\nUser Question: {question}" if not formatted_history else question
            response = chat.send_message(full_prompt, generation_config=genai.types.GenerationConfig(
                temperature=0.7,
            ))
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return "عذراً، واجهت مشكلة في الاتصال بالمساعد الذكي. يرجى المحاولة مرة أخرى لاحقاً."

    def _get_dummy_response(self, role: str, question: str) -> str:
        responses = {
            "trainee": [
                "يمكنك إكمال التسجيل من خلال الأقسام الظاهرة لك في صفحة التسجيل.",
                "جميع الدورات المتاحة تظهر في صفحة الدورات، ويمكنك متابعة حالة طلبك من لوحة التحكم.",
                "سيتم مراجعة طلبك من قبل المختصين، ويمكنك متابعة الحالة من حسابك."
            ],
            "trainee_authenticated": [
                "يمكنك متابعة حالة طلبك من لوحة التحكم، وسأساعدك في فهم أي خطوة مطلوبة.",
                "افتح صفحة الدورات لاختيار البرنامج المناسب ومراجعة حالة التقديم.",
                "راجع بياناتك ومستنداتك أولاً، ثم أكمل الأقسام المطلوبة في مسارك."
            ],
            "trainee_guest": [
                "مرحباً! يمكنني مساعدتك في فهم خطوات التسجيل والمستندات المطلوبة.",
                "ابدأ بقراءة التعليمات في صفحة التسجيل ثم جهز بياناتك الأساسية والمستندات المطلوبة.",
                "تأكد من إدخال رقم قومي صحيح ومراجعة البيانات قبل الإرسال."
            ],
            "admin": [
                "يمكنك رؤية جميع المتقدمين في صفحة عرض قائمة المرشحين.",
                "للموافقة على متقدم، افتح ملفه الشخصي ثم استخدم إجراءات المراجعة المتاحة.",
                "الإحصائيات في لوحة التحكم تعكس بيانات النظام الحالية."
            ],
            "editor": [
                "لإضافة دورة جديدة، اذهب إلى صفحة إدارة الدورات واضغط زر الإضافة.",
                "يمكنك تعديل حالة الدورة لتظهر بشكل صحيح للمتدربين.",
                "تأكد من رفع صور وملفات واضحة للدورات لضمان تجربة مستخدم جيدة."
            ]
        }
        role_responses = responses.get(role, ["مرحباً! كيف يمكنني مساعدتك اليوم؟"])
        return random.choice(role_responses)

chat_engine = ChatEngine()
