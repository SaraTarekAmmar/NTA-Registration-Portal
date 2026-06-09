import os
import asyncio
import sys

# Add the current directory to sys.path to import core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.chat_engine import chat_engine
from dotenv import load_dotenv

async def test_chat():
    load_dotenv()
    print("--- Testing NTA Gemini Chatbot ---")
    
    question = "What is the age limit for registration?"
    print(f"User: {question}")
    
    reply = await chat_engine.get_reply("trainee", question)
    print(f"AI: {reply}")
    
    print("\n--- Testing Arabic Response ---")
    question_ar = "ما هو الحد الأقصى لعدد المهارات التي يمكنني إضافتها؟"
    print(f"User: {question_ar}")
    
    reply_ar = await chat_engine.get_reply("trainee", question_ar)
    print(f"AI: {reply_ar}")

if __name__ == "__main__":
    if os.getenv("GEMINI_API_KEY") == "dummy" or not os.getenv("GEMINI_API_KEY"):
        print("Error: Please set GEMINI_API_KEY in .env")
    else:
        asyncio.run(test_chat())
