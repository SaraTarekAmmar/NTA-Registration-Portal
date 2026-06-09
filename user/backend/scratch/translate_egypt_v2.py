import json
import re

univ_translations = {
    "6th of October Technological University": "جامعة 6 أكتوبر التكنولوجية",
    "Ahram Canadian University (ACU)": "جامعة الأهرام الكندية",
    "Ain Shams National University": "جامعة عين شمس الأهلية",
    "Ain Shams University": "جامعة عين شمس",
    "Akhbar El Yom Academy": "أكاديمية أخبار اليوم",
    "Al Azhar University": "جامعة الأزهر",
    "Al Hayah University": "جامعة الحياة",
    "Alamein International University (AIU)": "جامعة العلمين الدولية",
    "Alexandria National University": "جامعة الإسكندرية الأهلية",
    "Alexandria University": "جامعة الإسكندرية",
    "American University in Cairo": "الجامعة الأمريكية بالقاهرة",
    "Arab Academy for Science & Technology": "الأكاديمية العربية للعلوم والتكنولوجيا والنقل البحري",
    "Arab Open University": "الجامعة العربية المفتوحة",
    "Arish University": "جامعة العريش",
    "Assiut National University": "جامعة أسيوط الأهلية",
    "Assiut Technological University": "جامعة أسيوط التكنولوجية",
    "Assiut University": "جامعة أسيوط",
    "Aswan University": "جامعة أسوان",
    "Badr University in Assiut (BUA)": "جامعة بدر بأسيوط",
    "Badr University in Cairo": "جامعة بدر بالقاهرة",
    "Benha National University": "جامعة بنها الأهلية",
    "Benha University": "جامعة بنها",
    "Beni Suef Technological University": "جامعة بني سويف التكنولوجية",
    "Beni Suef University": "جامعة بني سويف",
    "Borg El Arab Technological University": "جامعة برج العرب التكنولوجية",
    "CIC - Canadian International College": "الكلية الكندية الدولية",
    "Cairo National University": "جامعة القاهرة الأهلية",
    "Cairo University": "جامعة القاهرة",
    "Damanhour University": "جامعة دمنهور",
    "Damietta University": "جامعة دمياط",
    "Delta Technological University": "جامعة الدلتا التكنولوجية",
    "Delta University for Science and Technology": "جامعة الدلتا للعلوم والتكنولوجيا",
    "Deraya University": "جامعة دراية",
    "ESLSCA Business School": "جامعة إسلسكا مصر",
    "East Port Said Technological University": "جامعة شرق بورسعيد التكنولوجية",
    "Egypt University of Informatics (EUI)": "جامعة مصر للمعلوماتية",
    "Egypt-Japan University of Science and Technology (E-JUST)": "الجامعة المصرية اليابانية للعلوم والتكنولوجيا",
    "Egyptian Chinese University (ECU)": "الجامعة المصرية الصينية",
    "Egyptian E-Learning University (EELU)": "الجامعة المصرية للتعلم الإلكتروني الأهلية",
    "Egyptian Russian University (ERU)": "الجامعة المصرية الروسية",
    "El Shorouk Academy": "أكاديمية الشروق",
    "European Universities in Egypt (EUE)": "الجامعات الأوروبية في مصر",
    "Fayoum University": "جامعة الفيوم",
    "Future University in Egypt (FUE)": "جامعة المستقبل",
    "Galala University (GU)": "جامعة الجلالة",
    "German International University (GIU)": "الجامعة الألمانية الدولية",
    "German University in Cairo": "الجامعة الألمانية بالقاهرة",
    "Heliopolis University": "جامعة هليوبوليس",
    "Helwan National University": "جامعة حلوان الأهلية",
    "Helwan University": "جامعة حلوان",
    "Hertfordshire University in Egypt (UH-GAF)": "جامعة هيرتفوردشاير بمصر",
    "Higher Technological Institute": "المعهد التكنولوجي العالي",
    "Horus University (HUE)": "جامعة حورس",
    "Ismailia National University": "جامعة الإسماعيلية الأهلية",
    "Kafr El-Sheikh University": "جامعة كفر الشيخ",
    "King Salman International University (KSIU)": "جامعة الملك سلمان الدولية",
    "Luxor University": "جامعة الأقصر",
    "Mansoura National University": "جامعة المنصورة الأهلية",
    "Mansoura University": "جامعة المنصورة",
    "Matrouh University": "جامعة مطروح",
    "Menoufia National University": "جامعة المنوفية الأهلية",
    "Menoufia University": "جامعة المنوفية",
    "Merit University": "جامعة ميريت",
    "Military Technical College": "الكلية الفنية العسكرية",
    "Minia National University": "جامعة المنيا الأهلية",
    "Minia Technological University": "جامعة المنيا التكنولوجية",
    "Minia University": "جامعة المنيا",
    "Misr International University": "جامعة مصر الدولية",
    "Misr University for Science and Technology": "جامعة مصر للعلوم والتكنولوجيا",
    "Modern Academy": "الأكاديمية الحديثة",
    "Modern Sciences & Arts University": "جامعة العلوم والآداب الحديثة (MSA)",
    "Modern University For Technology and Information": "الجامعة الحديثة للتكنولوجيا والمعلومات",
    "Nahda University (NUB)": "جامعة النهضة",
    "New Cairo Technological University": "جامعة القاهرة الجديدة التكنولوجية",
    "New Giza University (NGU)": "جامعة الجيزة الجديدة",
    "New Mansoura University (NMU)": "جامعة المنصورة الجديدة",
    "New Valley University": "جامعة الوادي الجديد",
    "Nile University": "جامعة النيل الأهلية",
    "October 6 university": "جامعة 6 أكتوبر",
    "Pharos University in Alexandria (PUA)": "جامعة فاروس بالإسكندرية",
    "Port Said University": "جامعة بورسعيد",
    "Sadat Academy for Management Sciences": "أكاديمية السادات للعلوم الإدارية",
    "Samanoud Technological University": "جامعة سمنود التكنولوجية",
    "Sinai University": "جامعة سيناء",
    "Sohag University": "جامعة سوهاج",
    "South Valley University": "جامعة جنوب الوادي",
    "Sphinx University": "جامعة سفنكس",
    "Suez Canal University": "جامعة قناة السويس",
    "Suez University": "جامعة السويس",
    "Tanta University": "جامعة طنطا",
    "The British University in Egypt (BUE)": "الجامعة البريطانية في مصر",
    "The Knowledge Hub Universities (TKH)": "جامعات المعرفة الدولية",
    "Thebes Technological University": "جامعة طيبة التكنولوجية",
    "Universities of Canada in Egypt (UCE)": "جامعات كندا في مصر",
    "University of Sadat City": "جامعة مدينة السادات",
    "Université Française d'Égypte": "الجامعة الفرنسية في مصر",
    "Université Senghor d'Alexandrie": "جامعة سنجور بالإسكندرية",
    "Zagazig National University": "جامعة الزقازيق الأهلية",
    "Zagazig University": "جامعة الزقازيق",
    "Zewail City of Science and Technology": "مدينة زويل للعلوم والتكنولوجيا"
}

