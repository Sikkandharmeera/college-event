COLLEGE EVENTS HUB - FINAL SETUP

1. Install Python 3.
2. Install MySQL Server + MySQL Workbench.
3. Open this folder in VS Code.
4. Open Terminal in VS Code.
5. Create virtual environment:
   python -m venv venv
6. Activate on Windows:
   venv\Scripts\activate
7. Install packages:
   pip install -r requirements.txt
8. In MySQL Workbench, open database.sql and Execute it.
9. Copy .env.example to .env and enter your MySQL password.
10. Create an admin:
   python create_staff.py
   Enter role: admin
11. Run:
   python app.py
12. Browser:
   http://127.0.0.1:5000

No browser extension is required.

IMPORTANT:
- Event content is stored in MySQL.
- Admin can add/edit/delete events from the dashboard.
- Coordinator can edit only assigned events.
- Students have separate accounts.
- Payment is a QR/UPI + UTR verification model, not a live payment gateway.
- Upload event images through the admin/coordinator forms.
