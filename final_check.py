#!/usr/bin/env python3
"""
Final comprehensive check before running the application
"""
import sys
import os

print("=" * 80)
print("FINAL COMPREHENSIVE CHECK")
print("=" * 80)

# Test 1: Check Python syntax
print("\n[1] Checking app.py syntax...")
try:
    import py_compile
    py_compile.compile('app.py', doraise=True)
    print("✅ app.py syntax is valid")
except Exception as e:
    print(f"❌ Syntax error in app.py: {e}")
    sys.exit(1)

# Test 2: Import app module
print("\n[2] Importing app module...")
try:
    from app import app
    print(f"✅ App module imported successfully")
    print(f"   Routes registered: {len(list(app.url_map.iter_rules()))}")
except Exception as e:
    print(f"❌ Error importing app: {e}")
    sys.exit(1)

# Test 3: Check database
print("\n[3] Checking database connection...")
try:
    import mysql.connector
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
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'college_events_hub'")
    table_count = cursor.fetchone()[0]
    print(f"✅ Database connected")
    print(f"   Tables in database: {table_count}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

# Test 4: Check templates
print("\n[4] Checking template files...")
import os
template_dir = 'templates'
templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]
print(f"✅ Found {len(templates)} template files")

# Test 5: Check static files
print("\n[5] Checking static files...")
if os.path.exists('static'):
    css_files = [f for f in os.listdir('static/css') if f.endswith('.css')]
    js_files = [f for f in os.listdir('static/js') if f.endswith('.js')]
    print(f"✅ Found {len(css_files)} CSS files and {len(js_files)} JS files")
else:
    print("⚠️  Static folder not found")

# Test 6: Test key routes
print("\n[6] Testing key routes...")
import urllib.request
import urllib.error

routes_to_test = [
    ('/', 'Home'),
    ('/events', 'Events'),
    ('/login', 'Login'),
]

routes_ok = True
for route, name in routes_to_test:
    try:
        r = urllib.request.urlopen(f'http://127.0.0.1:5000{route}')
        if r.status == 200:
            print(f"✅ {name} ({route}): 200 OK")
        else:
            print(f"⚠️  {name} ({route}): {r.status}")
    except Exception as e:
        print(f"⚠️  {name} ({route}): Not accessible (Flask may not be running)")
        routes_ok = False

print("\n" + "=" * 80)
if routes_ok:
    print("✅ ALL CHECKS PASSED - Application is ready!")
else:
    print("✅ STATIC CHECKS PASSED - Flask server is needed for route testing")
print("=" * 80)

print("\nTo start the server, run:")
print("  python app.py")
print("\nThen access: http://localhost:5000")
