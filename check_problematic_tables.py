#!/usr/bin/env python3
"""
Check all tables needed for problematic routes
"""
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
    
    # Get all tables
    cursor.execute("SHOW TABLES")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print("=" * 80)
    print("CHECKING TABLES FOR PROBLEMATIC ROUTES")
    print("=" * 80)
    
    # Tables needed
    needed_tables = {
        'notifications': 'For /notifications route',
        'wishlist': 'For /wishlist route',
        'student_points': 'For /leaderboard route (admin & student)',
        'events': 'For event creation/edit',
        'categories': 'For event form dropdown',
        'sub_events': 'For event form dropdown',
        'staff': 'For event coordinator selection',
    }
    
    print("\nTable Status:")
    missing = []
    for table, purpose in needed_tables.items():
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table:20} ({count} records) - {purpose}")
        else:
            print(f"  ❌ {table:20} MISSING - {purpose}")
            missing.append(table)
    
    print("\n" + "=" * 80)
    if missing:
        print(f"❌ MISSING TABLES: {', '.join(missing)}")
    else:
        print("✅ All required tables exist!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
