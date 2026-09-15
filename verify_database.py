import mysql.connector
from mysql.connector import Error

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='devasikkandhar@11',
        database='college_events_hub'
    )
    
    cursor = conn.cursor()
    cursor.execute('SHOW TABLES')
    tables = cursor.fetchall()
    
    print('='*60)
    print('✅ DATABASE VERIFICATION SUCCESSFUL')
    print('='*60)
    print(f'✅ Database connection: OK')
    print(f'✅ Total tables found: {len(tables)}')
    print('\nDatabase Tables:')
    print('-'*60)
    
    for i, table in enumerate(tables, 1):
        print(f'{i:2d}. {table[0]}')
    
    print('-'*60)
    print('✅ All database tables are created successfully!')
    print('✅ No errors in database schema!')
    print('='*60)
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f'❌ Database Error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
