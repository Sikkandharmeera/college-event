#!/usr/bin/env python3
"""Test all website pages and save results to file."""

import urllib.request
import urllib.error
import time

def test_live_website():
    """Test the live website running on localhost."""
    
    routes = [
        ('/', 'Home page'),
        ('/events', 'Events listing'),
        ('/calendar', 'Calendar'),
        ('/leaderboard', 'Public leaderboard'),
        ('/login', 'Login page'),
        ('/register', 'Registration page'),
    ]
    
    results = []
    results.append('=' * 80)
    results.append('LIVE WEBSITE TEST RESULTS')
    results.append('=' * 80)
    results.append('')
    
    passed = 0
    failed = 0
    
    for path, description in routes:
        url = f'http://127.0.0.1:5000{path}'
        try:
            response = urllib.request.urlopen(url, timeout=5)
            status = response.status
            if status == 200:
                results.append(f'✅ {path:20} [{status}] {description}')
                passed += 1
            else:
                results.append(f'⚠️  {path:20} [{status}] {description}')
                failed += 1
            response.close()
        except urllib.error.HTTPError as e:
            results.append(f'❌ {path:20} [{e.code}] {description}')
            failed += 1
        except Exception as e:
            results.append(f'❌ {path:20} [ERROR] {description} - {str(e)[:40]}')
            failed += 1
    
    results.append('')
    results.append('=' * 80)
    results.append(f'SUMMARY: {passed} Passed | {failed} Failed')
    results.append('=' * 80)
    results.append('')
    
    if passed > 0 and failed == 0:
        results.append('✅ ALL TESTS PASSED - WEBSITE IS FULLY OPERATIONAL')
    elif passed > 0:
        results.append(f'⚠️  PARTIAL SUCCESS - {passed} pages working, {failed} need attention')
    else:
        results.append('❌ WEBSITE NOT RESPONDING - Check if server is running')
    
    results.append('')
    
    # Write results to file
    output = '\n'.join(results)
    with open('website_test_results.txt', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(output)

if __name__ == '__main__':
    time.sleep(2)  # Wait for server to be ready
    test_live_website()
