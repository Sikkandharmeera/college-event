import unittest

import app as app_module


class AdminPaymentFlowTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()
        self.original_q = app_module.q

    def tearDown(self):
        app_module.q = self.original_q

    def _login_admin(self):
        with self.client.session_transaction() as session:
            session['user_id'] = 1
            session['role'] = 'admin'
            session['name'] = 'System Admin'

    def test_payment_verification_page_lists_student_payment_details(self):
        self._login_admin()

        def fake_q(sql, p=(), fetch=False):
            if 'FROM payments p' in sql and 'JOIN students s' in sql:
                return [{
                    'id': 12,
                    'full_name': 'Alice Johnson',
                    'event_name': 'Tech Fest 2026',
                    'amount': '2500.00',
                    'receipt_path': 'uploads/payments/sample.pdf',
                    'status': 'Submitted',
                }]
            return []

        app_module.q = fake_q

        response = self.client.get('/admin/payments')
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('Alice Johnson', page)
        self.assertIn('Tech Fest 2026', page)
        self.assertIn('View Receipt', page)
        self.assertIn('Verify', page)

    def test_admin_can_download_registration_details_as_pdf(self):
        self._login_admin()

        def fake_q(sql, p=(), fetch=False):
            if 'FROM registrations' in sql and 'students' in sql:
                return [{
                    'id': 42,
                    'student_id': 7,
                    'event_id': 9,
                    'status': 'Pending',
                    'created_at': '2026-08-13 10:00:00',
                    'full_name': 'Alice Johnson',
                    'email': 'alice@example.com',
                    'mobile': '9876543210',
                    'register_number': '2024CS101',
                    'college_name': 'ABC College',
                    'department': 'Computer Science',
                    'course': 'B.Tech',
                    'year_semester': '2024-2025 / 3rd Year',
                    'event_name': 'Tech Fest 2026',
                    'event_date': '2026-09-20',
                    'venue': 'Main Auditorium',
                    'registration_fee': '2500.00',
                    'amount': '2500.00',
                    'receipt_path': 'uploads/payments/sample.pdf',
                }]
            return []

        app_module.q = fake_q

        response = self.client.get('/admin/registration/42/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertIn('attachment; filename=', response.headers.get('Content-Disposition', ''))

    def test_admin_can_download_event_registrations_as_pdf(self):
        self._login_admin()

        def fake_q(sql, p=(), fetch=False):
            if 'SELECT event_name' in sql and 'FROM events' in sql:
                return [{'event_name': 'Tech Fest 2026'}]
            if 'FROM registrations' in sql and 'JOIN students' in sql:
                return [{
                    'id': 42,
                    'full_name': 'Alice Johnson',
                    'email': 'alice@example.com',
                    'mobile': '9876543210',
                    'register_number': '2024CS101',
                    'college_name': 'ABC College',
                    'department': 'Computer Science',
                    'course': 'B.Tech',
                    'year_semester': '2024-2025 / 3rd Year',
                    'status': 'Pending',
                    'payment_status': 'Submitted',
                }]
            return []

        app_module.q = fake_q

        response = self.client.get('/admin/event/9/registrations/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertIn('attachment; filename=', response.headers.get('Content-Disposition', ''))

    def test_admin_can_download_all_registrations_as_pdf(self):
        self._login_admin()

        def fake_q(sql, p=(), fetch=False):
            if 'FROM registrations' in sql and 'JOIN students' in sql and 'JOIN events' in sql:
                return [{
                    'id': 42,
                    'full_name': 'Alice Johnson',
                    'email': 'alice@example.com',
                    'mobile': '9876543210',
                    'register_number': '2024CS101',
                    'college_name': 'ABC College',
                    'department': 'Computer Science',
                    'course': 'B.Tech',
                    'year_semester': '2024-2025 / 3rd Year',
                    'event_name': 'Tech Fest 2026',
                    'status': 'Confirmed',
                    'payment_status': 'Verified',
                    'amount': '2500.00',
                }]
            return []

        app_module.q = fake_q

        response = self.client.get('/admin/registrations/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertIn('attachment; filename=', response.headers.get('Content-Disposition', ''))

    def test_admin_can_download_all_registrations_as_csv(self):
        self._login_admin()

        def fake_q(sql, p=(), fetch=False):
            if 'FROM registrations' in sql and 'JOIN students' in sql and 'JOIN events' in sql:
                return [{
                    'id': 42,
                    'full_name': 'Alice Johnson',
                    'email': 'alice@example.com',
                    'mobile': '9876543210',
                    'register_number': '2024CS101',
                    'college_name': 'ABC College',
                    'department': 'Computer Science',
                    'course': 'B.Tech',
                    'event_name': 'Tech Fest 2026',
                    'event_date': '2026-09-20',
                    'registration_status': 'Confirmed',
                    'payment_status': 'Verified',
                    'amount': '2500.00',
                }]
            return []

        app_module.q = fake_q

        response = self.client.get('/admin/registrations/csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn('attachment; filename=', response.headers.get('Content-Disposition', ''))
        self.assertIn('Alice Johnson', response.get_data(as_text=True))

    def test_homepage_search_form_routes_to_event_listing(self):
        response = self.client.get('/events?q=tech')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Search', response.get_data(as_text=True))

    def test_student_event_registration_creates_registration_and_payment(self):
        with self.client.session_transaction() as session:
            session['user_id'] = 7
            session['role'] = 'student'
            session['name'] = 'Student One'

        def fake_q(sql, p=(), fetch=False):
            if 'FROM events' in sql and "status = 'Published'" in sql:
                return [{'id': 9, 'registration_fee': 150.00, 'status': 'Published'}]
            if 'SELECT id' in sql and 'FROM registrations' in sql:
                return []
            if 'INSERT INTO registrations' in sql:
                return 42
            if 'INSERT INTO payments' in sql:
                return 88
            return []

        app_module.q = fake_q

        response = self.client.post('/event/9/register', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/student/dashboard')

    def test_admin_event_form_is_visible_and_structured(self):
        self._login_admin()

        def fake_q(sql, p=(), fetch=False):
            if 'FROM categories' in sql:
                return [{'id': 1, 'name': 'Workshop'}]
            if 'FROM sub_events' in sql:
                return [{'id': 2, 'name': 'Coding'}]
            if 'FROM staff' in sql and "role='coordinator'" in sql:
                return [{'id': 3, 'full_name': 'Asha Rao'}]
            return []

        app_module.q = fake_q

        response = self.client.get('/admin/event/new')
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('Add Event', page)
        self.assertIn('Create a new event', page)


if __name__ == '__main__':
    unittest.main()
