#!/usr/bin/env python3
"""Complete test of all event-related routes."""

from app import app

def test_all_routes():
    """Test all routes comprehensively."""
    
    test_cases = [
        # Public routes
        ('/', {}, 'Home page'),
        ('/events', {}, 'Events list'),
        ('/leaderboard', {}, 'Leaderboard'),
        
        # Admin routes
        ('/admin', {'user_id': 1, 'role': 'admin'}, 'Admin dashboard'),
        ('/admin/event/new', {'user_id': 1, 'role': 'admin'}, 'Add event page'),
        ('/admin/analytics', {'user_id': 1, 'role': 'admin'}, 'Admin analytics'),
        
        # Student routes
        ('/student', {'user_id': 1, 'role': 'student'}, 'Student dashboard'),
        ('/notifications', {'user_id': 1, 'role': 'student'}, 'Notifications'),
        ('/wishlist', {'user_id': 1, 'role': 'student'}, 'Wishlist'),
    ]
    
    print('=' * 80)
    print('COMPLETE APPLICATION ROUTE TEST')
    print('=' * 80)
    
    all_passed = True
    
    for path, session_data, description in test_cases:
        try:
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess.clear()
                    sess.update(session_data)
                
                resp = client.get(path, follow_redirects=False)
                status = resp.status_code
                
                if status == 200:
                    print(f'✓ {path:30} => 200 OK      [{description}]')
                elif status in [301, 302]:
                    location = resp.headers.get('Location', 'N/A')
                    print(f'→ {path:30} => {status} REDIRECT [{description}]')
                    print(f'  └─ Location: {location}')
                else:
                    print(f'✗ {path:30} => {status} ERROR    [{description}]')
                    all_passed = False
                    # Print first 200 chars of error
                    err_msg = resp.get_data(as_text=True)[:200]
                    if err_msg:
                        print(f'  └─ Error: {err_msg.split(chr(10))[0]}')
        
        except Exception as e:
            print(f'✗ {path:30} => EXCEPTION  [{description}]')
            print(f'  └─ {str(e)[:100]}')
            all_passed = False
    
    print('=' * 80)
    if all_passed:
        print('✓ ALL TESTS PASSED')
    else:
        print('⚠ SOME TESTS FAILED - CHECK DETAILS ABOVE')
    print('=' * 80)

if __name__ == '__main__':
    test_all_routes()
