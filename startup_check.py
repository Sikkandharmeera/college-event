#!/usr/bin/env python3
import sys
import subprocess
import os

os.chdir(r'd:\CollegeEventsHub_FINAL')

print("=" * 80)
print("COLLEGE EVENTS HUB - STARTUP DIAGNOSTICS")
print("=" * 80)

# Test 1: Check Python imports
print("\n[1] Testing Python imports...")
try:
    from app import app
    print("✅ Flask app imported successfully")
except Exception as e:
    print(f"❌ Error importing app: {e}")
    sys.exit(1)

# Test 2: Check database connectivity
print("\n[2] Testing database connectivity...")
try:
    import mysql.connector
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='devasikkandhar@11'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"✅ MySQL connected successfully (Version: {version})")
    
    # Check if database exists
    cursor.execute("SHOW DATABASES LIKE 'college_events_hub'")
    if cursor.fetchone():
        print("✅ college_events_hub database exists")
    else:
        print("⚠️  college_events_hub database not found - need to create it")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Database connection error: {e}")

# Test 3: Check Flask routes
print("\n[3] Checking Flask routes...")
try:
    with app.app_context():
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        print(f"✅ Flask has {len(routes)} routes registered")
        print("\nTop 10 routes:")
        for route in sorted(routes)[:10]:
            print(f"   • {route}")
except Exception as e:
    print(f"❌ Error checking routes: {e}")

# Test 4: Flask configuration
print("\n[4] Flask configuration:")
print(f"   • App name: {app.name}")
print(f"   • Debug mode: {app.debug}")
print(f"   • Secret key: {'Set' if app.secret_key else 'Not set'}")

print("\n" + "=" * 80)
print("STARTUP DIAGNOSTICS COMPLETE")
print("=" * 80)
print("\nTo start the server, run:")
print("  python -m flask --app app run")
print("\nOr for debug mode:")
print("  python -m flask --app app run --debug")
print("\nThen access: http://localhost:5000")
print("=" * 80)
