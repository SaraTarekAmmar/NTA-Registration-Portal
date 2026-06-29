import os
import random
from typing import List, Dict

class ChatEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "dummy")
        
        # Role-based system prompts
        self.system_prompts = {
            "trainee": (
                "You are the NTA Academy Assistant for Trainees. Your goal is to help applicants "
                "with registration steps, course information, and profile status. Be encouraging and professional."
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
        Interacts with the LLM. 
        Note: Currently uses dummy logic if API key is 'dummy'.
        """
        system_msg = self.system_prompts.get(role, "You are a helpful assistant for the NTA portal.")
        
        if self.api_key == "dummy":
            return self._get_dummy_response(role, question)
        
        # Real LLM integration code would go here
        # e.g., OpenAI or Gemini API call
        return f"[DUMMY] {system_msg}\n\nYou asked: {question}\n(This is a placeholder response as a dummy API key is in use)."

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