def translate_college(name):
    # Mapping exact patterns
    patterns = [
        (r"(?i)\bFaculty of Medicine\b", "كلية الطب"),
        (r"(?i)\bFaculty of Engineering\b", "كلية الهندسة"),
        (r"(?i)\bFaculty of Pharmacy\b", "كلية الصيدلة"),
        (r"(?i)\bFaculty of Dentistry\b", "كلية طب الأسنان"),
        (r"(?i)\bFaculty of Physical Therapy\b", "كلية العلاج الطبيعي"),
        (r"(?i)\bFaculty of Science\b", "كلية العلوم"),
        (r"(?i)\bFaculty of Commerce\b", "كلية التجارة"),
        (r"(?i)\bFaculty of Law\b", "كلية الحقوق"),
        (r"(?i)\bFaculty of Arts\b", "كلية الآداب"),
        (r"(?i)\bFaculty of Agriculture\b", "كلية الزراعة"),
        (r"(?i)\bFaculty of Education\b", "كلية التربية"),
        (r"(?i)\bFaculty of Nursing\b", "كلية التمريض"),
        (r"(?i)\bFaculty of Veterinary Medicine\b", "كلية الطب البيطري"),
        (r"(?i)\bFaculty of Computer Science\b", "كلية علوم الحاسب"),
        (r"(?i)\bFaculty of Computers and Information\b", "كلية الحاسبات والمعلومات"),
        (r"(?i)\bFaculty of Media\b", "كلية الإعلام"),
        (r"(?i)\bFaculty of Mass Communication\b", "كلية الإعلام"),
        (r"(?i)\bFaculty of Languages & Translation\b", "كلية اللغات والترجمة"),
        (r"(?i)\bFaculty of Languages and Translation\b", "كلية اللغات والترجمة"),
        (r"(?i)\bFaculty of Languages\b", "كلية اللغات"),
        (r"(?i)\bFaculty of Al-Alsun\b", "كلية الألسن"),
        (r"(?i)\bFaculty of Archaeology\b", "كلية الآثار"),
        (r"(?i)\bFaculty of Fine Arts\b", "كلية الفنون الجميلة"),
        (r"(?i)\bFaculty of Applied Arts\b", "كلية الفنون التطبيقية"),
        (r"(?i)\bFaculty of Tourism & Hotels\b", "كلية السياحة والفنادق"),
        (r"(?i)\bFaculty of Tourism and Hotels\b", "كلية السياحة والفنادق"),
        (r"(?i)\bFaculty of Business Administration\b", "كلية إدارة الأعمال"),
        (r"(?i)\bFaculty of Business\b", "كلية إدارة الأعمال"),
        (r"(?i)\bFaculty of Economics & Political Science\b", "كلية الاقتصاد والعلوم السياسية"),
        (r"(?i)\bFaculty of Economics and Political Science\b", "كلية الاقتصاد والعلوم السياسية"),
        (r"(?i)\bFaculty of Oral and Dental Medicine\b", "كلية طب الفم والأسنان"),
        (r"(?i)\bFaculty of Dar Al-Ulum\b", "كلية دار العلوم"),
        (r"(?i)\bFaculty of Industry and Energy Technology\b", "كلية تكنولوجيا الصناعة والطاقة"),
        (r"(?i)\bFaculty of Industry and Energy\b", "كلية الصناعة والطاقة"),
        (r"(?i)\bFaculty of Social Work\b", "كلية الخدمة الاجتماعية"),
        (r"(?i)\bFaculty of Physical Education\b", "كلية التربية الرياضية"),
        (r"(?i)\bFaculty of Specific Education\b", "كلية التربية النوعية"),
        (r"(?i)\bFaculty of Kindergarten\b", "كلية رياض الأطفال"),
        (r"(?i)\bFaculty of Allied Medical Sciences\b", "كلية العلوم الطبية التطبيقية"),
        (r"(?i)\bFaculty of Allied Health Sciences\b", "كلية العلوم الصحية التطبيقية"),
        (r"(?i)\bFaculty of Health Sciences Technology\b", "كلية تكنولوجيا العلوم الصحية"),
        (r"(?i)\bFaculty of Management\b", "كلية الإدارة"),
        (r"(?i)\bFaculty of Informatics\b", "كلية المعلوماتية"),
        (r"(?i)\bFaculty of Information Technology\b", "كلية تكنولوجيا المعلومات"),
        (r"(?i)\bFaculty of Art and Design\b", "كلية الفنون والتصميم"),
        (r"(?i)\bFaculty of Design & Creative Arts\b", "كلية التصميم والفنون الإبداعية"),
        (r"(?i)\bFaculty of Design\b", "كلية التصميم"),
        (r"(?i)\bFaculty of Engineering & Technology\b", "كلية الهندسة والتكنولوجيا"),
        (r"(?i)\bFaculty of Engineering and Technology\b", "كلية الهندسة والتكنولوجيا"),
        (r"(?i)\bFaculty of Computers & Artificial Intelligence\b", "كلية الحاسبات والذكاء الاصطناعي"),
        (r"(?i)\bFaculty of Computers and Artificial Intelligence\b", "كلية الحاسبات والذكاء الاصطناعي"),
        (r"(?i)\bFaculty of Artificial Intelligence\b", "كلية الذكاء الاصطناعي"),
        (r"(?i)\bFaculty of Management Technology\b", "كلية تكنولوجيا الإدارة"),
        (r"(?i)\bFaculty of Biotechnology\b", "كلية التكنولوجيا الحيوية"),
        (r"(?i)\bFaculty of Human Sciences\b", "كلية العلوم الإنسانية"),
        (r"(?i)\bFaculty of Social Sciences\b", "كلية العلوم الاجتماعية")
    ]
    
    for pat, trans in patterns:
        if re.search(pat, name):
            return trans
    
    # Generic replacements
    res = name
    res = re.sub(r"(?i)\bFaculty of\b", "كلية", res)
    res = re.sub(r"(?i)\bSchool of\b", "مدرسة", res)
    res = re.sub(r"(?i)\bCollege of\b", "كلية", res)
    res = re.sub(r"(?i)\bDepartment of\b", "قسم", res)
    
    # Common departments/fields
    repls = {
        "Engineering": "الهندسة",
        "Medicine": "الطب",
        "Pharmacy": "الصيدلة",
        "Dentistry": "طب الأسنان",
        "Science": "العلوم",
        "Nursing": "التمريض",
        "Law": "الحقوق",
        "Arts": "الآداب",
        "Commerce": "التجارة",
        "Management": "الإدارة",
        "Business": "الأعمال",
        "Information Technology": "تكنولوجيا المعلومات",
        "Computer Science": "علوم الحاسب",
        "Computers": "الحاسبات",
        "Agriculture": "الزراعة",
        "Veterinary": "الطب البيطري",
        "Archaeology": "الآثار",
        "Languages": "اللغات",
        "Education": "التربية",
        "Mass Communication": "الإعلام",
        "Oral and Dental Medicine": "طب الفم والأسنان",
        "Fine Arts": "الفنون الجميلة",
        "Applied Arts": "الفنون التطبيقية",
        "Physical Therapy": "العلاج الطبيعي",
        "Tourism": "السياحة",
        "Hotels": "الفنادق",
        "Economics": "الاقتصاد",
        "Political Science": "العلوم السياسية",
        "Al-Alsun": "الألسن"
    }
    
    for eng, ara in repls.items():
        res = re.sub(r"\b" + eng + r"\b", ara, res)
        
    return res

