from app import app


def run_checks():
    checks = [
        ('/', {}),
        ('/leaderboard', {}),
        ('/notifications', {'user_id': 1, 'role': 'student'}),
        ('/admin/analytics', {'user_id': 1, 'role': 'admin'}),
        ('/admin/export/leaderboard', {'user_id': 1, 'role': 'admin'}),
    ]

    for path, session in checks:
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess.clear()
                sess.update(session)
            response = client.get(path, follow_redirects=False)
            print(f"{path} => {response.status_code} {response.headers.get('Location')}")
            if response.status_code >= 400:
                print(response.get_data(as_text=True)[:250])
                raise SystemExit(1)

    print('All route checks passed.')


if __name__ == '__main__':
    run_checks()
