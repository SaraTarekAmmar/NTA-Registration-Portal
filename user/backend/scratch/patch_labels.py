"""
Adds (اجبارى) or (اختيارى) markers to all labels that are missing them.
Runs in-place on registration.html.

Classification rules:
- A label is OPTIONAL if its field is Optional in Pydantic schema,
  or if the section is conditionally shown (prizes, conferences, political, etc.)
- A label is MANDATORY otherwise.
"""
import re
from pathlib import Path

html_path = Path(r"d:\Work\NTA\NTA-Regestration-Portal - Final\user\registration.html")
html = html_path.read_bytes().decode("utf-8")

MARKER_RE = re.compile(r"اجبارى|اختيارى")

# Map of label text substring → (mandatory=True/False)
# True  = اجبارى
# False = اختيارى
# None  = skip (already handled or quiz question)
RULES = {
    # Step 3 – education
    "الدرجة (ماجستير": True,
    "اسم الجهة المانحة للدرجة": True,
    "التخصص الرئيسي للدرجة": True,
    "التخصص الفرعي": False,
    "تاريخ البدء": True,
    "تاريخ الانتهاء": True,
    "تمويل شخصي": False,
    "اسم الجهة التي رشحتك": False,
    "اسم جهة المنحة": False,
    "الاختبارات والشهادات المعيارية": False,
    "اسم الاختبار (Test Name)": False,
    "درجة الاختبار (Test Score)": False,
    "جهة الإصدار (Issuing Authority)": False,
    "تاريخ الحصول (Date Obtained)": False,
    "Attach Document": False,

    # Step 4 – employment
    "هل لديك خبرة عملية": True,
    "تحميل السيرة الذاتية (PDF, DOC, DOCX)": True,
    "نوع الوظيفة": True,
    "طبيعة الوظيفة": True,
    "الوزارة": True,
    "الجهة التابعة للوزارة": False,
    "تاريخ الالتحاق بالعمل": True,
    "ما زلت أعمل في هذه الوظيفة": False,
    "تاريخ الانتهاء من العمل": False,
    "المسمى الوظيفي": True,
    "المستوى الوظيفي / الأقدمية": False,
    "القسم / الإدارة": False,
    "التخصص المهني": False,
    "وصف الوظيفة والمسؤوليات": False,
    "عنوان جهة العمل": False,
    "مجال العمل / طبيعة النشاط (أول)": False,
    "مجال العمل (ثانٍ": False,
    "اسم المرجع": False,
    "رقم هاتف المرجع": False,
    "البريد الإلكتروني للمرجع": False,
    "مكان العمل المشترك": False,
    "السجل المهني (Professional History)": False,
    "المنظمة / جهة العمل والقطاع": False,
    "تاريخ البدء (Start Date)": False,
    "تاريخ الانتهاء (End Date)": False,
    "المسؤوليات الرئيسية (Key Responsibilities)": False,
    "سبب ترك العمل (Reason for Leaving)": False,
    "ملخص البيانات المهنية (Professional Summary)": False,
    "المسمى الوظيفي الحالي (Current Job Title)": False,
    "سنوات الخبرة الإدارية": False,
    "حجم المنظمة (Organization Size)": False,
    "الميزانية السنوية المدارة": False,
    "عدد المرؤوسين المباشرين": False,
    "الخبرة العالمية (Global Experience": False,

    # Step 5 – skills & languages
    "المهارات التقنية (Technical Skills)": True,
    "مهارات الحاسب الآلي (Computer Skills)": True,
    "المهارات الشخصية (Soft Skills)": True,
    "مهارات أخرى (Other Skills)": False,
    "اللغة الأم (Mother Language)": True,
    "اللغة الثانية (الإنجليزية)": True,
    "لغات إضافية (حتى لغتين": False,
    "وصف الاهتمامات": True,
    "هل تستخدم وسائل التواصل الاجتماعي": True,
    "منصات التواصل (تشغيل": True,

    # Step 6 – prizes, conferences, misc
    "هل حصلت على أي جوائز أو تكريمات": True,
    "اسم الجائزة / التكريم": False,
    "تاريخ الحصول عليها": False,
    "فئة الجائزة": False,
    "الجهة المانحة": False,
    "تحميل صورة الشهادة (PDF أو صورة)": False,
    "هل شاركت في أي مؤتمرات أو ورش عمل": True,
    "اسم الفعالية": False,
    "الجهة المنظمة": False,
    "مستوى المشاركة": False,
    "الجوائز والتكريمات (Impact": False,
    "عنوان الجائزة / التكريم (Award": False,
    "الجهة المانحة (Issuing Body)": False,
    "الإنجاز الرئيسي (حتى 100 كلمة)": False,
    "القيادة المجتمعية / التطوع (Community": False,
    "الأنشطة اللاصفية (Extracurricular Depth)": False,
    "الدور (Role)": False,
    "مدة المشروع (Project Duration)": False,
    "منشورات / ملف أعمال (Publication": False,

    # Step 7 – public/political/legal
    "هل شاركت في أي عمل عام أو تطوعي": True,
    "اسم المؤسسة أو الجمعية الخيرية": True,
    "المنصب / الدور الوظيفي": True,
    "سنة / تاريخ الالتحاق": True,
    "سنة / تاريخ المغادرة": False,
    "نطاق العمل ووصف الخبرة": False,
    "مجال العمل": False,
    "دولة العمل": False,
    "هل شاركت في أي عمل سياسي": True,
}

# Quiz labels in step 9 — skip all (they are question text, not form field labels)
QUIZ_SKIP_SUBSTRINGS = [
    "تم تسليمك دليلاً",
    "When explaining a concept",
    "aha! moment",
    "A website performs poorly",
    "In a strategy game",
    "write a book",
    "sounds most like a compliment",
    "Deep work",
    "finishing a project",
]

def should_skip(txt):
    for s in QUIZ_SKIP_SUBSTRINGS:
        if s in txt:
            return True
    return False

def find_rule(txt):
    """Returns True (mandatory), False (optional), or None (skip)."""
    if should_skip(txt):
        return None
    for substr, mandatory in RULES.items():
        if substr in txt:
            return mandatory
    return None

# Match each <label> element that doesn't already have a marker
LABEL_ELEM_RE = re.compile(
    r'(<label(?![^>]*class=["\'][^"\']*(?:reg-btn|photo-upload-btn|identity-doc-option)[^"\']*["\'])[^>]*>)(.*?)(</label>)',
    re.DOTALL | re.IGNORECASE
)

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()

replaced = 0
misses = []

def replacer(m):
    global replaced
    open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
    txt = strip_tags(inner)
    if not txt or len(txt) < 3:
        return m.group(0)
    if MARKER_RE.search(txt):
        return m.group(0)  # already has marker
    # Skip if it wraps a file input or submit input
    if re.search(r'<input[^>]*type=["\'](?:file|submit|button|image|reset)["\']', inner, re.IGNORECASE):
        return m.group(0)
    rule = find_rule(txt)
    if rule is None:
        misses.append(txt[:70])
        return m.group(0)  # quiz question or unrecognised — skip
    marker = " (اجبارى)" if rule else " (اختيارى)"
    # Insert marker before </label>
    replaced += 1
    return open_tag + inner.rstrip() + marker + "\n" + close_tag

new_html = LABEL_ELEM_RE.sub(replacer, html)

html_path.write_bytes(new_html.encode("utf-8"))
print(f"Replaced {replaced} labels.")
if misses:
    print(f"\nNot matched ({len(misses)}) — no rule defined:")
    for m in misses:
        print(f"  • {m}")
