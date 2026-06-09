import os
import sys
import google.generativeai as genai
from pypdf import PdfReader
from dotenv import load_dotenv

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
env_path = os.path.join("user", "backend", ".env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment!")
    sys.exit(1)

genai.configure(api_key=api_key)

def extract_local_text():
    pdf_path = os.path.join("user", "تقرير ملاحظات اختبار لينك التسجيل -النسخة المجمعة.pdf")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)
        
    print(f"Extracting text from: {pdf_path}")
    reader = PdfReader(pdf_path)
    full_text = []
    
    for idx, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        full_text.append(f"--- START PAGE {idx} ---\n{text}\n--- END PAGE {idx} ---")
        
    return "\n\n".join(full_text)

def analyze_with_gemini(raw_text):
    print("Sending extracted text to Gemini for reconstruction and analysis...")
    model = genai.GenerativeModel("gemini-3-flash-preview")
    
    prompt = f"""
You are an expert QA Engineer and Senior Systems Architect.
Below is the raw extracted text from an Arabic PDF document listing QA testing comments (تقرير ملاحظات اختبار لينك التسجيل - النسخة المجمعة) for a 10-step registration portal.

Due to PDF extraction, some Arabic text might have reverse character direction, spelling issues, or split words (e.g., 'الخيرة' instead of 'الخبرة', 'عرنر' instead of 'عربي', 'اليرمجر' instead of 'البرمجة', 'تفعل' instead of 'تفعيل', etc.).

Please perform the following:
1. Reconstruct and organize EVERY SINGLE QA COMMENT from the PDF text.
2. For each comment, output its fields exactly as they are in the PDF in Arabic:
   - م (الرقم)
   - الصفحة / القسم (Page/Section)
   - الملاحظة (Component/Topic)
   - وصف الملاحظة (Description)
   - الاقتراح (Suggestion)
   
3. Under each comment, write a detailed and actionable section in Arabic:
   'تعليق المهندس / ما يجب القيام به:' (Engineer's Comment / Action Plan)
   In this section, explain exactly what needs to be changed in the codebase (HTML, CSS, registration.js, FastAPI backend, or MySQL DB schema) to resolve this specific comment, keeping in mind our current 10-step registration portal.

Format the output beautifully and write the entire response in professional, clear Arabic.

Here is the raw extracted PDF text:
{raw_text}
"""
    
    response = model.generate_content(prompt)
    return response.text

def main():
    try:
        raw_text = extract_local_text()
        print(f"Extracted {len(raw_text)} characters.")
        
        analysis = analyze_with_gemini(raw_text)
        
        output_path = os.path.join("user", "تقرير_ملاحظات_التسجيل_محللة.txt")
        print(f"Writing result to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(analysis)
            
        print("SUCCESS! File تقرير_ملاحظات_التسجيل_محللة.txt was created.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
