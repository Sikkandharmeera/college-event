import os
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'college_events_hub')
)
cur = conn.cursor()
cur.execute("SELECT email FROM staff WHERE role='admin' AND active=1 LIMIT 1")
row = cur.fetchone()
if row:
    print('EXISTING:' + row[0])
else:
    email = 'admin@collegeeventshub.com'
    password = 'Admin@1234'
    cur.execute(
        "INSERT INTO staff(full_name,email,password_hash,role,active) VALUES(%s,%s,%s,%s,%s)",
        ('System Admin', email, generate_password_hash(password), 'admin', 1)
    )
    conn.commit()
    print('CREATED:' + email + ':' + password)
cur.close()
conn.close()
