#!/usr/bin/env python3
"""Test event routes for errors."""

from app import app

def test_routes():
    """Test all event-related routes."""
    
    test_cases = [
        ('/', {}, 'Home page'),
        ('/events', {}, 'Events list'),
        ('/admin/event/new', {'user_id': 1, 'role': 'admin'}, 'Add event page'),
    ]
    
    print('=' * 70)
    print('EVENT ROUTES TEST')
    print('=' * 70)
    
    for path, session_data, description in test_cases:
        try:
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess.clear()
                    sess.update(session_data)
                
                resp = client.get(path, follow_redirects=False)
                status = resp.status_code
                
                if status == 200:
                    result = '✓ OK'
                else:
                    result = f'✗ ERROR({status})'
                
                print(f'{path:30} {result:15} {description}')
                
                if status >= 400:
                    error_msg = resp.get_data(as_text=True)[:400]
                    print(f'  └─ Error Details:')
                    for line in error_msg.split('\n')[:3]:
                        if line.strip():
                            print(f'     {line.strip()}')
        
        except Exception as e:
            print(f'{path:30} ✗ EXCEPTION:     {description}')
            print(f'  └─ {str(e)[:100]}')
    
    print('=' * 70)

if __name__ == '__main__':
    test_routes()
