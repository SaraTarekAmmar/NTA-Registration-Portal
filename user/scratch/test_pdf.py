import os
import sys
from pypdf import PdfReader

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def check_pdf():
    pdf_path = os.path.join("user", "تقرير ملاحظات اختبار لينك التسجيل -النسخة المجمعة.pdf")
    print(f"Reading PDF from: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print("Error: PDF file does not exist!")
        return
        
    try:
        reader = PdfReader(pdf_path)
        print(f"Number of pages: {len(reader.pages)}")
        
        for idx, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            print(f"\n--- PAGE {idx} ---")
            print(f"Text length: {len(text) if text else 0}")
            if text:
                print(text[:1000])  # Print first 1000 characters
            else:
                print("[No text extracted from this page - it might be a scanned image]")
                
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    check_pdf()
