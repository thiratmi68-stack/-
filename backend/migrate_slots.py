import sqlite3
import datetime
import re

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bookings.db')

# Map Thai/English days to Python weekday integers (Monday is 0)
DAY_MAP = {
    'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6,
    'จ': 0, 'อ': 1, 'พ': 2, 'พฤ': 3, 'ศ': 4, 'ส': 5, 'อา': 6,
    'จันทร์': 0, 'อังคาร': 1, 'พุธ': 2, 'พฤหัส': 3, 'ศุกร์': 4, 'เสาร์': 5, 'อาทิตย์': 6
}

# Standard 30-min slots
STANDARD_SLOTS = [
    ("09:00", "09:30"), ("09:30", "10:00"),
    ("10:00", "10:30"), ("10:30", "11:00"),
    ("13:00", "13:30"), ("13:30", "14:00"),
    ("14:00", "14:30"), ("14:30", "15:00"),
    ("15:00", "15:30"), ("15:30", "16:00"),
    ("16:00", "16:30"), ("16:30", "17:00")
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_schedule(schedule_str):
    """
    Parses a schedule string like "จ-ศ 09:00-17:00" or "Mon-Fri 09:00-16:00".
    Returns a list of allowed weekdays [0, 1, 2, 3, 4] and start/end times.
    For simplicity in this migration, we will generate ALL standard slots 
    if the doctor works on that day, as the standard slots are within typical working hours.
    """
    if not schedule_str:
        return []

    # Simple regex to find days range
    # Matches "Mon-Fri" or "จ-ศ"
    # This is a basic parser. Complex schedules might need manual adjustment.
    
    allowed_days = []
    
    # Check for "Mon-Fri" or "จ-ศ" pattern
    if 'จ-ศ' in schedule_str or 'Mon-Fri' in schedule_str:
        allowed_days = [0, 1, 2, 3, 4]
    elif 'จ-อา' in schedule_str: # Mon-Sun
        allowed_days = [0, 1, 2, 3, 4, 5, 6]
    elif 'ส-อา' in schedule_str: # Sat-Sun
        allowed_days = [5, 6]
    else:
        # Fallback: Assume Mon-Fri if unknown, or try to detect specific days
        # If specific days are listed like "Mon, Wed" (not implemented deep parsing for now)
        allowed_days = [0, 1, 2, 3, 4] 

    return allowed_days

def migrate():
    conn = get_db()
    cursor = conn.cursor()

    # Get all doctors
    doctors = cursor.execute("SELECT * FROM doctors").fetchall()

    today = datetime.date.today()
    days_to_generate = 30
    
    print(f"Found {len(doctors)} doctors. Generating slots for next {days_to_generate} days...")

    count = 0
    for doc in doctors:
        doc_id = doc['id_doctor']
        # We need department_id. 
        # Since doctors table might not have it or it's in Doctor_to_Department
        # Let's check if we can get it.
        # For now, we'll try to get it from Doctor_to_Department or doctor's 'department' field text mapping
        
        # Try to find existing mapping
        dept_mapping = cursor.execute("SELECT department_id FROM Doctor_to_Department WHERE doctor_id = ?", (doc['id_doctor'],)).fetchone()
        
        dept_id = None
        if dept_mapping:
            dept_id = dept_mapping['department_id']
        else:
            # If not mapped, try to find department by name
            dept_name = doc['department']
            dept_row = cursor.execute("SELECT department_id FROM departments WHERE name = ?", (dept_name,)).fetchone()
            if dept_row:
                dept_id = dept_row['department_id']
            else:
                # Create department if not exists? Or skip?
                # For migration safety, let's create it or use a default
                if dept_name:
                    cursor.execute("INSERT INTO departments (name) VALUES (?)", (dept_name,))
                    dept_id = cursor.lastrowid
                    # Link it
                    cursor.execute("INSERT INTO Doctor_to_Department (doctor_id, department_id) VALUES (?, ?)", (doc['id_doctor'], dept_id))

        if not dept_id:
            print(f"Skipping doctor {doc['name']} (No Department)")
            continue

        schedule = doc['schedule']
        allowed_days = parse_schedule(schedule)
        
        if not allowed_days:
            # If no schedule, maybe assume default Mon-Fri?
            allowed_days = [0, 1, 2, 3, 4]

        # Generate slots
        for day_offset in range(days_to_generate):
            date = today + datetime.timedelta(days=day_offset)
            if date.weekday() in allowed_days:
                # Generate all standard slots for this day
                for start, end in STANDARD_SLOTS:
                    # Check if exists
                    exists = cursor.execute("""
                        SELECT 1 FROM appointment_slots 
                        WHERE doctor_id = ? AND slot_date = ? AND start_time = ?
                    """, (doc['id_doctor'], date.strftime('%Y-%m-%d'), start)).fetchone()

                    if not exists:
                        cursor.execute("""
                            INSERT INTO appointment_slots 
                            (doctor_id, department_id, slot_date, start_time, end_time, max_capacity, current_booking, status)
                            VALUES (?, ?, ?, ?, ?, ?, 0, 'available')
                        """, (doc['id_doctor'], dept_id, date.strftime('%Y-%m-%d'), start, end, 10)) # Default capacity 10
                        count += 1
    
    conn.commit()
    print(f"Migration completed. Generated {count} new slots.")
    conn.close()

if __name__ == "__main__":
    migrate()
