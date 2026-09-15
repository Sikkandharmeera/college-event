#!/usr/bin/env python3
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "college_events_hub")
    )
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE SCHEMA CHECK")
    print("=" * 60)
    
    # Get all tables
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nTables in database ({len(tables)} total):")
    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  ✅ {table}: {count} records")
    
    # Check for key tables
    required_tables = ['users', 'events', 'categories', 'registrations', 'payments']
    print("\nRequired tables check:")
    for table in required_tables:
        if table in tables:
            print(f"  ✅ {table} exists")
        else:
            print(f"  ❌ {table} MISSING")
    
    print("\n" + "=" * 60)
    print("✅ Database connected successfully!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database error: {e}")
