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

    # doctors table
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            department TEXT,
            specialty TEXT,
            image TEXT,
            status TEXT DEFAULT 'ว่างวันนี้',
            status_color TEXT DEFAULT 'text-green-600'
        )
        """
    )
    db.commit()

    # users table (patients)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            id_card TEXT,
            dob TEXT,
            password TEXT,
            created_at TEXT
        )
        """
    )
    db.commit()

    # Seed initial doctors if empty
    cur = db.execute("SELECT count(*) FROM doctors")
    if cur.fetchone()[0] == 0:
        initial_doctors = [
            ('นพ. สมชาย ใจดี', 'med', 'อายุรกรรมทั่วไป', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'ว่างวันนี้', 'text-green-600'),
            ('พญ. วารี รักษา', 'med', 'อายุรกรรมโรคหัวใจ', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'คิวเต็มช่วงเช้า', 'text-gray-400'),
            ('ทพ. สมศักดิ์ ฟันสวย', 'dent', 'ทันตกรรมทั่วไป', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'ว่างวันนี้', 'text-green-600'),
            ('ทพญ. สวยใส ไร้ฟันผุ', 'dent', 'ทันตกรรมจัดฟัน', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'ว่างช่วงบ่าย', 'text-yellow-600'),
            ('นพ. กระดูก แข็งแรง', 'ortho', 'ศัลยกรรมกระดูก', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'ว่างช่วงบ่าย', 'text-yellow-600'),
            ('พญ. ข้อเข่า ดีจริง', 'ortho', 'ศัลยกรรมกระดูกและข้อ', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'ว่างวันนี้', 'text-green-600'),
            ('พญ. ใจดี รักเด็ก', 'pedia', 'กุมารเวชกรรม', 'https://cdn-icons-png.flaticon.com/512/3774/3774293.png', 'ว่างวันนี้', 'text-green-600'),
            ('นพ. เด็กน้อย สดใส', 'pedia', 'ทารกแรกเกิด', 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png', 'คิวเต็มวันนี้', 'text-red-600')
        ]
        db.executemany("INSERT INTO doctors (name, department, specialty, image, status, status_color) VALUES (?,?,?,?,?,?)", initial_doctors)
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

# --- Auth API ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    db = get_db()
    
    # Validation
    if not data.get('email') or not data.get('password') or not data.get('phone'):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check duplicates
    cur = db.execute("SELECT id FROM users WHERE email = ? OR phone = ?", (data.get('email'), data.get('phone')))
    if cur.fetchone():
         return jsonify({'error': 'Email or Phone already exists'}), 400

    cur = db.execute(
        "INSERT INTO users (first_name, last_name, email, phone, id_card, dob, password, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            data.get('firstName'),
            data.get('lastName'),
            data.get('email'),
            data.get('phone'),
            data.get('idCard'),
            data.get('dob'),
            data.get('password'),
            datetime.utcnow().isoformat()
        )
    )
    db.commit()
    return jsonify({'status': 'success', 'id': cur.lastrowid}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username') # can be email or phone
    password = data.get('password')
    
    if not username or not password:
         return jsonify({'error': 'Missing credentials'}), 400

    db = get_db()
    # Check email or phone
    row = db.execute("SELECT * FROM users WHERE (email = ? OR phone = ?) AND password = ?", (username, username, password)).fetchone()
    
    if row:
        user = dict(row)
        del user['password'] # don't send password back
        # normalize name for frontend
        user['name'] = f"{user.get('first_name','')} {user.get('last_name','')}".strip()
        user['role'] = 'patient'
        return jsonify(user), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401


# --- Public Doctor API ---
@app.route('/api/doctors', methods=['GET'])
def list_doctors():
    department = request.args.get('department')
    db = get_db()
    if department:
        rows = db.execute('SELECT * FROM doctors WHERE department = ?', (department,)).fetchall()
    else:
        rows = db.execute('SELECT * FROM doctors').fetchall()
    return jsonify([dict(r) for r in rows])


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


# --- Admin Doctor Management Endpoints ---
@app.route('/api/admin/doctors', methods=['POST'])
def create_doctor():
    data = request.get_json() or {}
    db = get_db()
    cur = db.execute(
        "INSERT INTO doctors (name, department, specialty, image, status, status_color) VALUES (?,?,?,?,?,?)",
        (
            data.get('name'),
            data.get('department'),
            data.get('specialty'),
            data.get('image'),
            data.get('status', 'ว่างวันนี้'),
            data.get('status_color', 'text-green-600')
        )
    )
    db.commit()
    row = db.execute('SELECT * FROM doctors WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/admin/doctors/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    data = request.get_json() or {}
    db = get_db()
    fields = {}
    valid_fields = ('name', 'department', 'specialty', 'image', 'status', 'status_color')
    for k in valid_fields:
        if k in data:
            fields[k] = data[k]

    if not fields:
        return jsonify({'error': 'no fields to update'}), 400

    set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
    values = [fields[k] for k in fields.keys()]
    values.append(doctor_id)

    cur = db.execute(f"UPDATE doctors SET {set_clause} WHERE id = ?", values)
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    row = db.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
    return jsonify(dict(row)), 200

@app.route('/api/admin/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    db = get_db()
    cur = db.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
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

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    # In a real app, we would filter by logged in user ID from session/token
    # Here we expect frontend to filter, or we return global + user specific logic if we had auth middleware
    # For simplicity, we return ALL notifications logic, and frontend filters by patient name if matched
    # Or better: We fetch all bookings and compute notifications for them
    
    db = get_db()
    # Fetch all active bookings
    bookings = db.execute("SELECT * FROM bookings WHERE status NOT IN ('cancelled', 'completed', 'arrived')").fetchall()
    
    notifications = []
    now = datetime.now()
    
    for b in bookings:
        try:
            booking_dt = datetime.strptime(f"{b['date']} {b['time']}", "%Y-%m-%d %H:%M")
        except:
            continue
            
        diff = booking_dt - now
        days = diff.days
        
        # New Booking Notification (created within last 24 hours)
        try:
             created_at = datetime.strptime(b['created_at'], "%Y-%m-%dT%H:%M:%S.%f")
        except:
             try: created_at = datetime.strptime(b['created_at'], "%Y-%m-%dT%H:%M:%S")
             except: created_at = now # fallback

        if (now - created_at).total_seconds() < 86400: # 24 hours
             notifications.append({
                 'type': 'appointment',
                 'title': 'การจองสำเร็จ',
                 'message': f"คุณได้จองคิว {b['department_name']} วันที่ {b['date']}",
                 'date': b['date'],
                 'time': b['time'],
                 'patient_name': b['patient_name'],
                 'is_new': True,
                 'meta': 'จองเมื่อเร็วๆ นี้'
             })

        # Reminder Logic
        if 0 <= days <= 1:
            if days == 0:
                msg = "ถึงวันนัดหมายแล้ว! กรุณาเตรียมตัวให้พร้อม"
                title = "ถึงวันนัดหมาย"
                urgent = True
            else:
                msg = f"อีก {days} วัน จะถึงวันนัดหมายของคุณ" # Actually if days=1 it means tomorrow
                title = "แจ้งเตือนใกล้ถึงวันนัด"
                urgent = False
                
            notifications.append({
                'type': 'reminder',
                'title': title,
                'message': msg,
                'date': b['date'],
                'time': b['time'],
                'patient_name': b['patient_name'],
                'urgent': urgent,
                'meta': 'เหลืออีก ' + (f"{int(diff.total_seconds()/3600)} ชม." if days==0 else f"{days} วัน")
            })
            
    # Add a system notification for everyone
    notifications.append({
        'type': 'system',
        'title': 'ยินดีต้อนรับสู่ Medical Queue',
        'message': 'ระบบจองคิวออนไลน์พร้อมให้บริการตลอด 24 ชม.',
        'meta': 'ข่าวสารระบบ',
        'patient_name': None # For everyone
    })
            
    return jsonify(notifications)


if __name__ == '__main__':
    # create DB file if not exists
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
    # ensure DB is initialized before serving
    startup()
    app.run(host='0.0.0.0', port=5000, debug=True)
