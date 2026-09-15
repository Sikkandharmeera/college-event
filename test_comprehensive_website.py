#!/usr/bin/env python3
"""Comprehensive website test - check all critical pages and routes."""

from app import app
import sys

def run_comprehensive_test():
    """Test all critical website routes and pages."""
    
    test_routes = [
        # Public pages
        ('/', {}, 'Home page'),
        ('/events', {}, 'Events listing'),
        ('/calendar', {}, 'Calendar page'),
        ('/leaderboard', {}, 'Public leaderboard'),
        ('/login', {}, 'Login page'),
        ('/register', {}, 'Registration page'),
        
        # Student pages
        ('/student', {'user_id': 1, 'role': 'student'}, 'Student dashboard'),
        ('/notifications', {'user_id': 1, 'role': 'student'}, 'Student notifications'),
        ('/wishlist', {'user_id': 1, 'role': 'student'}, 'Student wishlist'),
        
        # Admin pages
        ('/admin', {'user_id': 1, 'role': 'admin'}, 'Admin dashboard'),
        ('/admin/event/new', {'user_id': 1, 'role': 'admin'}, 'Add event page'),
        ('/admin/analytics', {'user_id': 1, 'role': 'admin'}, 'Admin analytics'),
        ('/admin/export/leaderboard', {'user_id': 1, 'role': 'admin'}, 'Export leaderboard'),
        
        # Coordinator pages (if exists)
        ('/coordinator', {'user_id': 2, 'role': 'coordinator'}, 'Coordinator dashboard'),
    ]
    
    print('\n' + '=' * 90)
    print('COMPREHENSIVE WEBSITE TEST - ALL CRITICAL PAGES')
    print('=' * 90)
    
    passed = 0
    failed = 0
    errors_detail = []
    
    for path, session_data, description in test_routes:
        try:
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess.clear()
                    if session_data:
                        sess.update(session_data)
                
                resp = client.get(path, follow_redirects=False)
                status = resp.status_code
                
                # Accept 200, 301, 302 (redirects for login)
                if status == 200:
                    print(f'✅ {path:35} [200 OK]      {description}')
                    passed += 1
                elif status in [301, 302]:
                    location = resp.headers.get('Location', 'N/A')
                    print(f'➡️  {path:35} [{status} REDIRECT] {description}')
                    print(f'    └─ Redirects to: {location}')
                    passed += 1
                elif status == 404:
                    print(f'⚠️  {path:35} [404 NOT FOUND] {description}')
                    failed += 1
                    errors_detail.append(f'{path} - 404 Not Found')
                else:
                    print(f'❌ {path:35} [{status} ERROR]   {description}')
                    failed += 1
                    errors_detail.append(f'{path} - HTTP {status}')
                    # Get error details
                    err_text = resp.get_data(as_text=True)[:300]
                    if err_text:
                        first_line = err_text.split('\n')[0]
                        print(f'    └─ Error: {first_line[:80]}')
        
        except Exception as e:
            print(f'❌ {path:35} [EXCEPTION]    {description}')
            print(f'    └─ {str(e)[:80]}')
            failed += 1
            errors_detail.append(f'{path} - Exception: {str(e)[:50]}')
    
    # Print summary
    print('=' * 90)
    print(f'RESULTS: {passed} passed | {failed} failed')
    print('=' * 90)
    
    if failed > 0:
        print('\n⚠️  FAILED TESTS:')
        for error in errors_detail:
            print(f'  • {error}')
        return False
    else:
        print('\n✅ ALL TESTS PASSED - WEBSITE IS READY!')
        return True

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
