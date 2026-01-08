from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bookings.db')

app = Flask(__name__)
CORS(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            department_value TEXT,
            department_name TEXT,
            doctor_name TEXT,
            symptoms TEXT,
            date TEXT,
            time TEXT,
            created_at TEXT
            
        )
        """
    )
    db.commit()
    # ensure there's a rescheduled column for marking reschedules
    cur = db.execute("PRAGMA table_info(bookings)").fetchall()
    cols = [r['name'] for r in cur]
    if 'rescheduled' not in cols:
        db.execute("ALTER TABLE bookings ADD COLUMN rescheduled INTEGER DEFAULT 0")
        db.commit()

    # ensure status column exists
    if 'status' not in cols:
        db.execute("ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT 'booked'")
        db.commit()

    # staff table for admin management
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT,
            role TEXT,
            contact TEXT,
            password TEXT,
            created_at TEXT
        )
        """
    )
    db.commit()
    # ensure password column exists for older DBs
    cur = db.execute("PRAGMA table_info(staff)").fetchall()
    staff_cols = [r['name'] for r in cur]
    if 'password' not in staff_cols:
        db.execute("ALTER TABLE staff ADD COLUMN password TEXT")
        db.commit()

    # ensure default admin user exists
    admin = db.execute("SELECT * FROM staff WHERE username = ?", ('admin',)).fetchone()
    if not admin:
        db.execute(
            "INSERT INTO staff (username, full_name, role, contact, password, created_at) VALUES (?,?,?,?,?,?)",
            ('admin', 'Administrator', 'admin', 'admin@example.com', 'admin123', datetime.utcnow().isoformat()),
        )
        db.commit()

# Initialize DB at startup using application context (safer and compatible)
def startup():
    with app.app_context():
        init_db()

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json() or {}
    # accept partial data; store what's provided
    db = get_db()
    cur = db.execute(
        "INSERT INTO bookings (patient_name, department_value, department_name, doctor_name, symptoms, date, time, created_at, status) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            data.get('patientName'),
            data.get('departmentValue'),
            data.get('departmentName'),
            data.get('doctorName'),
            data.get('symptoms'),
            data.get('date'),
            data.get('time'),
            datetime.utcnow().isoformat(),
            'booked',
        ),
    )
    db.commit()
    booking_id = cur.lastrowid
    row = db.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    db = get_db()
    row = db.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(dict(row))


@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    db = get_db()
    cur = db.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'deleted'}), 200


@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    data = request.get_json() or {}
    db = get_db()
    # only allow updating certain fields (date, time, department_name, doctor_name, symptoms, status)
    fields = {}
    for k in ('date', 'time', 'departmentName', 'doctorName', 'symptoms', 'departmentValue', 'status'):
        if k in data:
            fields[k] = data[k]

    if not fields:
        return jsonify({'error': 'no fields to update'}), 400

    # map keys to column names
    colmap = {
        'date': 'date',
        'time': 'time',
        'departmentName': 'department_name',
        'departmentValue': 'department_value',
        'doctorName': 'doctor_name',
        'symptoms': 'symptoms',
        'status': 'status'
    }

    set_clause = ', '.join([f"{colmap[k]} = ?" for k in fields.keys()])
    # Only set rescheduled flag if we are NOT just updating status (i.e. if we are changing date/time etc)
    # But simplifying: if date/time is in fields, set rescheduled=1?
    # For now, keep logic simple. If we update status, rescheduled flag logic might need care.
    # If the user is just confirming arrival (status='arrived'), we shouldn't mark as rescheduled.
    if any(k in fields for k in ['date', 'time']):
         set_clause += ', rescheduled = 1'
    
    values = [fields[k] for k in fields.keys()]
    values.append(booking_id)

    cur = db.execute(f"UPDATE bookings SET {set_clause} WHERE id = ?", values)
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    row = db.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    return jsonify(dict(row)), 200

@app.route('/api/bookings', methods=['GET'])
def list_bookings():
    db = get_db()
    rows = db.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in rows])


# --- Admin staff endpoints ---
@app.route('/api/admin/staff', methods=['GET'])
def list_staff():
    db = get_db()
    rows = db.execute('SELECT id, username, full_name, role, contact, created_at FROM staff ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/staff', methods=['POST'])
def create_staff():
    data = request.get_json() or {}
    db = get_db()
    cur = db.execute(
        "INSERT INTO staff (username, full_name, role, contact, password, created_at) VALUES (?,?,?,?,?,?)",
        (
            data.get('username'),
            data.get('fullName'),
            data.get('role'),
            data.get('contact'),
            data.get('password'),
            datetime.utcnow().isoformat(),
        ),
    )
    db.commit()
    row = db.execute('SELECT * FROM staff WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route('/api/admin/staff/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    data = request.get_json() or {}
    db = get_db()
    fields = {}
    for k in ('username', 'fullName', 'role', 'contact', 'password'):
        if k in data:
            fields[k] = data[k]

    if not fields:
        return jsonify({'error': 'no fields to update'}), 400

    colmap = {
        'username': 'username',
        'fullName': 'full_name',
        'role': 'role',
        'contact': 'contact',
        'password': 'password',
    }

    set_clause = ', '.join([f"{colmap[k]} = ?" for k in fields.keys()])
    values = [fields[k] for k in fields.keys()]
    values.append(staff_id)

    cur = db.execute(f"UPDATE staff SET {set_clause} WHERE id = ?", values)
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    row = db.execute('SELECT * FROM staff WHERE id = ?', (staff_id,)).fetchone()
    return jsonify(dict(row)), 200


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'missing credentials'}), 400
    db = get_db()
    row = db.execute('SELECT id, username, full_name, role, contact FROM staff WHERE username = ? AND password = ?', (username, password)).fetchone()
    if not row:
        return jsonify({'error': 'invalid credentials'}), 401
    return jsonify(dict(row)), 200


@app.route('/api/admin/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    db = get_db()
    cur = db.execute('DELETE FROM staff WHERE id = ?', (staff_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'deleted'}), 200


@app.route('/admin')
def admin_page():
    page_dir = os.path.abspath(os.path.join(BASE_DIR, '..', 'Page'))
    return send_from_directory(page_dir, 'admin.html')


@app.route('/admin/')
def admin_page_slash():
    page_dir = os.path.abspath(os.path.join(BASE_DIR, '..', 'Page'))
    return send_from_directory(page_dir, 'admin.html')


@app.route('/admin.html')
def admin_page_file():
    page_dir = os.path.abspath(os.path.join(BASE_DIR, '..', 'Page'))
    return send_from_directory(page_dir, 'admin.html')


# Serve the Page/ static files so frontend can call same-origin APIs
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_page(path):
    page_dir = os.path.abspath(os.path.join(BASE_DIR, '..', 'Page'))
    target = os.path.join(page_dir, path)
    if os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(page_dir, path)
    # fallback to index
    return send_from_directory(page_dir, 'index.html')

if __name__ == '__main__':
    # create DB file if not exists
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
    # ensure DB is initialized before serving
    startup()
    app.run(host='0.0.0.0', port=5000, debug=True)
