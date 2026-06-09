import os
import random
from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv

# Load env in case it's not loaded elsewhere
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

class ChatEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # Configure Gemini
        if self.api_key and self.api_key != "dummy":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.model = None

        # Role-based system prompts
        self.system_prompts = {
            "trainee_guest": (
                "Persona:\n"
                "You are the NTA Registration Assistant (Guest Mode). Your mission is to help potential applicants "
                "through the 10-step registration process. You are professional, bilingual, and encouraging.\n\n"
                "### 1. The 10-Section Registration Knowledge Base\n"
                "Focus on explaining what is needed for each step:\n"
                "1. Personal Details, 2. Contact, 3. Education, 4. Employment, 5. Skills, 6. Prizes, 7. Voluntary Work, 8. Logistics, 9. Quiz, 10. Verification.\n\n"
                "### 2. Critical Validation Rules\n"
                "- National ID: 14 digits exactly.\n"
                "- LinkedIn: Mandatory in Section 10.\n"
                "- Age: 16 to 60 years.\n"
                "- Files: Under 10MB.\n"
                "- Social Media: Section 5 locks permanently once you reach Section 6.\n"
                "- Technical help: Suggest Ctrl+Shift+R for freezes."
            ),
            "trainee_authenticated": (
                "Persona:\n"
                "You are the NTA Success Coach. Your mission is to help registered trainees navigate the portal, "
                "manage their profile, and track their courses. You are bilingual and professional.\n\n"
                "### 1. Portal Features\n"
                "- Profile: You can update your skills and details via the 'Edit Profile' modal.\n"
                "- Courses: Browse available programs in the 'Courses' tab and track your status (Registered, Pending, Completed).\n"
                "- Documents: You can view or re-upload documents if requested by admins.\n\n"
                "### 2. Guidance\n"
                "- Assist with finding relevant courses based on their skills.\n"
                "- Explain status badges: 'قيد المراجعة' means your application is being reviewed.\n"
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
        """
        Interacts with the Gemini LLM.
        """
        # Map generic 'trainee' to authenticated if it comes through legacy paths
        if role == "trainee":
            role = "trainee_authenticated"

        if not self.model or role not in ["trainee_guest", "trainee_authenticated"]:
            # Fallback to dummy or basic logic for other roles as requested
            return self._get_dummy_response(role, question)

        system_msg = self.system_prompts.get(role, "")
        
        # Prepare history for Gemini (Limit to last 5 messages / 10 turns if each turn has user+model)
        # Actually history is usually list of objects with 'question' and 'reply' from chat.py history format
        # but the chat.py ask_chatbot doesn't pass history yet.
        
        formatted_history = []
        if history:
            # Take last 5 interactions
            recent_history = history[-5:]
            for item in recent_history:
                formatted_history.append({"role": "user", "parts": [item.get("question", "")]})
                formatted_history.append({"role": "model", "parts": [item.get("reply", "")]})

        try:
            # Create a chat session with the system prompt injected as the first instruction
            # Gemini-pro 1.0 doesn't have a dedicated system_instruction parameter in the same way 1.5 does
            # so we'll prepend it to the first message or use a preamble.
            
            chat = self.model.start_chat(history=formatted_history)
            
            # Prepend system message to the question if it's the first message
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
                "يمكنك إكمال التسجيل عبر الـ 11 خطوة المتاحة في ملفك الشخصي.",
                "جميع الدورات متاحة في صفحة 'الدورات التدريبية'، ويمكنك التقديم بضغطة زر.",
                "سيتم مراجعة طلبك من قبل المختصين قريباً، يمكنك متابعة الحالة من لوحة التحكم."
            ],
            "admin": [
                "يمكنك رؤية جميع المتقدمين في صفحة 'عرض قائمة المرشحين'.",
                "للموافقة على متقدم، اذهب لملفه الشخصي واضغط على 'مراجعة المرحلة'.",
                "الإحصائيات المتاحة في لوحة التحكم تعكس البيانات اللحظية للمتقدمين."
            ],
            "editor": [
                "لإضافة دورة جديدة، اذهب لصفحة 'إدارة الدورات' واضغط على الزر (+) بالأعلى.",
                "يمكنك تعديل حالة الدورة (قادم، جاري، مكتمل) لتظهر بشكل صحيح للمتدربين.",
                "تأكد من رفع صور ذات جودة عالية للدورات التدريبية لضمان تجربة مستخدم مميزة."
            ]
        }
        
        role_responses = responses.get(role, ["مرحباً! كيف يمكنني مساعدتك اليوم؟"])
        return random.choice(role_responses)

# Singleton instance
chat_engine = ChatEngine()
