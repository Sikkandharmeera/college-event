#!/usr/bin/env python3
import re

# Read app.py and extract table references
with open('app.py', 'r') as f:
    content = f.read()

# Find all FROM/JOIN table references
pattern = r'(?m)^\s*(?:FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN)\s+(\w+)\b'
tables_used = sorted(set(re.findall(pattern, content)))
tables_used = [table for table in tables_used if table != 'information_schema']

print("=" * 60)
print("TABLES REFERENCED IN app.py")
print("=" * 60)

print("\nTables referenced:")
for table in tables_used:
    print(f"  • {table}")

print(f"\nTotal unique tables: {len(tables_used)}")

# Now check which ones exist in database
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'college_events_hub')
    )
    cursor = conn.cursor()
    
    cursor.execute('SHOW TABLES')
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print("\n" + "=" * 60)
    print("TABLE EXISTENCE CHECK")
    print("=" * 60)
    
    missing = []
    for table in tables_used:
        if table in existing_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} MISSING")
            missing.append(table)
    
    if missing:
        print(f"\n⚠️  Missing tables: {', '.join(missing)}")
    else:
        print("\n✅ All referenced tables exist!")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
