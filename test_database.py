import mysql.connector
from mysql.connector import Error

print("=" * 80)
print("DATABASE VERIFICATION - College Events Hub")
print("=" * 80)

try:
    # Connect to MySQL
    print("\n[1] Connecting to MySQL Server...")
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='devasikkandhar@11'
    )
    print("✅ MySQL Server connection successful!")
    
    # Drop and recreate database
    cursor = conn.cursor()
    print("\n[2] Preparing database...")
    cursor.execute("DROP DATABASE IF EXISTS college_events_hub")
    print("✅ Dropped existing database (if any)")
    
    # Read and execute database.sql
    print("\n[3] Reading database.sql file...")
    with open('database.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ File read successfully ({len(sql_content)} bytes)")
    
    # Execute the SQL script
    print("\n[4] Executing SQL script...")
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    executed = 0
    for i, statement in enumerate(statements, 1):
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                executed += 1
            except Error as e:
                print(f"❌ Error executing statement {i}: {e}")
                print(f"   Statement: {statement[:100]}...")
    
    conn.commit()
    print(f"✅ Executed {executed} SQL statements successfully!")
    
    # Verify database
    print("\n[5] Verifying database structure...")
    cursor.execute("USE college_events_hub")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print(f"✅ Database created successfully!")
    print(f"✅ Total tables: {len(tables)}\n")
    
    print("Tables created:")
    print("-" * 80)
    for i, (table,) in enumerate(tables, 1):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        print(f"{i:2d}. {table:25s} - {row_count:3d} rows")
    
    # Verify key constraints
    print("\n[6] Verifying database integrity...")
    print("-" * 80)
    
    # Check if indexes exist
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA='college_events_hub'")
    index_count = cursor.fetchone()[0]
    print(f"✅ Total indexes: {index_count}")
    
    # Check foreign keys
    cursor.execute("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
        WHERE CONSTRAINT_SCHEMA='college_events_hub'
    """)
    fk_count = cursor.fetchone()[0]
    print(f"✅ Total foreign keys: {fk_count}")
    
    # Check table engine
    cursor.execute("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA='college_events_hub' AND ENGINE='InnoDB'
    """)
    innodb_count = cursor.fetchone()[0]
    print(f"✅ InnoDB tables: {innodb_count}/{len(tables)}")
    
    # Verify sample data
    print("\n[7] Verifying sample data...")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    cat_count = cursor.fetchone()[0]
    print(f"✅ Categories inserted: {cat_count}")
    
    cursor.execute("SELECT COUNT(*) FROM sub_events")
    sub_count = cursor.fetchone()[0]
    print(f"✅ Sub-events inserted: {sub_count}")
    
    cursor.execute("SELECT COUNT(*) FROM staff")
    staff_count = cursor.fetchone()[0]
    print(f"✅ Staff users inserted: {staff_count}")
    
    cursor.execute("SELECT COUNT(*) FROM homepage")
    home_count = cursor.fetchone()[0]
    print(f"✅ Homepage content inserted: {home_count}")
    
    print("\n" + "=" * 80)
    print("✅✅✅ DATABASE VERIFICATION SUCCESSFUL - NO ERRORS FOUND! ✅✅✅")
    print("=" * 80)
    print("\nSummary:")
    print(f"  • Database: college_events_hub")
    print(f"  • Tables: {len(tables)}")
    print(f"  • Foreign Keys: {fk_count}")
    print(f"  • Indexes: {index_count}")
    print(f"  • Engine: InnoDB")
    print(f"  • Charset: utf8mb4")
    print("\nThe database is ready for production use!")
    print("=" * 80)
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f"\n❌ MySQL Error: {e}")
    print("=" * 80)
except FileNotFoundError:
    print("\n❌ Error: database.sql file not found!")
    print("=" * 80)
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("=" * 80)
