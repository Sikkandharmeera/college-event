#!/usr/bin/env python3
import urllib.request
import urllib.error

routes = [
    ('/', 'Home'),
    ('/events', 'Events'),
    ('/login', 'Login'),
    ('/register', 'Register'),
    ('/leaderboard', 'Leaderboard'),
    ('/calendar', 'Calendar'),
]

print("=" * 60)
print("ROUTE TESTING")
print("=" * 60)

for route, name in routes:
    try:
        r = urllib.request.urlopen(f'http://127.0.0.1:5000{route}')
        if r.status == 200:
            print(f"✅ {name:20} ({route:20}): 200 OK")
        else:
            print(f"⚠️  {name:20} ({route:20}): {r.status}")
    except urllib.error.HTTPError as e:
        print(f"❌ {name:20} ({route:20}): {e.code}")
    except Exception as e:
        print(f"❌ {name:20} ({route:20}): {str(e)}")

print("=" * 60)
print("✅ Route testing complete!")
