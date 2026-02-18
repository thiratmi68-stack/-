from flask import Blueprint, request, jsonify, g
from datetime import datetime
import json
import random
import string
from backend.database import get_db

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('', methods=['POST'])
def create_booking():
    data = request.get_json() or {}
    booking_date = data.get('date')
    booking_time = data.get('time')
    doctor_name = data.get('doctorName')
    slot_id = data.get('slot_id')
    user_id = data.get('userId')
    
    if not user_id: 
         pass
         
    db = get_db()
    
    # Check for existing active booking
    if user_id:
        existing = db.execute("SELECT * FROM bookings WHERE id_users = ? AND booking_Status IN ('booked', 'pending', 'rescheduled', 'รอรับบริการ')", (user_id,)).fetchone()
        if existing:
            return jsonify({'error': 'ท่านมีรายการจองที่ยังไม่เสร็จสิ้น กรุณายกเลิกรายการเดิมก่อนจองใหม่'}), 400
    
    # Slot Validation
    final_slot_id = None
    
    if slot_id:
        slot = db.execute("SELECT * FROM appointment_slots WHERE slot_id = ?", (slot_id,)).fetchone()
        if not slot:
             return jsonify({'error': 'Slot not found'}), 404
        
        if slot['current_booking'] >= slot['max_capacity']:
             return jsonify({'error': 'Slot is full'}), 400
             
        final_slot_id = slot_id
        db.execute("UPDATE appointment_slots SET current_booking = current_booking + 1 WHERE slot_id = ?", (slot_id,))
    
    elif booking_date and booking_time and doctor_name:
        doc = db.execute("SELECT id_doctor FROM doctors WHERE firstname || ' ' || lastname = ?", (doctor_name,)).fetchone()
        if doc:
            doc_id = doc['id_doctor']
            slot = db.execute("""
                SELECT * FROM appointment_slots 
                WHERE doctor_id = ? AND slot_date = ? AND start_time = ?
            """, (doc_id, booking_date, booking_time)).fetchone()
            
            if slot:
                if slot['current_booking'] >= slot['max_capacity']:
                     return jsonify({'error': 'Slot is full'}), 400
                final_slot_id = slot['slot_id']
                db.execute("UPDATE appointment_slots SET current_booking = current_booking + 1 WHERE slot_id = ?", (final_slot_id,))
            else:
                return jsonify({'error': 'No available slot found for this time'}), 400
        else:
             return jsonify({'error': 'Doctor not found'}), 400
    else:
        return jsonify({'error': 'Missing booking information'}), 400


    # Cancel previous pending bookings
    if user_id:
        db.execute(
            "UPDATE bookings SET booking_Status = 'ยกเลิก' WHERE id_users = ? AND booking_Status IN ('รอรับบริการ', 'booked')",
            (user_id,)
        )

    # Create Booking
    # Modify: Use user's card_id as qr_code if available
    qr_code = ''.join(random.choices(string.digits, k=10)) # fallback
    
    if user_id:
        user_row = db.execute("SELECT card_id FROM users WHERE ID_user = ?", (user_id,)).fetchone()
        if user_row and user_row['card_id']:
            qr_code = user_row['card_id']

    booking_at = f"{booking_date} {booking_time}"
    
    detail_obj = {
        'symptoms': data.get('symptoms'),
        'doctorName': data.get('doctorName'),
        'departmentName': data.get('departmentName'), 
        'patientName': data.get('patientName')
    }
    
    detail_json = json.dumps(detail_obj, ensure_ascii=False)
    
    cur = db.execute(
        "INSERT INTO bookings (id_users, slot_id, booking_at, booking_Status, detail, qr_code, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            user_id,
            final_slot_id,
            booking_at,
            'รอรับบริการ',
            detail_json,
            qr_code,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ),
    )
    db.commit()
    booking_id = cur.lastrowid
    
    return jsonify({
        'id': booking_id,
        'status': 'booked',
        'booking_Status': 'รอรับบริการ',
        'qr_code': qr_code,
        'date': booking_date,
        'time': booking_time,
        'doctor_name': doctor_name,
        'department_name': data.get('departmentName'),
        'symptoms': data.get('symptoms')
    }), 201

@bookings_bp.route('/verify/<string:card_id>', methods=['GET'])
def verify_booking_by_card(card_id):
    db = get_db()
    
    # Logic: Find the *active* booking for this card_id
    # Join users table to filter by card_id
    # status must be 'booked' or 'รอรับบริการ'
    
    query = """
        SELECT b.* 
        FROM bookings b
        JOIN users u ON b.id_users = u.ID_user
        WHERE u.card_id = ? 
        AND b.booking_Status IN ('booked', 'รอรับบริการ', 'pending')
        ORDER BY b.id DESC
        LIMIT 1
    """
    row = db.execute(query, (card_id,)).fetchone()
    
    if not row:
        return jsonify({'error': 'No active booking found for this ID card'}), 404
        
    # Reuse the same response format as get_booking
    d = dict(row)
    try:
        details = json.loads(d['detail'])
        if isinstance(details, dict):
            d.update(details) 
            d['patient_name'] = details.get('patientName')
            d['doctor_name'] = details.get('doctorName')
            d['department_name'] = details.get('departmentName')
            d['department_value'] = details.get('departmentValue')
            d['symptoms'] = details.get('symptoms')
    except:
        d['symptoms'] = d['detail']

    if d.get('booking_at'):
         try:
             parts = d['booking_at'].split(' ')
             d['date'] = parts[0]
             d['time'] = parts[1] if len(parts) > 1 else ''
         except: pass

    d['status'] = d.get('booking_Status')
    return jsonify(d)

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    db = get_db()
    row = db.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    d = dict(row)
    try:
        details = json.loads(d['detail'])
        if isinstance(details, dict):
            d.update(details) 
            d['patient_name'] = details.get('patientName')
            d['doctor_name'] = details.get('doctorName')
            d['department_name'] = details.get('departmentName')
            d['department_value'] = details.get('departmentValue')
            d['symptoms'] = details.get('symptoms')
    except:
        d['symptoms'] = d['detail']

    if d.get('booking_at'):
         try:
             parts = d['booking_at'].split(' ')
             d['date'] = parts[0]
             d['time'] = parts[1] if len(parts) > 1 else ''
         except: pass

    d['status'] = d.get('booking_Status')
    return jsonify(d)

