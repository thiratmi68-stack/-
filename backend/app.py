from flask import Flask, request, jsonify, g
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
        "INSERT INTO bookings (patient_name, department_value, department_name, doctor_name, symptoms, date, time, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            data.get('patientName'),
            data.get('departmentValue'),
            data.get('departmentName'),
            data.get('doctorName'),
            data.get('symptoms'),
            data.get('date'),
            data.get('time'),
            datetime.utcnow().isoformat(),
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
    # only allow updating certain fields (date, time, department_name, doctor_name, symptoms)
    fields = {}
    for k in ('date', 'time', 'departmentName', 'doctorName', 'symptoms', 'departmentValue'):
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
        'symptoms': 'symptoms'
    }

    set_clause = ', '.join([f"{colmap[k]} = ?" for k in fields.keys()]) + ', rescheduled = 1'
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

if __name__ == '__main__':
    # create DB file if not exists
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
    # ensure DB is initialized before serving
    startup()
    app.run(host='0.0.0.0', port=5000, debug=True)
