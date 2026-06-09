import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print(f"Checking models for API Key: {api_key[:10]}...")

try:
    print("\nSupported Models for 'generateContent':")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name} (DisplayName: {m.display_name})")
except Exception as e:
    print(f"\nError listing models: {e}")
