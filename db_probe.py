import mysql.connector
from app import db

conn = db()
cur = conn.cursor(dictionary=True)
cur.execute("SHOW TABLES")
print('TABLES:', [r[next(iter(r))] for r in cur.fetchall()])
for table in ['students','student_points','notifications']:
    try:
        cur.execute(f"SHOW CREATE TABLE `{table}`")
        rows = cur.fetchall()
        print('\nCREATE TABLE', table)
        for row in rows:
            print(row)
    except Exception as e:
        print('ERR TABLE', table, e)

cur.close()
conn.close()
