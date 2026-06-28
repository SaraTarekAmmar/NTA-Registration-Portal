import os
import google.generativeai as genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print("---LIST---")
    for m in models:
        # Strip 'models/' prefix for cleaner reading
        name = m.replace("models/", "")
        print(name)
    print("---END---")
except Exception as e:
    print(f"ERROR: {e}")