def load_robust_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        pos = 0
        combined = []
        while pos < len(content):
            while pos < len(content) and content[pos].isspace():
                pos += 1
            if pos >= len(content):
                break
            try:
                obj, next_pos = decoder.raw_decode(content, pos)
                if isinstance(obj, list):
                    combined.extend(obj)
                else:
                    combined.append(obj)
                pos = next_pos
            except Exception as e:
                cleaned = content.replace("]\n[", ",").replace("]\r\n[", ",")
                return json.loads(cleaned)
        return combined

def main():
    data = load_robust_json('Egypt V2.json')
    translated = []
    
    for u in data:
        name_en = u.get('name')
        name_ar = univ_translations.get(name_en, name_en)
        colleges = u.get('colleges', [])
        
        translated_colleges = []
        for c in colleges:
            if not c:
                continue
            translated_colleges.append({
                "name_en": c,
                "name_ar": translate_college(c)
            })
            
        translated.append({
            "name": name_en,
            "name_ar": name_ar,
            "colleges": translated_colleges
        })
        
    with open('Egypt V2.json', 'w', encoding='utf-8') as f:
        json.dump(translated, f, ensure_ascii=False, indent=4)
        
    print("Translation completed and saved to Egypt V2.json!")

if __name__ == "__main__":
    main()
