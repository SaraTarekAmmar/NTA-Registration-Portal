import os
import sys
import time
import google.generativeai as genai
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

def ocr_pdf():
    pdf_path = os.path.join("user", "تقرير ملاحظات اختبار لينك التسجيل -النسخة المجمعة.pdf")
    print(f"Uploading {pdf_path} to Gemini...")
    
    if not os.path.exists(pdf_path):
        print("Error: PDF file does not exist!")
        return
        
    try:
        # Upload the file using the Gemini File API
        myfile = genai.upload_file(pdf_path)
        print(f"Uploaded file name: {myfile.name}")
        print("Waiting for file processing...")
        
        # Wait for the file to be processed
        while myfile.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            myfile = genai.get_file(myfile.name)
            
        if myfile.state.name == "FAILED":
            raise ValueError(f"File processing failed: {myfile.error.message}")
            
        print("\nFile processing complete. Launching Gemini model to extract comments...")
        
        # We will use gemini-2.5-flash as it is highly supported and robust
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = (
            "You are an expert system architect and QA engineer specializing in analyzing software systems and forms. "
            "Please read the attached Arabic PDF document which contains testing comments (تقرير ملاحظات اختبار لينك التسجيل - النسخة المجمعة). "
            "Task 1: Perform a complete, highly precise OCR/transcription of EVERY SINGLE COMMENT listed in the PDF. "
            "Ensure that you transcribe all fields exactly as they are written in Arabic (e.g., ID 'م', Page 'الصفحة', Component 'الملاحظة', Description 'وصف الملاحظة', and Suggestion 'الاقتراح'). Do not summarize them; write them exactly as they are. "
            "Task 2: Under each extracted comment, add a section called 'تعليق المهندس / ما يجب القيام به:' (Engineer's Comment / What needs to be done). "
            "In this section, analyze the issue based on the current registration portal structure (HTML, CSS, JS, FastAPI backend, and MySQL database) and write concrete, actionable developer instructions on what must be changed in the codebase to implement the fix. "
            "Write the entire analysis and transcription in professional Arabic. Ensure it is organized and structured perfectly."
        )
        
        print("Sending prompt to Gemini...")
        response = model.generate_content([myfile, prompt])
        
        output_path = os.path.join("user", "تقرير_ملاحظات_التسجيل_محللة.txt")
        print(f"Writing structured output to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(response.text)
            
        print("SUCCESS! Analysis completed successfully.")
        
        # Cleanup uploaded file from Gemini servers
        print("Cleaning up file from Gemini storage...")
        genai.delete_file(myfile.name)
        
    except Exception as e:
        print(f"Error during OCR and analysis: {e}")

if __name__ == "__main__":
    ocr_pdf()
