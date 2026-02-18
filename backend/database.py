from flask import g
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Adjusted to be in backend/
DB_PATH = os.path.join(BASE_DIR, 'backend', 'bookings.db') # app.py is in backend/, so database.py in backend/ means BASE_DIR is backend/. 
# Wait, if database.py is in backend/, then dirname(abspath) is backend/.
# In app.py: BASE_DIR = os.path.dirname(os.path.abspath(__file__)) -> .../backend
# DB_PATH = os.path.join(BASE_DIR, 'bookings.db') -> .../backend/bookings.db

# If I move to backend/database.py:
# BASE_DIR = os.path.dirname(os.path.abspath(__file__)) -> .../backend
# DB_PATH = os.path.join(BASE_DIR, 'bookings.db') -> .../backend/bookings.db
# So logic stays same.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bookings.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    
    # bookings table
    cur = db.execute("PRAGMA table_info(bookings)")
    cols = [r['name'] for r in cur.fetchall()]
    if 'booking_Status' not in cols:
        db.execute("DROP TABLE IF EXISTS bookings")
        db.commit()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER,
            id_users INTEGER,
            booking_at TEXT,
            booking_Status TEXT,
            detail TEXT,
            qr_code TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(id_users) REFERENCES users(ID_user)
        )
        """
    )
    db.commit()
    
    # Check for new columns in bookings and add if missing
    cur = db.execute("PRAGMA table_info(bookings)")
    cols = [r['name'] for r in cur.fetchall()]
    if 'created_at' not in cols:
        db.execute("ALTER TABLE bookings ADD COLUMN created_at TEXT")
    if 'updated_at' not in cols:
        db.execute("ALTER TABLE bookings ADD COLUMN updated_at TEXT")
    db.commit()

    # staff table
    cur = db.execute("PRAGMA table_info(staff)")
    staff_cols = [r['name'] for r in cur.fetchall()]
    if 'full_name' in staff_cols:
        db.execute("DROP TABLE staff")
        db.commit()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT,
            lastname TEXT,
            employee_id TEXT,
            username TEXT UNIQUE,
            hash_password TEXT,
            contact TEXT,
            role TEXT,
            created_at TEXT
        )
        """
    )
    db.commit()

    # doctors table
    cur = db.execute("PRAGMA table_info(doctors)")
    doc_cols = [r['name'] for r in cur.fetchall()]
    if 'department' not in doc_cols:
        db.execute("DROP TABLE IF EXISTS doctors")
        db.commit()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS doctors (
            id_doctor INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT,
            lastname TEXT,
            doctor_id TEXT,
            department TEXT,
            specialist TEXT,
            status TEXT DEFAULT 'ว่างวันนี้',
            schedule TEXT,
            image TEXT,
            status_color TEXT DEFAULT 'text-green-600'
        )
        """
    )
    db.commit()

    # users table
    cur = db.execute("PRAGMA table_info(users)")
    current_cols = [r['name'] for r in cur.fetchall()]
    if 'first_name' in current_cols:
        db.execute("DROP TABLE users")
        db.commit()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            ID_user INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT,
            lastname TEXT,
            tel TEXT,
            email TEXT,
            card_id TEXT,
            hash_password TEXT,
            birth_day TEXT,
            created_at TEXT,
            last_login TEXT
        )
        """
    )
    db.commit()

    # Check for last_login column in users and add if missing
    cur = db.execute("PRAGMA table_info(users)")
    current_cols = [r['name'] for r in cur.fetchall()]
    if 'last_login' not in current_cols:
        db.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
        db.commit()

    # departments table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
        """
    )
    db.commit()

    # Doctor_to_Department table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS Doctor_to_Department (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT,
            department_id INTEGER
        )
        """
    )
    db.commit()

    # appointment_slots table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS appointment_slots (
            slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER,
            department_id INTEGER,
            slot_date TEXT,
            start_time TEXT,
            end_time TEXT,
            max_capacity INTEGER,
            current_booking INTEGER DEFAULT 0,
            status TEXT,
            FOREIGN KEY(doctor_id) REFERENCES doctors(id_doctor),
            FOREIGN KEY(department_id) REFERENCES departments(department_id)
        )
        """
    )
    db.commit()

    # Seed initial departments if empty
    cur = db.execute("SELECT count(*) FROM departments")
    if cur.fetchone()[0] == 0:
        initial_depts = [
            ('อายุรกรรม',),
            ('ทันตกรรม',),
            ('ศัลยกรรมกระดูก',),
            ('กุมารเวชกรรม',)
        ]
        db.executemany("INSERT INTO departments (name) VALUES (?)", initial_depts)
        db.commit()

    # Seed initial doctors if empty
    cur = db.execute("SELECT count(*) FROM doctors")
    if cur.fetchone()[0] == 0:
        initial_doctors = [
            ('สมชาย', 'ใจดี', 'D001', 'med', 'อายุรกรรมทั่วไป', 'ว่างวันนี้', 'จ-ศ 09:00-16:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'text-green-600'),
            ('วารี', 'รักษา', 'D002', 'med', 'อายุรกรรมโรคหัวใจ', 'คิวเต็มช่วงเช้า', 'อ-พฤ 10:00-14:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'text-gray-400'),
            ('สมศักดิ์', 'ฟันสวย', 'D003', 'dent', 'ทันตกรรมทั่วไป', 'ว่างวันนี้', 'จ-ส 09:00-17:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'text-green-600'),
            ('สวยใส', 'ไร้ฟันผุ', 'D004', 'dent', 'ทันตกรรมจัดฟัน', 'ว่างช่วงบ่าย', 'จ-ศ 13:00-19:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'text-yellow-600'),
            ('กระดูก', 'แข็งแรง', 'D005', 'ortho', 'ศัลยกรรมกระดูก', 'ว่างช่วงบ่าย', 'จ,พ,ศ 09:00-12:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'text-yellow-600'),
            ('ข้อเข่า', 'ดีจริง', 'D006', 'ortho', 'ศัลยกรรมกระดูกและข้อ', 'ว่างวันนี้', 'พฤ 09:00-16:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'text-green-600'),
            ('ใจดี', 'รักเด็ก', 'D007', 'pedia', 'กุมารเวชกรรม', 'ว่างวันนี้', 'ทุกวัน 08:00-20:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'text-green-600'),
            ('เด็กน้อย', 'สดใส', 'D008', 'pedia', 'ทารกแรกเกิด', 'คิวเต็มวันนี้', 'จ-ศ 08:00-16:00', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'text-red-600')
        ]
        db.executemany("INSERT INTO doctors (firstname, lastname, doctor_id, department, specialist, status, schedule, image, status_color) VALUES (?,?,?,?,?,?,?,?,?)", initial_doctors)
        db.commit()
startup = init_db
