from flask import Blueprint, request, jsonify
from datetime import datetime
from backend.database import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/staff', methods=['GET'])
def list_staff():
    db = get_db()
    rows = db.execute('SELECT * FROM staff ORDER BY id_admin DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/staff', methods=['POST'])
def create_staff():
    data = request.get_json() or {}
    db = get_db()
    
    fname = data.get('firstname')
    lname = data.get('lastname')
    if not fname and data.get('fullName'):
        parts = data.get('fullName').split(' ', 1)
        fname = parts[0]
        lname = parts[1] if len(parts) > 1 else ''

    cur = db.execute(
        "INSERT INTO staff (firstname, lastname, employee_id, username, hash_password, contact, role, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            fname,
            lname,
            data.get('employee_id'),
            data.get('username'),
            data.get('password'),
            data.get('contact'),
            data.get('role'),
            datetime.utcnow().isoformat(),
        ),
    )
    db.commit()
    row = db.execute('SELECT * FROM staff WHERE id_admin = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@admin_bp.route('/staff/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    data = request.get_json() or {}
    db = get_db()
    fields = {}
    
    if 'firstname' in data: fields['firstname'] = data['firstname']
    if 'lastname' in data: fields['lastname'] = data['lastname']
    if 'fullName' in data:
        parts = data['fullName'].split(' ', 1)
        fields['firstname'] = parts[0]
        fields['lastname'] = parts[1] if len(parts) > 1 else ''
        
    for k in ('employee_id', 'username', 'contact', 'role'):
        if k in data:
            fields[k] = data[k]
            
    if 'password' in data:
        fields['hash_password'] = data['password']

    if not fields:
        return jsonify({'error': 'no fields to update'}), 400

    set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
    values = [fields[k] for k in fields.keys()]
    values.append(staff_id)

    cur = db.execute(f"UPDATE staff SET {set_clause} WHERE id_admin = ?", values)
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    row = db.execute('SELECT * FROM staff WHERE id_admin = ?', (staff_id,)).fetchone()
    return jsonify(dict(row)), 200

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'missing credentials'}), 400
    db = get_db()
    row = db.execute('SELECT * FROM staff WHERE username = ? AND hash_password = ?', (username, password)).fetchone()
    if not row:
        return jsonify({'error': 'invalid credentials'}), 401
    
    user = dict(row)
    del user['hash_password']
    user['full_name'] = f"{user.get('firstname', '')} {user.get('lastname', '')}".strip()
    return jsonify(user), 200

@admin_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    db = get_db()
    cur = db.execute('DELETE FROM staff WHERE id_admin = ?', (staff_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'deleted'}), 200

@admin_bp.route('/doctors', methods=['POST'])
def create_doctor():
    data = request.get_json() or {}
    db = get_db()
    
    fname = data.get('firstname')
    lname = data.get('lastname')
    if not fname and data.get('name'):
        parts = data.get('name').split(' ', 1)
        fname = parts[0]
        lname = parts[1] if len(parts) > 1 else ''

    cur = db.execute(
        "INSERT INTO doctors (firstname, lastname, doctor_id, department, specialist, status, schedule, image, status_color) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            fname,
            lname,
            data.get('doctor_id'),
            data.get('department'),
            data.get('specialist'), 
            data.get('status', 'ว่างวันนี้'),
            data.get('schedule'),
            data.get('image'),
            data.get('status_color', 'text-green-600')
        )
    )
    db.commit()
    row = db.execute('SELECT * FROM doctors WHERE id_doctor = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@admin_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    data = request.get_json() or {}
    db = get_db()
    fields = {}
    
    if 'name' in data:
         parts = data.get('name').split(' ', 1)
         fields['firstname'] = parts[0]
         fields['lastname'] = parts[1] if len(parts) > 1 else ''
    
    if 'department' in data: fields['specialist'] = data['department'] 
    if 'specialty' in data: fields['specialist'] = data['specialty']
         
    valid_fields = ('firstname', 'lastname', 'doctor_id', 'department', 'specialist', 'status', 'schedule', 'image', 'status_color')
    for k in valid_fields:
        if k in data:
            fields[k] = data[k]

    if not fields:
        return jsonify({'error': 'no fields to update'}), 400

    set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
    values = [fields[k] for k in fields.keys()]
    values.append(doctor_id)

    cur = db.execute(f"UPDATE doctors SET {set_clause} WHERE id_doctor = ?", values)
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    row = db.execute('SELECT * FROM doctors WHERE id_doctor = ?', (doctor_id,)).fetchone()
    return jsonify(dict(row)), 200

@admin_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    db = get_db()
    cur = db.execute('DELETE FROM doctors WHERE id_doctor = ?', (doctor_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'deleted'}), 200
