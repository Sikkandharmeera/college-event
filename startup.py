#!/usr/bin/env python3
"""
Comprehensive College Events Hub Diagnostics and Startup
"""
import subprocess
import time
import sys
import os

print("=" * 80)
print("COLLEGE EVENTS HUB - COMPREHENSIVE DIAGNOSTICS AND STARTUP")
print("=" * 80)

# Step 1: Check database schema
print("\n[1] Checking database schema...")
os.system('python check_all_tables.py')

# Step 2: Restart Flask server
print("\n[2] Starting Flask server...")
print("=" * 80)
print("Flask server starting on http://127.0.0.1:5000")
print("=" * 80)

# Run Flask app
os.system('python app.py')
