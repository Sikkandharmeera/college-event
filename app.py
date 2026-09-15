import os
import uuid
import csv
import re
from io import BytesIO, StringIO
from functools import wraps
from tempfile import gettempdir
from urllib.parse import quote_plus, unquote

from datetime import date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
    abort,
    send_from_directory
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import mysql.connector
import qrcode

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

# Vercel's deployed code directory is read-only. Keep the normal static
# assets in the deployment and put user uploads in writable temporary storage.
IS_VERCEL = bool(
    os.getenv("VERCEL")
    or os.getenv("VERCEL_ENV")
)
STATIC_ASSET_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static"
)

app = Flask(
    __name__,
    static_folder=None
)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

app.secret_key = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)

UPLOAD_ROOT = os.getenv(
    "UPLOAD_ROOT",
    os.path.join(gettempdir(), "college_events_hub_uploads")
    if IS_VERCEL
    else os.path.join(STATIC_ASSET_FOLDER, "uploads")
)

UPLOAD_FOLDER = UPLOAD_ROOT


def ensure_upload_folder(folder=None):
    """Create writable upload storage only when an upload is being saved."""
    target = UPLOAD_FOLDER
    if folder:
        target = os.path.join(UPLOAD_FOLDER, folder)
    os.makedirs(target, exist_ok=True)
    return target


@app.route("/static/<path:filename>")
def static_assets(filename):
    """Serve bundled assets and the current instance's temporary uploads."""
    if filename == "uploads" or filename.startswith("uploads/"):
        upload_name = filename.removeprefix("uploads/")
        return send_from_directory(UPLOAD_FOLDER, upload_name)

    return send_from_directory(STATIC_ASSET_FOLDER, filename)


# ============================================================
# PAYMENT CONFIGURATION
# ============================================================

MERCHANT_UPI_ID = os.getenv(
    "MERCHANT_UPI_ID",
    "collegeevents@upi"
)

MERCHANT_UPI_NAME = os.getenv(
    "MERCHANT_UPI_NAME",
    "College Events Hub"
)


# ============================================================
# DEFAULT ADMIN
# ============================================================

DEFAULT_ADMIN_EMAIL = os.getenv(
    "DEFAULT_ADMIN_EMAIL",
    "admin@collegeeventshub.com"
)

