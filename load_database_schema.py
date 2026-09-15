#!/usr/bin/env python3
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # Read the database.sql file
    with open('database.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Connect to MySQL
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    
    cursor = conn.cursor(buffered=True)
    
    # Execute all SQL statements
    # Split by semicolon and execute each statement
    statements = sql_content.split(';')
    
    print("=" * 60)
    print("LOADING DATABASE SCHEMA")
    print("=" * 60)
    
    count = 0
    for statement in statements:
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
                count += 1
            except Exception as e:
                print(f"Error executing statement: {e}")
                print(f"Statement: {statement[:100]}...")
    
    conn.commit()
    print(f"\n✅ Successfully executed {count} SQL statements")
    
    # Verify student_points table
    cursor.execute("USE college_events_hub")
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'student_points' in tables:
        print("✅ student_points table created successfully")
    else:
        print("❌ student_points table still missing")
    
    print(f"\nTotal tables in database: {len(tables)}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