@bookings_bp.route('/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    db = get_db()
    
    booking = db.execute('SELECT slot_id, booking_Status FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    if booking:
        slot_id = booking['slot_id']
        status = booking['booking_Status']
        if slot_id and status not in ['ยกเลิก', 'cancelled']:
             db.execute("UPDATE appointment_slots SET current_booking = MAX(0, current_booking - 1) WHERE slot_id = ?", (slot_id,))
             
    cur = db.execute("UPDATE bookings SET booking_Status = 'cancelled', updated_at = ? WHERE id = ?", (datetime.now().isoformat(), booking_id))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'cancelled'}), 200

@bookings_bp.route('/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    data = request.get_json() or {}
    db = get_db()
    fields = {}
    for k in ('date', 'time', 'departmentName', 'doctorName', 'symptoms', 'departmentValue', 'status'):
        if k in data:
            fields[k] = data[k]

    if not fields:
        return jsonify({'error': 'no fields to update'}), 400

    current = db.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    if not current:
        return jsonify({'error': 'not found'}), 404
    
    current_dict = dict(current)
    try:
        current_details = json.loads(current_dict['detail'])
    except:
        current_details = {}

    updated_details = current_details.copy()
    
    for k in ('departmentName', 'doctorName', 'symptoms', 'departmentValue', 'patientName'):
        if k in data:
            updated_details[k] = data[k]
    
    current_booking_at = current_dict.get('booking_at', '')
    try:
        parts = current_booking_at.split(' ')
        c_date = parts[0]
        c_time = parts[1] if len(parts) > 1 else ''
    except:
        c_date = ''
        c_time = ''
        
    new_date = data.get('date', c_date)
    new_time = data.get('time', c_time)
    new_booking_at = f"{new_date} {new_time}"
    
    new_status = data.get('status')
    if new_status == 'booked': new_status_val = 'รอรับบริการ'
    elif new_status == 'arrived': new_status_val = 'arrived' 
    else: new_status_val = new_status
    
    if not new_status:
        new_status_val = current_dict['booking_Status']

    old_status = current_dict.get('booking_Status')
    slot_id = current_dict.get('slot_id')
    
    is_active_old = old_status not in ['ยกเลิก', 'cancelled']
    is_cancelled_new = new_status_val in ['ยกเลิก', 'cancelled']
    
    if slot_id and is_active_old and is_cancelled_new:
         db.execute("UPDATE appointment_slots SET current_booking = MAX(0, current_booking - 1) WHERE slot_id = ?", (slot_id,))
    
    new_detail_json = json.dumps(updated_details, ensure_ascii=False)
    
    db.execute(
        "UPDATE bookings SET detail = ?, booking_at = ?, booking_Status = ?, updated_at = ? WHERE id = ?",
        (new_detail_json, new_booking_at, new_status_val, datetime.now().isoformat(), booking_id)
    )
    db.commit()

    row = db.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    d = dict(row)
    try:
        details = json.loads(d['detail'])
        if isinstance(details, dict):
            d.update(details) 
            d['patient_name'] = details.get('patientName')
            d['doctor_name'] = details.get('doctorName')
            d['department_name'] = details.get('departmentName')
            d['department_value'] = details.get('departmentValue')
            d['symptoms'] = details.get('symptoms')
    except:
        d['symptoms'] = d['detail']

    if d.get('booking_at'):
         try:
             parts = d['booking_at'].split(' ')
             d['date'] = parts[0]
             d['time'] = parts[1] if len(parts) > 1 else ''
         except: pass

    d['status'] = d.get('booking_Status')
    return jsonify(d)

@bookings_bp.route('', methods=['GET'])
def list_bookings():
    db = get_db()
    rows = db.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d['status'] = d.get('booking_Status')
        d['symptoms'] = d.get('detail')
        if d.get('booking_at'):
             try:
                 parts = d['booking_at'].split(' ')
                 d['date'] = parts[0]
                 d['time'] = parts[1] if len(parts) > 1 else ''
             except: pass
             
        try:
            details = json.loads(d['detail'])
            if isinstance(details, dict):
                 d['doctor_name'] = details.get('doctorName')
                 d['department_name'] = details.get('departmentName')
                 d['patient_name'] = details.get('patientName')
                 d['symptoms'] = details.get('symptoms')
        except:
            pass
            
        results.append(d)
    return jsonify(results)

@bookings_bp.route('/slots/<int:slot_id>', methods=['DELETE'])
def delete_slot(slot_id):
    db = get_db()
    cur = db.execute('DELETE FROM appointment_slots WHERE slot_id = ?', (slot_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'deleted'}), 200
