from flask import Blueprint, request, jsonify, g
from datetime import datetime
from backend.database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    db = get_db()
    
    # Validation
    if not data.get('email') or not data.get('password') or not data.get('phone'):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check duplicates
    cur = db.execute("SELECT ID_user FROM users WHERE email = ? OR tel = ?", (data.get('email'), data.get('phone')))
    if cur.fetchone():
         return jsonify({'error': 'Email or Phone already exists'}), 400

    cur = db.execute(
        "INSERT INTO users (firstname, lastname, email, tel, card_id, birth_day, hash_password, created_at) VALUES (?,?,?,?,?,?,?,?)",
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

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('identifier')
    password = data.get('password')
    
    if not identifier or not password:
         return jsonify({'error': 'Missing identifier or password'}), 400

    db = get_db()
    # Check tel OR card_id and duplicate password check for security (should use hashing in prod)
    row = db.execute(
        "SELECT * FROM users WHERE (tel = ? OR card_id = ?) AND hash_password = ?", 
        (identifier, identifier, password)
    ).fetchone()
    
    if row:
        user = dict(row)
        # Update last_login
        now_iso = datetime.now().isoformat()
        db.execute("UPDATE users SET last_login = ? WHERE ID_user = ?", (now_iso, user['ID_user']))
        db.commit()
        
        if 'hash_password' in user:
            del user['hash_password'] # don't send password back
        # normalize name for frontend
        user['name'] = f"{user.get('firstname','')} {user.get('lastname','')}".strip()
        user['role'] = 'patient'
        user['id'] = user['ID_user'] # Standardize ID
        return jsonify(user), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401
