#!/usr/bin/env python3
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'college_events_hub')
)
cursor = conn.cursor()

cursor.execute('SHOW TABLES')
tables = [row[0] for row in cursor.fetchall()]

print('Checking for student_points table:')
if 'student_points' in tables:
    print('✅ student_points exists')
else:
    print('❌ student_points MISSING - This causes /leaderboard to fail')
    
print('\nAll tables:', ', '.join(sorted(tables)))

cursor.close()
conn.close()
