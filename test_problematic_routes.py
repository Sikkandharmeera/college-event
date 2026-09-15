#!/usr/bin/env python3
"""
Test all problematic routes reported by user
"""
import urllib.request
import urllib.error

routes_to_test = [
    # Student Dashboard Routes
    ('/notifications', 'Student Notifications'),
    ('/wishlist', 'Student Wishlist'),
    ('/leaderboard', 'Leaderboard'),
    
    # Admin Dashboard Routes
    ('/admin', 'Admin Dashboard'),
    ('/admin/event/new', 'Add Event Page'),
    ('/admin/analytics', 'Admin Analytics'),
]

print("=" * 80)
print("TESTING PROBLEMATIC ROUTES")
print("=" * 80)

for route, name in routes_to_test:
    try:
        r = urllib.request.urlopen(f'http://127.0.0.1:5000{route}')
        print(f"✅ {name:30} ({route:30}): HTTP {r.status}")
    except urllib.error.HTTPError as e:
        print(f"❌ {name:30} ({route:30}): HTTP {e.code}")
    except Exception as e:
        print(f"❌ {name:30} ({route:30}): {type(e).__name__}: {str(e)[:40]}")

print("=" * 80)
