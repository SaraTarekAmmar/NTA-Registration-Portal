import mysql.connector
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

# Setup password hashing (using pbkdf2_sha256 for pure-python compatibility on Windows)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def apply_defaults():
    # Load DB credentials from admin portal
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, 'backend', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print(f"Warning: .env not found at {env_path}, using defaults.")

    db_pass = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'nta_portal')
    db_user = os.getenv('DB_USER', 'root')
    db_host = os.getenv('DB_HOST', 'localhost')

    # Full profile for each staff/system account to INSERT on a fresh database.
    # ON DUPLICATE KEY UPDATE ensures only the password is refreshed if the row already exists.
    staff_accounts = [
        # ── Super Admin ──────────────────────────────────────────────────────
        {
            "full_name_ar": "Super Admin",
            "full_name_en": "Super Admin",
            "email": "superadmin@nta.edu.eg",
            "national_id": "10000000000000",
            "role": "superadmin",
            "dob": "1985-01-01",
            "gender": "male",
            "marital_status": "married",
            "password": "NTA@Super2026",
        },
        # ── Admin Portal Staff ───────────────────────────────────────────────
        {
            "full_name_ar": "مدير النظام",
            "full_name_en": "System Admin",
            "email": "admin@nta.edu.eg",
            "national_id": "29001011234567",
            "role": "admin",
            "dob": "1990-01-01",
            "gender": "male",
            "marital_status": "married",
            "password": "NTA@Admin2026",
        },
        {
            "full_name_ar": "محرر المحتوى",
            "full_name_en": "Content Editor",
            "email": "editor@nta.edu.eg",
            "national_id": "29505051234567",
            "role": "editor",
            "dob": "1995-05-05",
            "gender": "female",
            "marital_status": "single",
            "password": "NTA@Editor2026",
        },
        # ── Trainers ─────────────────────────────────────────────────────────
        {
            "full_name_ar": "غادة عبد اللطيف",
            "full_name_en": "Ghada Abdullatif",
            "email": "ghada.abdullatif@example.com",
            "national_id": "29404252103456",
            "role": "trainer",
            "dob": "1994-04-25",
            "gender": "female",
            "marital_status": "single",
            "password": "NTA@Trainer2026",
        },
        {
            "full_name_ar": "أحمد سعيد محمد",
            "full_name_en": "Ahmed Saeed Mohamed",
            "email": "trainer@nta.edu.eg",
            "national_id": "28501011234567",
            "role": "trainer",
            "dob": "1985-01-01",
            "gender": "male",
            "marital_status": "single",
            "password": "NTA@Trainer2026",
        },
        # ── Primary Test Trainees ─────────────────────────────────────────────
        {
            "full_name_ar": "محمد أحمد علي",
            "full_name_en": "Mohamed Ahmed Ali",
            "email": "trainee@example.com",
            "national_id": "29808081234567",
            "role": "trainee",
            "dob": "1998-08-08",
            "gender": "male",
            "marital_status": "single",
            "password": "NTA@Trainee2026",
        },
        {
            "full_name_ar": "أمل سيد حسن",
            "full_name_en": "Amal Sayed Hassan",
            "email": "amal@example.com",
            "national_id": "29901011234567",
            "role": "trainee",
            "dob": "1999-01-01",
            "gender": "female",
            "marital_status": "single",
            "password": "Pass@2024",
        },
        # ── Demo / Batch Trainees ─────────────────────────────────────────────
        {
            "full_name_ar": "عمر أحمد محمد",
            "full_name_en": "Omar Ahmed Mohamed",
            "email": "omar.ahmed.fake01@nta-test.eg",
            "national_id": "29203151000001",
            "role": "trainee",
            "dob": "1992-03-15",
            "gender": "male",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "فاطمة علي السيد",
            "full_name_en": "Fatima Ali El-Sayed",
            "email": "fatima.ali.fake02@nta-test.eg",
            "national_id": "29505031000002",
            "role": "trainee",
            "dob": "1995-05-03",
            "gender": "female",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "خالد إبراهيم النجار",
            "full_name_en": "Khaled Ibrahim El-Naggar",
            "email": "khaled.ibrahim.fake03@nta-test.eg",
            "national_id": "29808081000003",
            "role": "trainee",
            "dob": "1998-08-08",
            "gender": "male",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "رانيا يوسف البيطار",
            "full_name_en": "Rania Youssef El-Baytar",
            "email": "rania.youssef.fake13@nta-test.eg",
            "national_id": "29501301000013",
            "role": "trainee",
            "dob": "1995-01-30",
            "gender": "female",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "طارق سيد الباز",
            "full_name_en": "Tarek Sayed El-Baz",
            "email": "tarek.sayed.fake14@nta-test.eg",
            "national_id": "29207051000014",
            "role": "trainee",
            "dob": "1992-07-05",
            "gender": "male",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "منى عاطف زهران",
            "full_name_en": "Mona Atef Zahran",
            "email": "mona.atef.fake15@nta-test.eg",
            "national_id": "29604221000015",
            "role": "trainee",
            "dob": "1996-04-22",
            "gender": "female",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "باسم محمد الغزالي",
            "full_name_en": "Bassem Mohamed El-Ghazaly",
            "email": "bassem.m.fake16@nta-test.eg",
            "national_id": "29008171000016",
            "role": "trainee",
            "dob": "1990-08-17",
            "gender": "male",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "لبنى حسين الشناوي",
            "full_name_en": "Lobna Hussein El-Shinawi",
            "email": "lobna.hussein.fake17@nta-test.eg",
            "national_id": "29403071000017",
            "role": "trainee",
            "dob": "1994-03-07",
            "gender": "female",
            "marital_status": "single",
            "password": "Password123",
        },
        {
            "full_name_ar": "كريم عصام الدين فهمي",
            "full_name_en": "Karim Essam El-Din Fahmy",
            "email": "karim.essam.fake18@nta-test.eg",
            "national_id": "29109141000018",
            "role": "trainee",
            "dob": "1991-09-14",
            "gender": "male",
            "marital_status": "single",
            "password": "Password123",
        },
    ]

    # Upsert query:
    # - If email/national_id don't exist → INSERT a full new row
    # - If they already exist            → only UPDATE the password_hash
    upsert_query = """
        INSERT INTO users
            (full_name_ar, full_name_en, email, national_id, role, dob, gender, marital_status, password_hash)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            password_hash = VALUES(password_hash)
    """

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name
        )
        cursor = conn.cursor()

        for account in staff_accounts:
            hashed = pwd_context.hash(account["password"])
            cursor.execute(upsert_query, (
                account["full_name_ar"],
                account["full_name_en"],
                account["email"],
                account["national_id"],
                account["role"],
                account["dob"],
                account["gender"],
                account["marital_status"],
                hashed,
            ))
            print(f"[+] Upserted credentials for {account['email']}")

        conn.commit()
        cursor.close()
        conn.close()
        print("[SUCCESS] All default staff credentials applied.")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    apply_defaults()
