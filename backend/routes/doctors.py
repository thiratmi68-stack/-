from flask import Blueprint, request, jsonify
from backend.database import get_db

doctors_bp = Blueprint('doctors', __name__)

@doctors_bp.route('/doctors', methods=['GET'])
def list_doctors():
    department = request.args.get('department')
    specialist = request.args.get('specialist')
    db = get_db()
    
    if department:
        rows = db.execute('SELECT * FROM doctors WHERE department = ?', (department,)).fetchall()
    elif specialist:
        rows = db.execute('SELECT * FROM doctors WHERE specialist = ?', (specialist,)).fetchall()
    else:
        rows = db.execute('SELECT * FROM doctors').fetchall()
    
    results = []
    for r in rows:
        d = dict(r)
        d['name'] = f"{d.get('firstname', '')} {d.get('lastname', '')}".strip()
        d['specialty'] = d.get('specialist')
        results.append(d)
        
    return jsonify(results)

@doctors_bp.route('/departments', methods=['GET'])
def list_departments():
    db = get_db()
    rows = db.execute('SELECT * FROM departments').fetchall()
    return jsonify([dict(r) for r in rows])

@doctors_bp.route('/doctors/<int:doctor_id>/slots', methods=['GET'])
def list_doctor_slots(doctor_id):
    db = get_db()
    date = request.args.get('date')
    
    query = 'SELECT * FROM appointment_slots WHERE doctor_id = ?'
    files = [doctor_id]
    
    if date:
        query += ' AND slot_date = ?'
        files.append(date)
    
    query += ' ORDER BY slot_date, start_time'
    
    rows = db.execute(query, files).fetchall()
    return jsonify([dict(r) for r in rows])

@doctors_bp.route('/doctors/<int:doctor_id>/slots', methods=['POST'])
def create_doctor_slot(doctor_id):
    data = request.get_json() or {}
    db = get_db()
    
    doc = db.execute('SELECT department FROM doctors WHERE id_doctor = ?', (doctor_id,)).fetchone()
    if not doc:
        return jsonify({'error': 'Doctor not found'}), 404
    
    dept_code = doc['department']
    dept_map_reverse = {
        'med': 'อายุรกรรม',
        'dent': 'ทันตกรรม',
        'ortho': 'ศัลยกรรมกระดูก',
        'pedia': 'กุมารเวชกรรม'
    }
    thai_name = dept_map_reverse.get(dept_code)
    dept_id = 0
    if thai_name:
         d_row = db.execute('SELECT department_id FROM departments WHERE name LIKE ?', (f"%{thai_name}%",)).fetchone()
         if d_row: dept_id = d_row['department_id']
    
    cur = db.execute(
        """
        INSERT INTO appointment_slots (
            doctor_id, department_id, slot_date, start_time, end_time, max_capacity, current_booking, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doctor_id,
            dept_id,
            data.get('date'),
            data.get('start_time'),
            data.get('end_time'),
            data.get('capacity', 1),
            0, # current_booking
            'available' 
        )
    )
    db.commit()
    
    return jsonify({'status': 'success', 'slot_id': cur.lastrowid}), 201