DEFAULT_ADMIN_PASSWORD = os.getenv(
    "DEFAULT_ADMIN_PASSWORD",
    "Admin@1234"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def db():
    """
    Create and return a MySQL database connection.
    """

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME")

    if IS_VERCEL and not all([db_host, db_user, db_name]):
        raise RuntimeError(
            "DB_HOST, DB_USER, and DB_NAME must be configured on Vercel."
        )

    return mysql.connector.connect(
        host=db_host or "localhost",
        port=int(db_port),
        user=db_user or "root",
        password=db_password,
        database=db_name or "college_events_hub"
    )


# ============================================================
# DATABASE QUERY HELPER
# ============================================================

def q(sql, params=(), fetch=False):
    """
    Execute a SQL query.

    fetch=True  -> returns rows
    fetch=False -> returns last inserted ID
    """

    connection = db()
    cursor = connection.cursor(
        dictionary=True
    )

    try:
        cursor.execute(sql, params)

        if fetch:
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid

        connection.commit()

        return result

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ============================================================
# DATABASE SCHEMA HELPERS
# ============================================================

def ensure_homepage_table():

    q(
        """
        CREATE TABLE IF NOT EXISTS homepage (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hero_small VARCHAR(255) DEFAULT NULL,
            hero_title VARCHAR(255) DEFAULT NULL,
            hero_description TEXT DEFAULT NULL,
            hero_button_text VARCHAR(100) DEFAULT NULL,
            hero_button_link VARCHAR(255) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        )
        """
    )


def ensure_payment_upi_column():

    existing = q(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'payments'
        AND COLUMN_NAME = 'upi_id'
        """,
        fetch=True
    )

    if not existing:

        q(
            """
            ALTER TABLE payments
            ADD COLUMN upi_id VARCHAR(120)
            DEFAULT NULL
            """
        )


def ensure_payment_receipt_column():

    existing = q(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'payments'
        AND COLUMN_NAME = 'receipt_path'
        """,
        fetch=True
    )

    if not existing:

        q(
            """
            ALTER TABLE payments
            ADD COLUMN receipt_path VARCHAR(255)
            DEFAULT NULL
            """
        )


def ensure_payment_schema():

    ensure_payment_upi_column()
    ensure_payment_receipt_column()


def ensure_student_points_table():

    q(
        """
        CREATE TABLE IF NOT EXISTS student_points (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            points INT NOT NULL DEFAULT 0,
            total_events INT NOT NULL DEFAULT 0,
            attended_events INT NOT NULL DEFAULT 0,
            `rank` INT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_student_points_student (student_id),
            KEY idx_student_points_points (points),
            KEY idx_student_points_rank (`rank`),
            CONSTRAINT fk_student_points_student
                FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        ) ENGINE=InnoDB
          DEFAULT CHARSET=utf8mb4
          COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_wishlist_table():

    q(
        """
        CREATE TABLE IF NOT EXISTS wishlist (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            event_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_wishlist_student_event (student_id, event_id),
            KEY idx_wishlist_student (student_id),
            KEY idx_wishlist_event (event_id),
            CONSTRAINT fk_wishlist_student
                FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            CONSTRAINT fk_wishlist_event
                FOREIGN KEY (event_id)
                REFERENCES events(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        ) ENGINE=InnoDB
          DEFAULT CHARSET=utf8mb4
          COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_notifications_table():

    q(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            event_id INT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            `type` ENUM('reminder', 'update', 'feedback', 'announcement', 'registration')
                NOT NULL DEFAULT 'reminder',
            read_status TINYINT(1) NOT NULL DEFAULT 0,
            notification_date DATETIME NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_notifications_student (student_id),
            KEY idx_notifications_event (event_id),
            KEY idx_notifications_read (read_status),
            KEY idx_notifications_type (`type`),
            CONSTRAINT fk_notifications_student
                FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        ) ENGINE=InnoDB
          DEFAULT CHARSET=utf8mb4
          COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_registrations_table():
    """Auto-create registrations table with proper schema."""
    try:
        q(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                student_id INT UNSIGNED NOT NULL,
                event_id INT UNSIGNED NOT NULL,
                status ENUM(
                    'Pending',
                    'Confirmed',
                    'Cancelled',
                    'Attended',
                    'No-Show'
                ) NOT NULL DEFAULT 'Pending',
                registration_number VARCHAR(100) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_registration_number (registration_number),
                UNIQUE KEY uq_student_event (student_id, event_id),
                KEY idx_registrations_student (student_id),
                KEY idx_registrations_event (event_id),
                KEY idx_registrations_status (status),
                KEY idx_registrations_created (created_at),
                CONSTRAINT fk_registrations_student
                    FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                CONSTRAINT fk_registrations_event
                    FOREIGN KEY (event_id)
                    REFERENCES events(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            ) ENGINE=InnoDB
              DEFAULT CHARSET=utf8mb4
              COLLATE=utf8mb4_unicode_ci
            """
        )
    except Exception as e:
        print(f"[AUTO-FIX] Error creating registrations table: {str(e)}")


def ensure_payments_table():
    """Auto-create payments table with proper schema."""
    try:
        q(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                registration_id INT UNSIGNED NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                utr VARCHAR(120) NULL,
                upi_id VARCHAR(120) NULL,
                receipt_path VARCHAR(255) NULL,
                payment_method ENUM(
                    'upi',
                    'card',
                    'razorpay',
                    'bank_transfer',
                    'cash'
                ) NOT NULL DEFAULT 'upi',
                razorpay_order_id VARCHAR(255) NULL,
                razorpay_payment_id VARCHAR(255) NULL,
                razorpay_signature VARCHAR(255) NULL,
                status ENUM(
                    'Pending',
                    'Submitted',
                    'Verified',
                    'Rejected',
                    'Refunded'
                ) NOT NULL DEFAULT 'Pending',
                notes TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                verified_by INT UNSIGNED NULL,
                verified_at TIMESTAMP NULL DEFAULT NULL,
                UNIQUE KEY uq_payment_registration (registration_id),
                KEY idx_payments_status (status),
                KEY idx_payments_method (payment_method),
                KEY idx_payments_created (created_at),
                KEY idx_payments_verified_by (verified_by),
                CONSTRAINT fk_payments_registration
                    FOREIGN KEY (registration_id)
                    REFERENCES registrations(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                CONSTRAINT fk_payments_verified_by
                    FOREIGN KEY (verified_by)
                    REFERENCES staff(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE
            ) ENGINE=InnoDB
              DEFAULT CHARSET=utf8mb4
              COLLATE=utf8mb4_unicode_ci
            """
        )
    except Exception as e:
        print(f"[AUTO-FIX] Error creating payments table: {str(e)}")


def ensure_attendance_table():
    """Auto-create attendance table with proper schema."""
    try:
        q(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                registration_id INT UNSIGNED NOT NULL,
                attended TINYINT(1) NOT NULL DEFAULT 0,
                check_in_time TIMESTAMP NULL DEFAULT NULL,
                check_out_time TIMESTAMP NULL DEFAULT NULL,
                marked_by INT UNSIGNED NULL,
                marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_attendance_registration (registration_id),
                KEY idx_attendance_marked_by (marked_by),
                KEY idx_attendance_marked_at (marked_at),
                CONSTRAINT fk_attendance_registration
                    FOREIGN KEY (registration_id)
                    REFERENCES registrations(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                CONSTRAINT fk_attendance_staff
                    FOREIGN KEY (marked_by)
                    REFERENCES staff(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE
            ) ENGINE=InnoDB
              DEFAULT CHARSET=utf8mb4
              COLLATE=utf8mb4_unicode_ci
            """
        )
    except Exception as e:
        print(f"[AUTO-FIX] Error creating attendance table: {str(e)}")


def ensure_certificates_table():
    """Auto-create certificates table with proper schema."""
    try:
        q(
            """
            CREATE TABLE IF NOT EXISTS certificates (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                registration_id INT UNSIGNED NOT NULL,
                certificate_number VARCHAR(100) NOT NULL,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path VARCHAR(255) NULL,
                certificate_code VARCHAR(100) NULL,
                verified TINYINT(1) NOT NULL DEFAULT 0,
                UNIQUE KEY uq_certificate_registration (registration_id),
                UNIQUE KEY uq_certificate_number (certificate_number),
                KEY idx_certificate_code (certificate_code),
                CONSTRAINT fk_certificates_registration
                    FOREIGN KEY (registration_id)
                    REFERENCES registrations(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            ) ENGINE=InnoDB
              DEFAULT CHARSET=utf8mb4
              COLLATE=utf8mb4_unicode_ci
            """
        )
    except Exception as e:
        print(f"[AUTO-FIX] Error creating certificates table: {str(e)}")


def ensure_all_tables():
    """Initialize all required database tables."""
    try:
        ensure_homepage_table()
        ensure_payment_upi_column()
        ensure_payment_receipt_column()
        ensure_payment_schema()
        ensure_student_points_table()
        ensure_wishlist_table()
        ensure_notifications_table()
        ensure_registrations_table()
        ensure_payments_table()
        ensure_attendance_table()
        ensure_certificates_table()
        print("[AUTO-FIX] All database tables initialized successfully")
    except Exception as e:
        print(f"[AUTO-FIX] Error during table initialization: {str(e)}")


# ============================================================
# AUTHENTICATION DECORATOR
# ============================================================

def auth(role=None):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if not session.get("user_id"):

                return redirect(
                    url_for("login")
                )

            if role and session.get("role") != role:

                flash(
                    "Access denied.",
                    "error"
                )

                return redirect(
                    url_for("home")
                )

            return function(
                *args,
                **kwargs
            )

        return wrapper

    return decorator


# ============================================================
# FILE UPLOAD
# ============================================================

def save_file(file, folder):

    if not file:
        return None

    if not file.filename:
        return None

    filename = (
        uuid.uuid4().hex
        + "_"
        + secure_filename(file.filename)
    )

    ensure_upload_folder(folder)

    file_path = os.path.join(
        UPLOAD_FOLDER,
        folder,
        filename
    )

    file.save(file_path)

    return f"uploads/{folder}/{filename}"


# ============================================================
# UPI PAYMENT LINK
# ============================================================

def build_upi_link(
    upi_id,
    amount,
    payee_name=None,
    note=None
):

    if not upi_id:
        return None

    params = {
        "pa": upi_id,
        "cu": "INR"
    }

    if payee_name:
        params["pn"] = payee_name

    if amount is not None:
        params["am"] = f"{float(amount):.2f}"

    if note:
        params["tn"] = note

    query_string = "&".join(
        f"{key}={quote_plus(str(value))}"
        for key, value in params.items()
    )

    return f"upi://pay?{query_string}"


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    ensure_homepage_table()
    ensure_payment_schema()

    categories = q(
        """
        SELECT *
        FROM categories
        ORDER BY name
        """,
        fetch=True
    )

    events = q(
        """
        SELECT
            e.*,
            c.name AS category_name,
            s.name AS sub_event_name

        FROM events e

        JOIN categories c
            ON c.id = e.category_id

        LEFT JOIN sub_events s
            ON s.id = e.sub_event_id

        WHERE e.status = 'Published'

        ORDER BY
            e.event_date,
            e.event_time

        LIMIT 12
        """,
        fetch=True
    )

    homepage_rows = q(
        """
        SELECT *
        FROM homepage
        LIMIT 1
        """,
        fetch=True
    )

    homepage_data = (
        homepage_rows[0]
        if homepage_rows
        else None
    )

    return render_template(
        "index.html",
        categories=categories,
        events=events,
        home=homepage_data
    )


# ============================================================
# EVENTS
# ============================================================

@app.route("/events")
def event_list():

    category_id = request.args.get(
        "category_id",
        type=int
    )

    search = request.args.get(
        "q",
        ""
    ).strip()

    categories = q(
        """
        SELECT *
        FROM categories
        ORDER BY name
        """,
        fetch=True
    )

    base_query = """
        SELECT
            e.*,
            c.name AS category_name,
            s.name AS sub_event_name

        FROM events e

        JOIN categories c
            ON c.id = e.category_id

        LEFT JOIN sub_events s
            ON s.id = e.sub_event_id

        WHERE e.status IN ('Published', 'Draft')
    """

    params = []

    if category_id:

        base_query += """
            AND e.category_id = %s
        """

        params.append(category_id)

    if search:

        base_query += """
            AND (
                e.event_name LIKE %s
                OR e.description LIKE %s
                OR c.name LIKE %s
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])

    base_query += """
        ORDER BY
            e.event_date,
            e.event_time
    """

    events = q(
        base_query,
        tuple(params),
        fetch=True
    )

    return render_template(
        "events.html",
        events=events,
        categories=categories,
        search=search
    )


# ============================================================
# EVENT DETAILS
# ============================================================

@app.route("/event/<int:eid>")
def event_detail(eid):

    event_rows = q(
        """
        SELECT
            e.*,
            c.name AS category_name,
            s.name AS sub_event_name

        FROM events e

        JOIN categories c
            ON c.id = e.category_id

        LEFT JOIN sub_events s
            ON s.id = e.sub_event_id

        WHERE e.id = %s
        AND e.status IN ('Published', 'Draft')
        """,
        (eid,),
        fetch=True
    )

    if not event_rows:

        return "Event not found", 404

    event = event_rows[0]

    rules = q(
        """
        SELECT *
        FROM event_rules
        WHERE event_id = %s
        """,
        (eid,),
        fetch=True
    )

    speakers = q(
        """
        SELECT *
        FROM speakers
        WHERE event_id = %s
        """,
        (eid,),
        fetch=True
    )

    schedule = q(
        """
        SELECT *
        FROM schedules
        WHERE event_id = %s
        ORDER BY start_time
        """,
        (eid,),
        fetch=True
    )

    prizes = q(
        """
        SELECT *
        FROM prizes
        WHERE event_id = %s
        """,
        (eid,),
        fetch=True
    )

    return render_template(
        "event_detail.html",
        event=event,
        rules=rules,
        speakers=speakers,
        schedule=schedule,
        prizes=prizes
    )


# ============================================================
# STUDENT REGISTRATION
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        form = request.form

        required_fields = [
            "full_name",
            "mobile",
            "email",
            "register_number",
            "college_name",
            "department",
            "course",
            "year_semester",
            "password"
        ]

        if not all(
            form.get(field, "").strip()
            for field in required_fields
        ):

            flash(
                "Please fill all fields.",
                "error"
            )

            return render_template(
                "register.html"
            )

        existing = q(
            """
            SELECT id
            FROM students
            WHERE email = %s
            OR register_number = %s
            """,
            (
                form["email"],
                form["register_number"]
            ),
            fetch=True
        )

        if existing:

            flash(
                "Email or register number already exists.",
                "error"
            )

            return render_template(
                "register.html"
            )

        password_hash = generate_password_hash(
            form["password"]
        )

        q(
            """
            INSERT INTO students (
                full_name,
                mobile,
                email,
                register_number,
                college_name,
                department,
                course,
                year_semester,
                password_hash
            )

            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            """,
            (
                form["full_name"],
                form["mobile"],
                form["email"],
                form["register_number"],
                form["college_name"],
                form["department"],
                form["course"],
                form["year_semester"],
                password_hash
            )
        )

        flash(
            "Student account created successfully.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    role_hint = request.args.get(
        "role",
        ""
    ).lower()

    login_hint = None

    if role_hint == "admin":

        login_hint = (
            "Use your admin credentials to continue."
        )

    elif role_hint == "coordinator":

        login_hint = (
            "Use your coordinator credentials to continue."
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # -------------------------------
        # STUDENT LOGIN
        # -------------------------------

        students = q(
            """
            SELECT *
            FROM students
            WHERE email = %s
            """,
            (email,),
            fetch=True
        )

        if students:

            student = students[0]

            if check_password_hash(
                student["password_hash"],
                password
            ):

                session.clear()

                session.update(
                    user_id=student["id"],
                    name=student["full_name"],
                    role="student"
                )

                return redirect(
                    url_for("student_dashboard")
                )

        # -------------------------------
        # STAFF LOGIN
        # -------------------------------

        staff = q(
            """
            SELECT *
            FROM staff
            WHERE email = %s
            AND active = 1
            """,
            (email,),
            fetch=True
        )

        if staff:

            member = staff[0]

            if check_password_hash(
                member["password_hash"],
                password
            ):

                session.clear()

                session.update(
                    user_id=member["id"],
                    name=member["full_name"],
                    role=member["role"]
                )

                if member["role"] == "admin":

                    return redirect(
                        url_for("admin_dashboard")
                    )

                return redirect(
                    url_for("coordinator_dashboard")
                )

        # -------------------------------
        # DEFAULT ADMIN LOGIN
        # -------------------------------

        if (
            email == DEFAULT_ADMIN_EMAIL
            and password == DEFAULT_ADMIN_PASSWORD
        ):

            session.clear()

            session.update(
                user_id=1,
                name="System Admin",
                role="admin"
            )

            return redirect(
                url_for("admin_dashboard")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template(
        "login.html",
        login_hint=login_hint
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/student")
@app.route("/student/dashboard")
@auth("student")
def student_dashboard():

    registrations = q(
        """
        SELECT
            r.id,
            r.status,
            e.id AS event_id,
            e.event_name,
            e.event_date,
            e.venue,
            e.registration_fee,
            p.status AS payment_status

        FROM registrations r

        JOIN events e
            ON e.id = r.event_id

        LEFT JOIN payments p
            ON p.registration_id = r.id

        WHERE r.student_id = %s

        ORDER BY r.created_at DESC
        """,
        (session["user_id"],),
        fetch=True
    )

    return render_template(
        "student_dashboard.html",
        registrations=registrations
    )


# ============================================================
# REGISTER FOR EVENT
# ============================================================

@app.route(
    "/event/<int:eid>/register",
    methods=["POST"]
)
@auth("student")
def register_event(eid):

    events = q(
        """
        SELECT *
        FROM events
        WHERE id = %s
        AND status = 'Published'
        """,
        (eid,),
        fetch=True
    )

    if not events:

        return "Event not found", 404

    already_registered = q(
        """
        SELECT id
        FROM registrations
        WHERE student_id = %s
        AND event_id = %s
        """,
        (
            session["user_id"],
            eid
        ),
        fetch=True
    )

    if already_registered:

        flash(
            "You are already registered for this event.",
            "error"
        )

        return redirect(
            url_for(
                "event_detail",
                eid=eid
            )
        )

    registration_id = q(
        """
        INSERT INTO registrations (
            student_id,
            event_id
        )

        VALUES (%s,%s)
        """,
        (
            session["user_id"],
            eid
        )
    )

    fee = float(
        events[0]["registration_fee"] or 0
    )

    if fee > 0:

        q(
            """
            INSERT INTO payments (
                registration_id,
                amount
            )

            VALUES (%s,%s)
            """,
            (
                registration_id,
                fee
            )
        )

    else:

        q(
            """
            UPDATE registrations
            SET status = 'Confirmed'
            WHERE id = %s
            """,
            (registration_id,)
        )

    flash(
        "Registration successful.",
        "success"
    )

    return redirect(
        url_for("student_dashboard")
    )


# ============================================================
# MULTIPLE EVENT REGISTRATION
# ============================================================

@app.route(
    "/events/checkout",
    methods=["POST"]
)
@auth("student")
def checkout_events():

    selected = [
        int(event_id)
        for event_id in request.form.getlist("event_ids")
        if event_id.isdigit()
    ]

    if not selected:

        flash(
            "Select at least one event.",
            "error"
        )

        return redirect(
            url_for("event_list")
        )

    placeholders = ",".join(
        ["%s"] * len(selected)
    )

    params = [
        session["user_id"]
    ] + selected

    existing = q(
        f"""
        SELECT e.event_name

        FROM registrations r

        JOIN events e
            ON e.id = r.event_id

        WHERE r.student_id = %s
        AND r.event_id IN ({placeholders})
        """,
        tuple(params),
        fetch=True
    )

    if existing:

        names = ", ".join(
            item["event_name"]
            for item in existing
        )

        flash(
            f"Already registered for: {names}",
            "error"
        )

        return redirect(
            url_for("event_list")
        )

    events = q(
        f"""
        SELECT *
        FROM events

        WHERE id IN ({placeholders})
        AND status = 'Published'
        """,
        tuple(selected),
        fetch=True
    )

    if len(events) != len(selected):

        flash(
            "Some selected events are unavailable.",
            "error"
        )

        return redirect(
            url_for("event_list")
        )

    registration_ids = []

    for event in events:

        registration_id = q(
            """
            INSERT INTO registrations (
                student_id,
                event_id
            )

            VALUES (%s,%s)
            """,
            (
                session["user_id"],
                event["id"]
            )
        )

        fee = float(
            event["registration_fee"] or 0
        )

        if fee > 0:

            q(
                """
                INSERT INTO payments (
                    registration_id,
                    amount
                )

                VALUES (%s,%s)
                """,
                (
                    registration_id,
                    fee
                )
            )

            registration_ids.append(
                registration_id
            )

        else:

            q(
                """
                UPDATE registrations
                SET status = 'Confirmed'
                WHERE id = %s
                """,
                (registration_id,)
            )

    if registration_ids:

        return redirect(
            url_for(
                "checkout_payment",
                rids=",".join(
                    str(rid)
                    for rid in registration_ids
                )
            )
        )

    flash(
        "Registration successful for selected free events.",
        "success"
    )

    return redirect(
        url_for("student_dashboard")
    )


# ============================================================
# PAYMENT CHECKOUT
# ============================================================

@app.route("/payment/checkout")
@auth("student")
def checkout_payment():

    raw_ids = request.args.get(
        "rids",
        ""
    )

    registration_ids = [
        int(item)
        for item in raw_ids.split(",")
        if item.isdigit()
    ]

    if not registration_ids:

        flash(
            "No payments to process.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    placeholders = ",".join(
        ["%s"] * len(registration_ids)
    )

    params = registration_ids + [
        session["user_id"]
    ]

    payments = q(
        f"""
        SELECT
            p.id,
            p.registration_id,
            p.amount,
            p.status,
            e.event_name,
            e.event_date,
            e.venue,
            e.registration_fee,
            e.qr_image

        FROM payments p

        JOIN registrations r
            ON r.id = p.registration_id

        JOIN events e
            ON e.id = r.event_id

        WHERE p.registration_id IN ({placeholders})
        AND r.student_id = %s
        AND p.status IN ('Pending','Rejected')
        """,
        tuple(params),
        fetch=True
    )

    if not payments:

        flash(
            "No pending payments found.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    total = sum(
        float(payment["amount"] or 0)
        for payment in payments
    )

    qr_images = []

    for payment in payments:

        qr_image = payment.get(
            "qr_image"
        )

        if (
            qr_image
            and qr_image not in qr_images
        ):

            qr_images.append(
                qr_image
            )

    upi_link = build_upi_link(
        MERCHANT_UPI_ID,
        total,
        MERCHANT_UPI_NAME,
        "College Events Hub registration"
    )

    return render_template(
        "checkout.html",
        payments=payments,
        total=total,
        registration_ids=",".join(
            str(rid)
            for rid in registration_ids
        ),
        qr_images=qr_images,
        merchant_upi_id=MERCHANT_UPI_ID,
        upi_link=upi_link
    )


# ============================================================
# PAYMENT SUBMISSION - MULTIPLE
# ============================================================

@app.route(
    "/payment/launch",
    methods=["POST"]
)
@auth("student")
def payment_launch_batch():

    raw_ids = request.form.get(
        "registration_ids",
        ""
    )

    registration_ids = [
        int(item)
        for item in raw_ids.split(",")
        if item.isdigit()
    ]

    if not registration_ids:

        flash(
            "No payments selected.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    receipt_file = request.files.get(
        "receipt"
    )

    if (
        not receipt_file
        or not receipt_file.filename
    ):

        flash(
            "Please upload a payment receipt.",
            "error"
        )

        return redirect(
            url_for(
                "checkout_payment",
                rids=",".join(
                    str(rid)
                    for rid in registration_ids
                )
            )
        )

    receipt_path = save_file(
        receipt_file,
        "payments"
    )

    placeholders = ",".join(
        ["%s"] * len(registration_ids)
    )

    params = [
        MERCHANT_UPI_ID,
        receipt_path
    ] + registration_ids + [
        session["user_id"]
    ]

    q(
        f"""
        UPDATE payments p

        JOIN registrations r
            ON r.id = p.registration_id

        SET
            p.upi_id = %s,
            p.receipt_path = %s,
            p.status = 'Submitted'

        WHERE p.registration_id IN ({placeholders})
        AND r.student_id = %s
        AND p.status IN ('Pending','Rejected')
        """,
        tuple(params)
    )

    payments = q(
        f"""
        SELECT
            p.id,
            p.registration_id,
            p.amount,
            e.event_name,
            e.qr_image

        FROM payments p

        JOIN registrations r
            ON r.id = p.registration_id

        JOIN events e
            ON e.id = r.event_id

        WHERE p.registration_id IN ({placeholders})
        AND r.student_id = %s
        """,
        tuple(
            registration_ids
            + [session["user_id"]]
        ),
        fetch=True
    )

    qr_images = []

    for payment in payments:

        image = payment.get(
            "qr_image"
        )

        if image and image not in qr_images:
            qr_images.append(image)

    return render_template(
        "receipt_submitted.html",
        payments=payments,
        receipt_path=receipt_path,
        qr_images=qr_images
    )


# ============================================================
# PAYMENT SUBMISSION - SINGLE
# ============================================================

@app.route(
    "/payment/launch/<int:rid>",
    methods=["POST"]
)
@auth("student")
def payment_launch(rid):

    receipt_file = request.files.get(
        "receipt"
    )

    if (
        not receipt_file
        or not receipt_file.filename
    ):

        flash(
            "Please upload a payment receipt.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    receipt_path = save_file(
        receipt_file,
        "payments"
    )

    q(
        """
        UPDATE payments p

        JOIN registrations r
            ON r.id = p.registration_id

        SET
            p.upi_id = %s,
            p.receipt_path = %s,
            p.status = 'Submitted'

        WHERE p.registration_id = %s
        AND r.student_id = %s
        """,
        (
            MERCHANT_UPI_ID,
            receipt_path,
            rid,
            session["user_id"]
        )
    )

    payment = q(
        """
        SELECT
            p.id,
            p.amount,
            e.event_name,
            e.qr_image

        FROM payments p

        JOIN registrations r
            ON r.id = p.registration_id

        JOIN events e
            ON e.id = r.event_id

        WHERE p.registration_id = %s
        AND r.student_id = %s
        """,
        (
            rid,
            session["user_id"]
        ),
        fetch=True
    )

    if not payment:

        flash(
            "Payment cannot be submitted.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    qr_images = []

    if payment[0].get("qr_image"):
        qr_images.append(
            payment[0]["qr_image"]
        )

    return render_template(
        "receipt_submitted.html",
        payments=payment,
        receipt_path=receipt_path,
        qr_images=qr_images
    )


# ============================================================
# PAYMENT ROOT
# ============================================================

@app.route("/payment")
@auth("student")
def payment_root():

    flash(
        "Use the Events checkout page to submit payment.",
        "info"
    )

    return redirect(
        url_for("student_dashboard")
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@auth("admin")
def admin_dashboard():

    total_students = q(
        "SELECT COUNT(*) AS n FROM students",
        fetch=True
    )[0]["n"]

    total_events = q(
        "SELECT COUNT(*) AS n FROM events",
        fetch=True
    )[0]["n"]

    total_registrations = q(
        "SELECT COUNT(*) AS n FROM registrations",
        fetch=True
    )[0]["n"]

    submitted_payments = q(
        """
        SELECT COUNT(*) AS n
        FROM payments
        WHERE status = 'Submitted'
        """,
        fetch=True
    )[0]["n"]

    stats = [
        total_students,
        total_events,
        total_registrations,
        submitted_payments
    ]

    if submitted_payments > 0:

        flash(
            f"{submitted_payments} payment(s) require verification.",
            "info"
        )

    events = q(
        """
        SELECT
            e.*,
            c.name AS category_name,
            st.full_name AS coordinator_name

        FROM events e

        JOIN categories c
            ON c.id = e.category_id

        LEFT JOIN staff st
            ON st.id = e.coordinator_id

        ORDER BY e.created_at DESC
        """,
        fetch=True
    )

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        events=events
    )


# ============================================================
# ADMIN HOME PAGE EDITOR
# ============================================================

@app.route(
    "/admin/home",
    methods=["GET", "POST"]
)
@auth("admin")
def admin_home():

    rows = q(
        """
        SELECT *
        FROM homepage
        LIMIT 1
        """,
        fetch=True
    )

    homepage = (
        rows[0]
        if rows
        else None
    )

    if request.method == "POST":

        form = request.form

        data = (
            form.get("hero_small"),
            form.get("hero_title"),
            form.get("hero_description"),
            form.get("hero_button_text"),
            form.get("hero_button_link") or None
        )

        if homepage:

            q(
                """
                UPDATE homepage

                SET
                    hero_small = %s,
                    hero_title = %s,
                    hero_description = %s,
                    hero_button_text = %s,
                    hero_button_link = %s,
                    updated_at = CURRENT_TIMESTAMP

                WHERE id = %s
                """,
                data + (
                    homepage["id"],
                )
            )

        else:

            q(
                """
                INSERT INTO homepage (
                    hero_small,
                    hero_title,
                    hero_description,
                    hero_button_text,
                    hero_button_link
                )

                VALUES (%s,%s,%s,%s,%s)
                """,
                data
            )

        flash(
            "Home page content updated.",
            "success"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "home_form.html",
        home=homepage
    )


# ============================================================
# ADMIN CREATE EVENT
# ============================================================

@app.route(
    "/admin/event/new",
    methods=["GET", "POST"]
)
@auth("admin")
def event_new():

    if request.method == "POST":

        return save_event()

    return render_template(
        "event_form.html",
        event=None,
        categories=q(
            "SELECT * FROM categories ORDER BY name",
            fetch=True
        ),
        subs=q(
            "SELECT * FROM sub_events ORDER BY name",
            fetch=True
        ),
        staff=q(
            """
            SELECT id, full_name
            FROM staff
            WHERE role = 'coordinator'
            AND active = 1
            ORDER BY full_name
            """,
            fetch=True
        ),
        rules=[]
    )


# ============================================================
# ADMIN EDIT EVENT
# ============================================================

@app.route(
    "/admin/event/<int:eid>/edit",
    methods=["GET", "POST"]
)
@auth("admin")
def event_edit(eid):

    events = q(
        """
        SELECT *
        FROM events
        WHERE id = %s
        """,
        (eid,),
        fetch=True
    )

    if not events:

        return "Event not found", 404

    if request.method == "POST":

        return save_event(eid)

    return render_template(
        "event_form.html",
        event=events[0],
        categories=q(
            "SELECT * FROM categories ORDER BY name",
            fetch=True
        ),
        subs=q(
            "SELECT * FROM sub_events ORDER BY name",
            fetch=True
        ),
        staff=q(
            """
            SELECT id, full_name
            FROM staff
            WHERE role = 'coordinator'
            AND active = 1
            ORDER BY full_name
            """,
            fetch=True
        ),
        rules=q(
            """
            SELECT rule_text
            FROM event_rules
            WHERE event_id = %s
            """,
            (eid,),
            fetch=True
        )
    )


# ============================================================
# SAVE EVENT
# ============================================================

def save_event(eid=None):

    form = request.form

    category_id = form.get(
        "category_id"
    )

    event_name = form.get(
        "event_name",
        ""
    ).strip()

    if not category_id:

        flash(
            "Please select a category.",
            "error"
        )

        if eid:
            return redirect(
                url_for(
                    "event_edit",
                    eid=eid
                )
            )

        return redirect(
            url_for("event_new")
        )

    if not event_name:

        flash(
            "Event name is required.",
            "error"
        )

        if eid:
            return redirect(
                url_for(
                    "event_edit",
                    eid=eid
                )
            )

        return redirect(
            url_for("event_new")
        )

    old_event = None

    if eid:

        old_rows = q(
            """
            SELECT *
            FROM events
            WHERE id = %s
            """,
            (eid,),
            fetch=True
        )

        if old_rows:
            old_event = old_rows[0]

    banner = (
        save_file(
            request.files.get("banner"),
            "events"
        )
        or form.get("old_banner")
        or (
            old_event.get("banner")
            if old_event
            else None
        )
    )

    image = (
        save_file(
            request.files.get("image"),
            "events"
        )
        or form.get("old_image")
        or (
            old_event.get("image")
            if old_event
            else None
        )
    )

    qr_image = (
        save_file(
            request.files.get("qr_image"),
            "events"
        )
        or form.get("old_qr_image")
        or (
            old_event.get("qr_image")
            if old_event
            else None
        )
    )

    data = (
        category_id,
        form.get("sub_event_id") or None,
        form.get("coordinator_id") or None,
        event_name,
        form.get("description"),
        form.get("event_date") or None,
        form.get("event_time") or None,
        form.get("registration_deadline") or None,
        form.get("venue"),
        form.get("registration_fee") or 0,
        qr_image,
        banner,
        image,
        form.get("status", "Published")  # Default to Published for immediate visibility
    )

    if eid:

        q(
            """
            UPDATE events

            SET
                category_id = %s,
                sub_event_id = %s,
                coordinator_id = %s,
                event_name = %s,
                description = %s,
                event_date = %s,
                event_time = %s,
                registration_deadline = %s,
                venue = %s,
                registration_fee = %s,
                qr_image = %s,
                banner = %s,
                image = %s,
                status = %s

            WHERE id = %s
            """,
            data + (eid,)
        )

        q(
            """
            DELETE FROM event_rules
            WHERE event_id = %s
            """,
            (eid,)
        )

    else:

        eid = q(
            """
            INSERT INTO events (
                category_id,
                sub_event_id,
                coordinator_id,
                event_name,
                description,
                event_date,
                event_time,
                registration_deadline,
                venue,
                registration_fee,
                qr_image,
                banner,
                image,
                status
            )

            VALUES (
                %s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s
            )
            """,
            data
        )

    for rule in form.getlist("rules"):

        if rule and rule.strip():

            q(
                """
                INSERT INTO event_rules (
                    event_id,
                    rule_text
                )

                VALUES (%s,%s)
                """,
                (
                    eid,
                    rule.strip()
                )
            )

    flash(
        "Event saved successfully.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# DELETE EVENT
# ============================================================

@app.route(
    "/admin/event/<int:eid>/delete",
    methods=["POST"]
)
@auth("admin")
def event_delete(eid):

    q(
        """
        DELETE FROM events
        WHERE id = %s
        """,
        (eid,)
    )

    flash(
        "Event deleted.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# ADMIN PAYMENTS
# ============================================================

@app.route("/admin/payments")
@auth("admin")
def payments():

    ensure_payment_schema()

    rows = q(
        """
        SELECT
            p.*,
            s.full_name,
            e.event_name,
            e.venue,
            e.event_date,
            e.registration_fee,
            r.id AS registration_id,
            r.status AS registration_status

        FROM payments p

        JOIN registrations r
            ON r.id = p.registration_id

        JOIN students s
            ON s.id = r.student_id

        JOIN events e
            ON e.id = r.event_id

        ORDER BY p.created_at DESC
        """,
        fetch=True
    )

    return render_template(
        "payments.html",
        payments=rows
    )


# ============================================================
# VERIFY / REJECT PAYMENT
# ============================================================

@app.route(
    "/admin/payment/<int:pid>/<action>",
    methods=["POST"]
)
@auth("admin")
def payment_action(pid, action):

    if action == "verify":

        status = "Verified"

    elif action == "reject":

        status = "Rejected"

    else:

        flash(
            "Invalid payment action.",
            "error"
        )

        return redirect(
            url_for("payments")
        )

    q(
        """
        UPDATE payments
        SET status = %s
        WHERE id = %s
        """,
        (
            status,
            pid
        )
    )

    if status == "Verified":

        q(
            """
            UPDATE registrations r

            JOIN payments p
                ON p.registration_id = r.id

            SET r.status = 'Confirmed'

            WHERE p.id = %s
            """,
            (pid,)
        )

    return redirect(
        url_for("payments")
    )


# ============================================================
# COORDINATOR DASHBOARD
# ============================================================

@app.route("/coordinator")
@auth("coordinator")
def coordinator_dashboard():

    events = q(
        """
        SELECT
            e.*,
            c.name AS category_name

        FROM events e

        JOIN categories c
            ON c.id = e.category_id

        WHERE e.coordinator_id = %s

        ORDER BY e.event_date
        """,
        (session["user_id"],),
        fetch=True
    )

    return render_template(
        "coordinator_dashboard.html",
        events=events
    )


# ============================================================
# COORDINATOR EDIT EVENT
# ============================================================

@app.route(
    "/coordinator/event/<int:eid>/edit",
    methods=["GET", "POST"]
)
@auth("coordinator")
def coordinator_edit(eid):

    events = q(
        """
        SELECT *
        FROM events
        WHERE id = %s
        AND coordinator_id = %s
        """,
        (
            eid,
            session["user_id"]
        ),
        fetch=True
    )

    if not events:

        return "Event not assigned to you", 403

    event = events[0]

    if request.method == "POST":

        form = request.form

        banner = (
            save_file(
                request.files.get("banner"),
                "events"
            )
            or form.get("old_banner")
            or event.get("banner")
        )

        q(
            """
            UPDATE events

            SET
                event_name = %s,
                description = %s,
                event_date = %s,
                event_time = %s,
                registration_deadline = %s,
                venue = %s,
                registration_fee = %s,
                banner = %s,
                status = %s

            WHERE id = %s
            """,
            (
                form.get("event_name"),
                form.get("description"),
                form.get("event_date") or None,
                form.get("event_time") or None,
                form.get("registration_deadline") or None,
                form.get("venue"),
                form.get("registration_fee") or 0,
                banner,
                form.get("status", "Draft"),
                eid
            )
        )

        q(
            """
            DELETE FROM event_rules
            WHERE event_id = %s
            """,
            (eid,)
        )

        for rule in form.getlist("rules"):

            if rule.strip():

                q(
                    """
                    INSERT INTO event_rules (
                        event_id,
                        rule_text
                    )

                    VALUES (%s,%s)
                    """,
                    (
                        eid,
                        rule.strip()
                    )
                )

        flash(
            "Assigned event updated.",
            "success"
        )

        return redirect(
            url_for(
                "coordinator_dashboard"
            )
        )

    return render_template(
        "coordinator_edit.html",
        event=event,
        rules=q(
            """
            SELECT *
            FROM event_rules
            WHERE event_id = %s
            """,
            (eid,),
            fetch=True
        )
    )


# ============================================================
# ADMIN - STUDENTS
# ============================================================

@app.route("/admin/students")
@auth("admin")
def admin_students():

    students = q(
        """
        SELECT
            id,
            full_name,
            email,
            register_number,
            college_name,
            department,
            course,
            year_semester

        FROM students

        ORDER BY full_name
        """,
        fetch=True
    )

    return render_template(
        "admin_students.html",
        students=students
    )


@app.route(
    "/admin/student/<int:sid>/delete",
    methods=["POST"]
)
@auth("admin")
def admin_student_delete(sid):

    q(
        """
        DELETE FROM students
        WHERE id = %s
        """,
        (sid,)
    )

    flash(
        "Student removed.",
        "success"
    )

    return redirect(
        url_for("admin_students")
    )


# ============================================================
# ADMIN - COORDINATORS
# ============================================================

@app.route("/admin/coordinators")
@auth("admin")
def admin_coordinators():

    staff = q(
        """
        SELECT
            id,
            full_name,
            email,
            role,
            active

        FROM staff

        WHERE role = 'coordinator'

        ORDER BY full_name
        """,
        fetch=True
    )

    return render_template(
        "admin_coordinators.html",
        staff=staff
    )


@app.route(
    "/admin/coordinator/new",
    methods=["GET", "POST"]
)
@auth("admin")
def admin_coordinator_new():

    if request.method == "POST":

        form = request.form

        if (
            not form.get("full_name")
            or not form.get("email")
            or not form.get("password")
        ):

            flash(
                "Fill all required fields.",
                "error"
            )

            return render_template(
                "admin_coordinator_form.html",
                staff=None
            )

        q(
            """
            INSERT INTO staff (
                full_name,
                email,
                password_hash,
                role,
                active
            )

            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                form["full_name"],
                form["email"],
                generate_password_hash(
                    form["password"]
                ),
                "coordinator",
                1
            )
        )

        flash(
            "Coordinator created.",
            "success"
        )

        return redirect(
            url_for("admin_coordinators")
        )

    return render_template(
        "admin_coordinator_form.html",
        staff=None
    )


@app.route(
    "/admin/coordinator/<int:sid>/edit",
    methods=["GET", "POST"]
)
@auth("admin")
def admin_coordinator_edit(sid):

    rows = q(
        """
        SELECT *
        FROM staff
        WHERE id = %s
        """,
        (sid,),
        fetch=True
    )

    if not rows:

        return "Coordinator not found", 404

    staff = rows[0]

    if request.method == "POST":

        form = request.form

        active = (
            1
            if form.get("active") == "on"
            else 0
        )

        if form.get("password"):

            q(
                """
                UPDATE staff

                SET
                    full_name = %s,
                    email = %s,
                    password_hash = %s,
                    active = %s

                WHERE id = %s
                """,
                (
                    form["full_name"],
                    form["email"],
                    generate_password_hash(
                        form["password"]
                    ),
                    active,
                    sid
                )
            )

        else:

            q(
                """
                UPDATE staff

                SET
                    full_name = %s,
                    email = %s,
                    active = %s

                WHERE id = %s
                """,
                (
                    form["full_name"],
                    form["email"],
                    active,
                    sid
                )
            )

        flash(
            "Coordinator updated.",
            "success"
        )

        return redirect(
            url_for("admin_coordinators")
        )

    return render_template(
        "admin_coordinator_form.html",
        staff=staff
    )


@app.route(
    "/admin/coordinator/<int:sid>/delete",
    methods=["POST"]
)
@auth("admin")
def admin_coordinator_delete(sid):

    q(
        """
        DELETE FROM staff
        WHERE id = %s
        """,
        (sid,)
    )

    flash(
        "Coordinator removed.",
        "success"
    )

    return redirect(
        url_for("admin_coordinators")
    )


# ============================================================
# WISHLIST
# ============================================================

@app.route(
    "/wishlist/add/<int:eid>",
    methods=["POST"]
)
@auth("student")
def wishlist_add(eid):

    event = q(
        """
        SELECT id
        FROM events
        WHERE id = %s
        AND status = 'Published'
        """,
        (eid,),
        fetch=True
    )

    if event:

        existing = q(
            """
            SELECT id
            FROM wishlist
            WHERE student_id = %s
            AND event_id = %s
            """,
            (
                session["user_id"],
                eid
            ),
            fetch=True
        )

        if not existing:

            q(
                """
                INSERT INTO wishlist (
                    student_id,
                    event_id
                )

                VALUES (%s,%s)
                """,
                (
                    session["user_id"],
                    eid
                )
            )

            flash(
                "Event added to wishlist.",
                "success"
            )

        else:

            flash(
                "Already in wishlist.",
                "info"
            )

    return redirect(
        url_for(
            "event_detail",
            eid=eid
        )
    )


@app.route(
    "/wishlist/remove/<int:eid>",
    methods=["POST"]
)
@auth("student")
def wishlist_remove(eid):

    q(
        """
        DELETE FROM wishlist
        WHERE student_id = %s
        AND event_id = %s
        """,
        (
            session["user_id"],
            eid
        )
    )

    flash(
        "Removed from wishlist.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for("student_dashboard")
    )


@app.route("/wishlist")
@auth("student")
def wishlist():

    ensure_wishlist_table()

    items = q(
        """
        SELECT
            e.*,
            c.name AS category_name

        FROM wishlist w

        JOIN events e
            ON e.id = w.event_id

        JOIN categories c
            ON c.id = e.category_id

        WHERE w.student_id = %s
        AND e.status = 'Published'

        ORDER BY w.created_at DESC
        """,
        (session["user_id"],),
        fetch=True
    )

    return render_template(
        "wishlist.html",
        wishlist_items=items
    )


# ============================================================
# EVENT RATINGS
# ============================================================

@app.route(
    "/event/<int:eid>/rate",
    methods=["GET", "POST"]
)
@auth("student")
def rate_event(eid):

    registrations = q(
        """
        SELECT id
        FROM registrations

        WHERE student_id = %s
        AND event_id = %s
        AND status = 'Attended'
        """,
        (
            session["user_id"],
            eid
        ),
        fetch=True
    )

    if not registrations:

        flash(
            "You can only rate events you attended.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    registration_id = registrations[0]["id"]

    if request.method == "POST":

        form = request.form

        try:
            rating = int(
                form.get(
                    "rating",
                    3
                )
            )
        except (
            TypeError,
            ValueError
        ):
            rating = 3

        rating = max(
            1,
            min(5, rating)
        )

        review = form.get(
            "review",
            ""
        ).strip()

        existing = q(
            """
            SELECT id
            FROM event_ratings
            WHERE registration_id = %s
            """,
            (registration_id,),
            fetch=True
        )

        if existing:

            q(
                """
                UPDATE event_ratings

                SET
                    rating = %s,
                    review = %s

                WHERE registration_id = %s
                """,
                (
                    rating,
                    review,
                    registration_id
                )
            )

            flash(
                "Rating updated.",
                "success"
            )

        else:

            q(
                """
                INSERT INTO event_ratings (
                    registration_id,
                    rating,
                    review
                )

                VALUES (%s,%s,%s)
                """,
                (
                    registration_id,
                    rating,
                    review
                )
            )

            flash(
                "Thank you for your feedback!",
                "success"
            )

        return redirect(
            url_for("student_dashboard")
        )

    existing_rating = q(
        """
        SELECT rating, review
        FROM event_ratings
        WHERE registration_id = %s
        """,
        (registration_id,),
        fetch=True
    )

    event = q(
        """
        SELECT *
        FROM events
        WHERE id = %s
        """,
        (eid,),
        fetch=True
    )

    return render_template(
        "rate_event.html",
        event=event[0] if event else None,
        existing_rating=(
            existing_rating[0]
            if existing_rating
            else None
        )
    )


@app.route("/event/<int:eid>/ratings")
def event_ratings(eid):

    ratings = q(
        """
        SELECT
            er.rating,
            er.review,
            er.created_at,
            s.full_name

        FROM event_ratings er

        JOIN registrations r
            ON r.id = er.registration_id

        JOIN students s
            ON s.id = r.student_id

        WHERE r.event_id = %s

        ORDER BY er.created_at DESC
        """,
        (eid,),
        fetch=True
    )

    event = q(
        """
        SELECT
            e.event_name,
            AVG(er.rating) AS avg_rating

        FROM events e

        LEFT JOIN registrations r
            ON r.event_id = e.id

        LEFT JOIN event_ratings er
            ON er.registration_id = r.id

        WHERE e.id = %s

        GROUP BY e.id
        """,
        (eid,),
        fetch=True
    )

    return render_template(
        "event_ratings.html",
        ratings=ratings,
        event=event[0] if event else None
    )


# ============================================================
# EVENT PHOTO GALLERY
# ============================================================

@app.route("/event/<int:eid>/photos")
def event_gallery(eid):

    photos = q(
        """
        SELECT *
        FROM event_photos
        WHERE event_id = %s
        ORDER BY uploaded_at DESC
        """,
        (eid,),
        fetch=True
    )

    event = q(
        """
        SELECT event_name
        FROM events
        WHERE id = %s
        """,
        (eid,),
        fetch=True
    )

    return render_template(
        "event_gallery.html",
        photos=photos,
        event=event[0] if event else None
    )


@app.route(
    "/event/<int:eid>/photos/upload",
    methods=["POST"]
)
@auth("admin")
def upload_event_photos(eid):

    event = q(
        """
        SELECT id
        FROM events
        WHERE id = %s
        """,
        (eid,),
        fetch=True
    )

    if not event:

        flash(
            "Event not found.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    files = request.files.getlist(
        "photos"
    )

    uploaded_count = 0

    for file in files:

        if file and file.filename:

            photo_path = save_file(
                file,
                "events"
            )

            if photo_path:

                q(
                    """
                    INSERT INTO event_photos (
                        event_id,
                        photo_path,
                        uploaded_by
                    )

                    VALUES (%s,%s,%s)
                    """,
                    (
                        eid,
                        photo_path,
                        session["user_id"]
                    )
                )

                uploaded_count += 1

    flash(
        f"{uploaded_count} photo(s) uploaded.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for(
            "event_detail",
            eid=eid
        )
    )


# ============================================================
# WAITING LIST
# ============================================================

@app.route(
    "/event/<int:eid>/waiting/add",
    methods=["POST"]
)
@auth("student")
def add_waiting_list(eid):

    registered = q(
        """
        SELECT id
        FROM registrations

        WHERE student_id = %s
        AND event_id = %s
        """,
        (
            session["user_id"],
            eid
        ),
        fetch=True
    )

    if registered:

        flash(
            "You are already registered.",
            "info"
        )

        return redirect(
            url_for(
                "event_detail",
                eid=eid
            )
        )

    existing = q(
        """
        SELECT id
        FROM waiting_list

        WHERE student_id = %s
        AND event_id = %s
        """,
        (
            session["user_id"],
            eid
        ),
        fetch=True
    )

    if not existing:

        q(
            """
            INSERT INTO waiting_list (
                student_id,
                event_id
            )

            VALUES (%s,%s)
            """,
            (
                session["user_id"],
                eid
            )
        )

        flash(
            "Added to waiting list.",
            "success"
        )

    else:

        flash(
            "Already in waiting list.",
            "info"
        )

    return redirect(
        url_for(
            "event_detail",
            eid=eid
        )
    )


# ============================================================
# LEADERBOARD
# ============================================================

@app.route("/leaderboard")
def leaderboard():

    ensure_student_points_table()

    leaders = q(
        """
        SELECT
            s.id,
            s.full_name,
            sp.points,
            sp.total_events,
            COUNT(
                DISTINCT r.event_id
            ) AS events_attended

        FROM student_points sp

        JOIN students s
            ON s.id = sp.student_id

        LEFT JOIN registrations r
            ON r.student_id = s.id
            AND r.status = 'Attended'

        GROUP BY
            s.id,
            s.full_name,
            sp.points,
            sp.total_events

        ORDER BY sp.points DESC

        LIMIT 50
        """,
        fetch=True
    )

    return render_template(
        "leaderboard.html",
        leaderboard=leaders
    )


# ============================================================
# STUDENT PROFILE
# ============================================================

@app.route("/student/<int:sid>/profile")
def student_profile(sid):

    students = q(
        """
        SELECT *
        FROM students
        WHERE id = %s
        """,
        (sid,),
        fetch=True
    )

    if not students:

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("leaderboard")
        )

    points = q(
        """
        SELECT *
        FROM student_points
        WHERE student_id = %s
        """,
        (sid,),
        fetch=True
    )

    events_attended = q(
        """
        SELECT
            e.event_name,
            e.event_date,
            r.status

        FROM registrations r

        JOIN events e
            ON e.id = r.event_id

        WHERE r.student_id = %s
        AND r.status = 'Attended'

        ORDER BY e.event_date DESC
        """,
        (sid,),
        fetch=True
    )

    return render_template(
        "student_profile.html",
        student=students[0],
        points=(
            points[0]
            if points
            else None
        ),
        events_attended=events_attended
    )


# ============================================================
# ADMIN ANALYTICS
# ============================================================

@app.route("/admin/analytics")
@auth("admin")
def admin_analytics():

    stats = {
        "total_students": q(
            "SELECT COUNT(*) AS n FROM students",
            fetch=True
        )[0]["n"],

        "total_events": q(
            "SELECT COUNT(*) AS n FROM events",
            fetch=True
        )[0]["n"],

        "total_registrations": q(
            "SELECT COUNT(*) AS n FROM registrations",
            fetch=True
        )[0]["n"],

        "total_revenue": q(
            """
            SELECT COALESCE(
                SUM(amount),
                0
            ) AS total

            FROM payments

            WHERE status = 'Verified'
            """,
            fetch=True
        )[0]["total"] or 0,

        "pending_payments": q(
            """
            SELECT COUNT(*) AS n

            FROM payments

            WHERE status IN (
                'Pending',
                'Submitted'
            )
            """,
            fetch=True
        )[0]["n"],

        "attended_count": q(
            """
            SELECT COUNT(*) AS n

            FROM registrations

            WHERE status = 'Attended'
            """,
            fetch=True
        )[0]["n"]
    }

    event_stats = q(
        """
        SELECT
            e.event_name,
            COUNT(DISTINCT r.id) AS registrations,

            COUNT(
                DISTINCT CASE
                    WHEN r.status = 'Attended'
                    THEN r.id
                END
            ) AS attended,

            COUNT(
                DISTINCT CASE
                    WHEN p.status = 'Verified'
                    THEN p.id
                END
            ) AS verified_payments,

            COALESCE(
                SUM(
                    CASE
                        WHEN p.status = 'Verified'
                        THEN p.amount
                        ELSE 0
                    END
                ),
                0
            ) AS revenue

        FROM events e

        LEFT JOIN registrations r
            ON r.event_id = e.id

        LEFT JOIN payments p
            ON p.registration_id = r.id

        GROUP BY
            e.id,
            e.event_name

        ORDER BY registrations DESC
        """,
        fetch=True
    )

    category_stats = q(
        """
        SELECT
            c.name,
            COUNT(DISTINCT e.id) AS events,
            COUNT(DISTINCT r.id) AS registrations

        FROM categories c

        LEFT JOIN events e
            ON e.category_id = c.id

        LEFT JOIN registrations r
            ON r.event_id = e.id

        GROUP BY
            c.id,
            c.name

        ORDER BY registrations DESC
        """,
        fetch=True
    )

    return render_template(
        "admin_analytics.html",
        stats=stats,
        event_stats=event_stats,
        category_stats=category_stats
    )


# ============================================================
# EXPORT LEADERBOARD CSV
# ============================================================

@app.route("/admin/export/leaderboard")
@auth("admin")
def export_leaderboard():

    ensure_student_points_table()

    leaders = q(
        """
        SELECT
            s.full_name,
            sp.points,
            sp.total_events,
            COUNT(
                DISTINCT r.event_id
            ) AS events_attended

        FROM student_points sp

        JOIN students s
            ON s.id = sp.student_id

        LEFT JOIN registrations r
            ON r.student_id = s.id
            AND r.status = 'Attended'

        GROUP BY
            s.id,
            s.full_name,
            sp.points,
            sp.total_events

        ORDER BY sp.points DESC
        """,
        fetch=True
    )

    stream = StringIO()

    writer = csv.writer(stream)

    writer.writerow([
        "Rank",
        "Student Name",
        "Points",
        "Total Events",
        "Events Attended"
    ])

    for rank, row in enumerate(
        leaders,
        start=1
    ):

        writer.writerow([
            rank,
            row.get("full_name"),
            row.get("points"),
            row.get("total_events"),
            row.get("events_attended")
        ])

    output = stream.getvalue()

    stream.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=leaderboard.csv"
        }
    )


# ============================================================
# ALL REGISTRATIONS CSV
# ============================================================

@app.route("/admin/registrations/csv")
@auth("admin")
def all_registrations_csv():

    registrations = q(
        """
        SELECT
            r.id,
            r.status AS registration_status,
            r.created_at,

            s.full_name,
            s.email,
            s.mobile,
            s.register_number,
            s.college_name,
            s.department,
            s.course,
            s.year_semester,

            e.event_name,
            e.event_date,
            e.venue,

            p.status AS payment_status,
            p.amount

        FROM registrations r

        JOIN students s
            ON s.id = r.student_id

        JOIN events e
            ON e.id = r.event_id

        LEFT JOIN payments p
            ON p.registration_id = r.id

        ORDER BY
            e.event_date,
            r.created_at DESC
        """,
        fetch=True
    )

    stream = StringIO()

    writer = csv.writer(stream)

    writer.writerow([
        "ID",
        "Student Name",
        "Register Number",
        "College",
        "Department",
        "Course",
        "Event",
        "Event Date",
        "Mobile",
        "Email",
        "Registration Status",
        "Payment Status",
        "Amount Paid"
    ])

    for row in registrations:

        writer.writerow([
            row.get("id"),
            row.get("full_name") or "-",
            row.get("register_number") or "-",
            row.get("college_name") or "-",
            row.get("department") or "-",
            row.get("course") or "-",
            row.get("event_name") or "-",
            row.get("event_date") or "-",
            row.get("mobile") or "-",
            row.get("email") or "-",
            row.get("registration_status")
                or "Pending",
            row.get("payment_status")
                or "Pending",
            f"₹{float(row.get('amount') or 0):.2f}"
        ])

    output = stream.getvalue()

    stream.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=all_registrations.csv"
        }
    )


# ============================================================
# REGISTRATION PDF
# ============================================================

def create_registration_pdf(
    registrations,
    title
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = [
        Paragraph(
            title,
            styles["Title"]
        ),
        Spacer(1, 12),
        Paragraph(
            f"Total Registrations: {len(registrations)}",
            styles["Heading2"]
        ),
        Spacer(1, 12)
    ]

    table_data = [
        [
            "Student Name",
            "Register Number",
            "College",
            "Department",
            "Course",
            "Event",
            "Event Date",
            "Mobile",
            "Email",
            "Registration Status",
            "Payment Status",
            "Amount Paid"
        ]
    ]

    for row in registrations:

        table_data.append([
            row.get("full_name") or "-",
            row.get("register_number") or "-",
            row.get("college_name") or "-",
            row.get("department") or "-",
            row.get("course") or "-",
            row.get("event_name") or "-",
            row.get("event_date") or "-",
            row.get("mobile") or "-",
            row.get("email") or "-",
            row.get("registration_status")
                or "Pending",
            row.get("payment_status")
                or "Pending",
            f"₹{float(row.get('amount') or 0):.2f}"
        ])

    table = Table(
        table_data,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    elements.append(table)

    document.build(elements)

    pdf_data = buffer.getvalue()

    buffer.close()

    return pdf_data


# ============================================================
# ALL REGISTRATIONS PDF
# ============================================================

@app.route("/admin/registrations/pdf")
@auth("admin")
def all_registrations_pdf():

    registrations = q(
        """
        SELECT
            r.id,
            r.status AS registration_status,
            r.created_at,

            s.full_name,
            s.email,
            s.mobile,
            s.register_number,
            s.college_name,
            s.department,
            s.course,
            s.year_semester,

            e.event_name,
            e.event_date,
            e.venue,

            p.status AS payment_status,
            p.amount

        FROM registrations r

        JOIN students s
            ON s.id = r.student_id

        JOIN events e
            ON e.id = r.event_id

        LEFT JOIN payments p
            ON p.registration_id = r.id

        ORDER BY
            e.event_date,
            r.created_at DESC
        """,
        fetch=True
    )

    pdf_data = create_registration_pdf(
        registrations,
        "All Registered Students"
    )

    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
                "attachment; filename=all_registrations.pdf"
        }
    )


# ============================================================
# SINGLE REGISTRATION PDF
# ============================================================

@app.route(
    "/admin/registration/<int:rid>/pdf"
)
@auth("admin")
def registration_pdf(rid):

    rows = q(
        """
        SELECT
            r.id,
            r.status AS registration_status,
            r.created_at,

            s.full_name,
            s.email,
            s.mobile,
            s.register_number,
            s.college_name,
            s.department,
            s.course,
            s.year_semester,

            e.event_name,
            e.event_date,
            e.event_time,
            e.venue,
            e.registration_fee,

            p.amount,
            p.receipt_path,
            p.status AS payment_status

        FROM registrations r

        JOIN students s
            ON s.id = r.student_id

        JOIN events e
            ON e.id = r.event_id

        LEFT JOIN payments p
            ON p.registration_id = r.id

        WHERE r.id = %s
        """,
        (rid,),
        fetch=True
    )

    if not rows:

        return "Registration not found", 404

    data = rows[0]

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = [
        Paragraph(
            "College Event Registration Details",
            styles["Title"]
        ),
        Spacer(1, 12),
        Paragraph(
            f"Registration ID: {data.get('id')}",
            styles["Heading2"]
        ),
        Spacer(1, 8)
    ]

    details = [
        [
            "Student Name",
            data.get("full_name") or "-"
        ],
        [
            "Email",
            data.get("email") or "-"
        ],
        [
            "Mobile",
            data.get("mobile") or "-"
        ],
        [
            "Register Number",
            data.get("register_number") or "-"
        ],
        [
            "College",
            data.get("college_name") or "-"
        ],
        [
            "Department",
            data.get("department") or "-"
        ],
        [
            "Course",
            data.get("course") or "-"
        ],
        [
            "Year / Semester",
            data.get("year_semester") or "-"
        ],
        [
            "Event Name",
            data.get("event_name") or "-"
        ],
        [
            "Event Date",
            data.get("event_date") or "-"
        ],
        [
            "Event Time",
            data.get("event_time") or "-"
        ],
        [
            "Venue",
            data.get("venue") or "-"
        ],
        [
            "Registration Fee",
            f"₹{float(data.get('registration_fee') or 0):.2f}"
        ],
        [
            "Amount Paid",
            f"₹{float(data.get('amount') or 0):.2f}"
        ],
        [
            "Receipt",
            data.get("receipt_path")
            or "Not uploaded"
        ],
        [
            "Payment Status",
            data.get("payment_status")
            or "Pending"
        ],
        [
            "Registration Status",
            data.get("registration_status")
            or "Pending"
        ],
        [
            "Submitted On",
            data.get("created_at") or "-"
        ]
    ]

    table = Table(
        details,
        colWidths=[200, 320]
    )

    table.setStyle(
        TableStyle([
            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    elements.append(table)

    document.build(elements)

    pdf_data = buffer.getvalue()

    buffer.close()

    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename=registration_{rid}.pdf"
        }
    )


# ============================================================
# EVENT REGISTRATIONS PDF
# ============================================================

@app.route(
    "/admin/event/<int:eid>/registrations/pdf"
)
@auth("admin")
def event_registrations_pdf(eid):

    event_rows = q(
        """
        SELECT event_name
        FROM events
        WHERE id = %s
        """,
        (eid,),
        fetch=True
    )

    if not event_rows:

        return "Event not found", 404

    registrations = q(
        """
        SELECT
            r.id,
            r.status AS registration_status,
            r.created_at,

            s.full_name,
            s.email,
            s.mobile,
            s.register_number,
            s.college_name,
            s.department,
            s.course,
            s.year_semester,

            e.event_name,
            e.event_date,

            p.status AS payment_status,
            p.amount

        FROM registrations r

        JOIN students s
            ON s.id = r.student_id

        JOIN events e
            ON e.id = r.event_id

        LEFT JOIN payments p
            ON p.registration_id = r.id

        WHERE r.event_id = %s

        ORDER BY r.created_at DESC
        """,
        (eid,),
        fetch=True
    )

    event_name = (
        event_rows[0]["event_name"]
        or "Event"
    )

    pdf_data = create_registration_pdf(
        registrations,
        f"{event_name} - Registered Students"
    )

    safe_name = secure_filename(
        event_name
    )

    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename={safe_name}_registrations.pdf"
        }
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

def create_notification(
    student_id,
    event_id,
    title,
    message,
    notif_type="reminder"
):

    q(
        """
        INSERT INTO notifications (
            student_id,
            event_id,
            title,
            message,
            type
        )

        VALUES (%s,%s,%s,%s,%s)
        """,
        (
            student_id,
            event_id,
            title,
            message,
            notif_type
        )
    )


@app.route("/notifications")
@auth("student")
def notifications():

    ensure_notifications_table()

    notifications_list = q(
        """
        SELECT *
        FROM notifications

        WHERE student_id = %s

        ORDER BY created_at DESC

        LIMIT 20
        """,
        (session["user_id"],),
        fetch=True
    )

    unread = q(
        """
        SELECT COUNT(*) AS n
        FROM notifications

        WHERE student_id = %s
        AND read_status = 0
        """,
        (session["user_id"],),
        fetch=True
    )[0]["n"]

    q(
        """
        UPDATE notifications

        SET read_status = 1

        WHERE student_id = %s
        AND read_status = 0
        """,
        (session["user_id"],)
    )

    return render_template(
        "notifications.html",
        notifications=notifications_list,
        unread_count=unread
    )


# ============================================================
# CALENDAR
# ============================================================

@app.route("/calendar")
def calendar_view():

    events = q(
        """
        SELECT
            e.id,
            e.event_name,
            e.event_date,
            e.event_time,
            e.venue,
            c.name AS category_name

        FROM events e

        JOIN categories c
            ON c.id = e.category_id

        WHERE e.status = 'Published'
        AND e.event_date IS NOT NULL

        ORDER BY e.event_date
        """,
        fetch=True
    )

    return render_template(
        "calendar.html",
        events=events
    )


# ============================================================
# APPLICATION ERROR HANDLERS
# ============================================================

FIREWALL_PATTERN = re.compile(
    r"(?:\.\./|<script|javascript:|union\s+select|select\s+.*\s+from|"
    r"insert\s+into|drop\s+table|delete\s+from|/etc/passwd)",
    re.IGNORECASE
)


@app.before_request
def application_firewall():
    """Reject clearly malicious request paths and query strings early."""
    request_target = request.path
    if request.query_string:
        request_target += "?" + request.query_string.decode(
            "utf-8",
            errors="ignore"
        )

    if FIREWALL_PATTERN.search(unquote(request_target)):
        abort(403)


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()"
    )
    return response

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):

    return render_template(
        "500.html"
    ), 500


@app.errorhandler(403)
def forbidden_request(error):
    return render_template("404.html"), 403


# ============================================================
# APPLICATION START
# ============================================================

@app.before_request
def auto_fix_app_errors():
    """Run lightweight repair checks on every request."""
    try:
        ensure_all_tables()

        if not session.get("user_id"):
            return None

        user_role = session.get("role")
        if user_role == "student":
            q(
                """
                CREATE TABLE IF NOT EXISTS student_points (
                    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    student_id INT UNSIGNED NOT NULL,
                    points INT NOT NULL DEFAULT 0,
                    `rank` INT NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_student_points_student (student_id),
                    CONSTRAINT fk_student_points_student
                        FOREIGN KEY (student_id)
                        REFERENCES students(id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
                """
            )

        return None
    except Exception as exc:
        print(f"[AUTO-FIX] Request-level repair failed: {exc}")
        return None


if __name__ == "__main__":

    ensure_all_tables()

    app.run(
        host=os.getenv(
            "HOST",
            "0.0.0.0"
        ),
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),
        debug=False
    )