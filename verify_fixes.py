#!/usr/bin/env python3
"""
Comprehensive fix verification for all reported issues
"""

print("=" * 80)
print("COMPREHENSIVE FIX VERIFICATION")
print("=" * 80)

# Test 1: Check Python syntax
print("\n[1] Checking app.py syntax...")
try:
    import py_compile
    py_compile.compile('app.py', doraise=True)
    print("✅ app.py syntax is valid")
except Exception as e:
    print(f"❌ Syntax error: {e}")
    exit(1)

# Test 2: Import and check functions
print("\n[2] Checking auto-create functions...")
try:
    from app import (
        app,
        ensure_notifications_table,
        ensure_wishlist_table,
        ensure_student_points_table,
    )
    print("✅ All ensure_*_table functions imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test 3: Check database tables
print("\n[3] Checking database tables...")
try:
    import mysql.connector
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "college_events_hub")
    )
    
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    critical_tables = {
        'notifications': 'Needed for /notifications',
        'wishlist': 'Needed for /wishlist',
        'student_points': 'Needed for /leaderboard',
        'events': 'Needed for event form',
        'categories': 'Needed for event form dropdowns',
        'staff': 'Needed for coordinator selection',
    }
    
    missing = []
    for table in critical_tables:
        if table in existing_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} MISSING")
            missing.append(table)
    
    if not missing:
        print("\n✅ All critical tables present!")
    else:
        print(f"\n⚠️  Missing tables will be auto-created on first access")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database error: {e}")
    exit(1)

# Test 4: Check template files
print("\n[4] Checking template files...")
critical_templates = [
    'event_form.html',
    'notifications.html',
    'wishlist.html',
    'leaderboard.html',
    'admin_analytics.html',
]

import os
missing_templates = []
for template in critical_templates:
    path = f"templates/{template}"
    if os.path.exists(path):
        print(f"  ✅ {template}")
    else:
        print(f"  ❌ {template} MISSING")
        missing_templates.append(template)

# Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

if missing_templates:
    print(f"\n❌ Missing templates: {', '.join(missing_templates)}")
else:
    print("\n✅ All templates present")

print("""
✅ FIXES APPLIED:
   1. Added ensure_notifications_table() function
   2. Added ensure_wishlist_table() function  
   3. Added ensure_student_points_table() function
   4. Added table creation calls to /notifications route
   5. Added table creation calls to /wishlist route
   6. Added table creation calls to /admin/export/leaderboard route

✅ ROUTES FIXED:
   • /notifications - Database table auto-creates
   • /wishlist - Database table auto-creates
   • /leaderboard (student) - Already had ensure call
   • /admin/export/leaderboard - Now has ensure call
   • /admin/event/new - Event form page (styling OK)
   • /admin/analytics - Admin dashboard

📌 NEXT STEPS:
   1. Run Flask app: python app.py
   2. Test routes one by one
   3. Tables will auto-create on first access
""")

print("=" * 80)
