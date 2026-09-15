#!/usr/bin/env python3
import os
import subprocess

os.chdir(r'd:\CollegeEventsHub_FINAL')

# Verify database.sql exists
if os.path.exists('database.sql'):
    print("✅ database.sql file exists")
    with open('database.sql', 'r') as f:
        lines = f.readlines()
        print(f"✅ File has {len(lines)} lines")
        
    # Count tables in SQL
    table_count = sum(1 for line in lines if 'CREATE TABLE' in line)
    print(f"✅ Found {table_count} CREATE TABLE statements")
    
    # Show first few lines
    print("\n✅ First 20 lines of database.sql:")
    print("=" * 80)
    for i, line in enumerate(lines[:20]):
        print(f"{i+1:3d}: {line.rstrip()}")
else:
    print("❌ database.sql not found")
