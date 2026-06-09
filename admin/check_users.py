import os, mysql.connector
from dotenv import load_dotenv
load_dotenv('database/.env')
db = mysql.connector.connect(host=os.getenv('DB_HOST','localhost'), user=os.getenv('DB_USER','root'), password=os.getenv('DB_PASSWORD',''), database=os.getenv('DB_NAME','nta_portal'))
cursor = db.cursor()
cursor.execute('SELECT email, national_id, role FROM users LIMIT 10')
for row in cursor.fetchall(): print(row)
cursor.close()
db.close()
