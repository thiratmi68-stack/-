
import sqlite3
import os
from datetime import datetime

DB_PATH = '/home/pheem49/vscode/Project/-/backend/bookings.db'

def seed_admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT * FROM staff WHERE username = 'admin'")
    if cursor.fetchone():
        print("Admin user already exists.")
        conn.close()
        return

    # Create default admin
    # Schema: id_admin, firstname, lastname, employee_id, username, hash_password, contact, role, created_at
    cursor.execute("""
        INSERT INTO staff (firstname, lastname, employee_id, username, hash_password, contact, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('Admin', 'System', 'ADMIN01', 'admin', '1234', '000-000-0000', 'admin', datetime.utcnow().isoformat()))
    
    conn.commit()
    print("Default admin created: admin / 1234")
    conn.close()

if __name__ == '__main__':
    seed_admin()
