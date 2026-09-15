#!/usr/bin/env python
"""
Comprehensive validation test for College Events Hub website
"""

import os
import sys

# Test 1: Verify Python files compile
print("=" * 60)
print("TEST 1: Python Syntax Validation")
print("=" * 60)

files_to_check = [
    'app.py',
    'test_database.py',
    'startup_check.py'
]

import py_compile

for file in files_to_check:
    try:
        py_compile.compile(file, doraise=True)
        print(f"✅ {file} - VALID")
    except py_compile.PyCompileError as e:
        print(f"❌ {file} - ERROR: {e}")
        sys.exit(1)

# Test 2: Check CSS files exist
print("\n" + "=" * 60)
print("TEST 2: CSS Files Check")
print("=" * 60)

css_files = [
    'static/css/custom.css',
    'static/css/style.css',
    'static/css/futuristic.css'
]

for file in css_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file} - EXISTS ({size} bytes)")
    else:
        print(f"❌ {file} - MISSING")

# Test 3: Check JavaScript files exist
print("\n" + "=" * 60)
print("TEST 3: JavaScript Files Check")
print("=" * 60)

js_files = [
    'static/js/script.js'
]

for file in js_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file} - EXISTS ({size} bytes)")
    else:
        print(f"❌ {file} - MISSING")

# Test 4: Check all HTML templates exist
print("\n" + "=" * 60)
print("TEST 4: HTML Templates Check")
print("=" * 60)

templates_dir = 'templates'
if os.path.isdir(templates_dir):
    templates = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
    print(f"✅ Found {len(templates)} templates:")
    for t in sorted(templates):
        print(f"   - {t}")
else:
    print(f"❌ Templates directory not found")

# Test 5: Check static folders exist
print("\n" + "=" * 60)
print("TEST 5: Static Folders Check")
print("=" * 60)

static_folders = [
    'static/css',
    'static/js',
    'static/images',
    'static/uploads',
    'static/uploads/events',
    'static/uploads/payments',
    'static/uploads/speakers',
    'static/uploads/certificates'
]

for folder in static_folders:
    if os.path.isdir(folder):
        print(f"✅ {folder} - EXISTS")
    else:
        print(f"⚠️  {folder} - MISSING (will be created at runtime)")

# Test 6: Verify requirements
print("\n" + "=" * 60)
print("TEST 6: Requirements Check")
print("=" * 60)

try:
    import flask
    print(f"✅ Flask - INSTALLED")
except ImportError:
    print(f"❌ Flask - NOT INSTALLED")

try:
    import mysql.connector
    print(f"✅ mysql.connector - INSTALLED")
except ImportError:
    print(f"❌ mysql.connector - NOT INSTALLED")

try:
    import werkzeug
    print(f"✅ Werkzeug - INSTALLED")
except ImportError:
    print(f"❌ Werkzeug - NOT INSTALLED")

try:
    import qrcode
    print(f"✅ qrcode - INSTALLED")
except ImportError:
    print(f"❌ qrcode - NOT INSTALLED")

print("\n" + "=" * 60)
print("VALIDATION COMPLETE ✅")
print("=" * 60)
