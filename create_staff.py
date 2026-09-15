import os
from getpass import getpass

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from mysql.connector import Error, IntegrityError


# Load environment variables
load_dotenv()


def create_staff():
    db = None
    cursor = None

    try:
        # ---------------------------------------------------------
        # Database connection
        # ---------------------------------------------------------
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "college_events_hub")
        )

        cursor = db.cursor()

        print("\n===================================")
        print("   CREATE STAFF ACCOUNT")
        print("===================================\n")

        # ---------------------------------------------------------
        # Get staff details
        # ---------------------------------------------------------
        name = input("Full name: ").strip()
        email = input("Email: ").strip().lower()

        role = input(
            "Role (admin/coordinator): "
        ).strip().lower()

        # ---------------------------------------------------------
        # Validate role
        # ---------------------------------------------------------
        if role not in ("admin", "coordinator"):
            print("\nError: Role must be 'admin' or 'coordinator'.")
            return

        # ---------------------------------------------------------
        # Validate name
        # ---------------------------------------------------------
        if not name:
            print("\nError: Full name cannot be empty.")
            return

        # ---------------------------------------------------------
        # Validate email
        # ---------------------------------------------------------
        if not email:
            print("\nError: Email cannot be empty.")
            return

        # ---------------------------------------------------------
        # Password
        # ---------------------------------------------------------
        password = getpass("Password: ")
        confirm_password = getpass("Confirm password: ")

        if not password:
            print("\nError: Password cannot be empty.")
            return

        if password != confirm_password:
            print("\nError: Passwords do not match.")
            return

        if len(password) < 6:
            print("\nError: Password must contain at least 6 characters.")
            return

        # ---------------------------------------------------------
        # Check whether email already exists
        # ---------------------------------------------------------
        cursor.execute(
            "SELECT id FROM staff WHERE email = %s",
            (email,)
        )

        existing_staff = cursor.fetchone()

        if existing_staff:
            print("\nError: A staff account with this email already exists.")
            return

        # ---------------------------------------------------------
        # Generate secure password hash
        # ---------------------------------------------------------
        password_hash = generate_password_hash(password)

        # ---------------------------------------------------------
        # Insert staff account
        # ---------------------------------------------------------
        sql = """
            INSERT INTO staff
                (full_name, email, password_hash, role)
            VALUES
                (%s, %s, %s, %s)
        """

        values = (
            name,
            email,
            password_hash,
            role
        )

        cursor.execute(sql, values)

        db.commit()

        print("\n===================================")
        print("   STAFF ACCOUNT CREATED")
        print("===================================")
        print(f"Name  : {name}")
        print(f"Email : {email}")
        print(f"Role  : {role}")
        print("===================================\n")

    except IntegrityError as e:
        if db:
            db.rollback()

        print("\nDatabase error: The email may already exist.")
        print(f"Details: {e}")

    except Error as e:
        if db:
            db.rollback()

        print("\nDatabase connection/error:")
        print(e)

    except ValueError:
        print("\nError: Invalid database port in .env file.")

    finally:
        # ---------------------------------------------------------
        # Close database resources
        # ---------------------------------------------------------
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


if __name__ == "__main__":
    create_staff()