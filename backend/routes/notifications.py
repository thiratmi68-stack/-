from flask import Blueprint, jsonify
from datetime import datetime
import json
from backend.database import get_db

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
def get_notifications():
    db = get_db()
    # Fetch all active bookings (include arrived to show success message)
    bookings = db.execute("SELECT * FROM bookings WHERE booking_Status NOT IN ('cancelled', 'completed')").fetchall()
    
    notifications = []
    now = datetime.now()
    
    today_str = now.strftime("%Y-%m-%d")
    
    # 0. Login Success Notification (New)
    # This is tricky because we need to know WHICH user is asking, or return for all.
    # Current design returns ALL and frontend filters.
    # So we fetch users who logged in recently (e.g., last 24 hours to be safe, frontend filters by user_id)
    recent_users = db.execute("SELECT ID_user, firstname, lastname, last_login FROM users WHERE last_login IS NOT NULL").fetchall()
    
    for u in recent_users:
        u_dict = dict(u)
        last_login_str = u_dict['last_login']
        try:
            last_login = datetime.fromisoformat(last_login_str)
            # If logged in within last 24 hours, show notification
            # (Frontend should ideally show only if it's 'recent' or not read, but for now we follow the pattern)
            if (now - last_login).total_seconds() < 86400:
                notifications.append({
                    'type': 'system',
                    'title': 'เข้าสู่ระบบสำเร็จ',
                    'message': f"ยินดีต้อนรับคุณ {u_dict['firstname']} เข้าสู่ระบบ",
                    'date': last_login.strftime("%Y-%m-%d"),
                    'time': last_login.strftime("%H:%M"),
                    'patient_name': f"{u_dict['firstname']} {u_dict['lastname']}".strip(),
                    'user_id': u_dict['ID_user'],
                    'is_new': True,
                    'meta': 'ระบบ'
                })
        except:
             pass

    for row in bookings:
        b = dict(row)
        dept_name = '-'
        patient_name = '-'
        try:
            details = json.loads(b['detail'])
            if isinstance(details, dict):
                dept_name = details.get('departmentName', '-')
                patient_name = details.get('patientName', '-')
        except:
            pass

        # Date/Time Parsing Logic
        booking_dt = now
        date_str = 'Unknown'
        time_str = ''
        
        try:
            raw_dt = b.get('booking_at')
            if raw_dt:
                dt_str = str(raw_dt).strip()
                # Try standard format YYYY-MM-DD HH:MM
                try:
                    booking_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                    parts = dt_str.split(' ')
                    date_str = parts[0]
                    time_str = parts[1]
                except ValueError:
                    # Try YYYY-MM-DD only
                    try:
                        booking_dt = datetime.strptime(dt_str, "%Y-%m-%d")
                        date_str = dt_str.split(' ')[0]
                        time_str = '' # No time specified
                    except ValueError:
                         # Keep defaults if all parsing fails
                         date_str = dt_str
                         pass
            else:
                 # Try to recover from detail if booking_at is missing
                 # (Optional: implement if detail has date/time)
                 pass
                 
        except Exception:
            # Final safety net
            pass
            
        diff = booking_dt - now
        days = diff.days
        total_seconds = diff.total_seconds()
        
        created_at = None
        if 'created_at' in b.keys() and b['created_at']:
             try: created_at = datetime.fromisoformat(b['created_at'])
             except: pass
             
        updated_at = None
        if 'updated_at' in b.keys() and b['updated_at']:
             try: updated_at = datetime.fromisoformat(b['updated_at'])
             except: pass
        
        # 1. Booking Success
        if created_at and (now - created_at).total_seconds() < 86400 and b['booking_Status'] not in ['cancelled', 'ยกเลิก']:
             notifications.append({
                 'type': 'appointment',
                 'title': 'จองคิวสำเร็จ',
                 'message': f"คุณได้จองคิว {dept_name} เรียบร้อยแล้ว",
                 'date': date_str,
                 'time': time_str,
                 'patient_name': patient_name,
                 'user_id': b['id_users'],
                 'is_new': True,
                 'meta': 'จองเมื่อเร็วๆ นี้'
             })

        # 2. Reschedule Success
        if updated_at and (now - updated_at).total_seconds() < 86400 and b['booking_Status'] not in ['cancelled', 'ยกเลิก', 'arrived']:
             if not created_at or (updated_at - created_at).total_seconds() > 60:
                 notifications.append({
                     'type': 'system', 
                     'title': 'เลื่อนวันจองสำเร็จ',
                     'message': f"การนัดหมาย {dept_name} เปลี่ยนเป็นวันที่ {date_str} เวลา {time_str}",
                     'date': date_str,
                     'time': time_str,
                     'patient_name': patient_name,
                     'user_id': b['id_users'],
                     'is_new': True,
                     'meta': 'แก้ไขล่าสุด'
                 })

        # 3. Check-in Success (Arrived)
        if b['booking_Status'] == 'arrived' and updated_at and (now - updated_at).total_seconds() < 86400:
             notifications.append({
                 'type': 'system',
                 'title': 'เช็คอินสำเร็จ',
                 'message': f"คุณได้เช็คอิน {dept_name} เรียบร้อยแล้ว",
                 'date': date_str,
                 'time': time_str,
                 'patient_name': patient_name,
                 'user_id': b['id_users'],
                 'is_new': True,
                 'meta': 'ใช้บริการแล้ว'
             })
                 
        # 4. Reminder Logic (Today/Tomorrow)
        if 0 <= days <= 1 and b['booking_Status'] not in ['cancelled', 'ยกเลิก', 'arrived']:
            # 4.1 "It's Time" Notification (Active within +/- 30 mins)
            # If difference is between -30 mins and +30 mins
            if abs(total_seconds) < 1800: # 30 mins window
                time_display = f"เวลา {time_str}" if time_str else ""
                notifications.append({
                    'type': 'reminder',
                    'title': 'ถึงเวลานัดหมาย',
                    'message': f"ถึงเวลานัดหมาย {dept_name} {time_display} กรุณาติดต่อจุดคัดกรอง",
                    'date': date_str,
                    'time': time_str,
                    'patient_name': patient_name,
                    'user_id': b['id_users'],
                    'is_new': True,
                    'meta': 'ถึงเวลาแล้ว'
                })
            
            # Normal reminders
            elif days == 0:
                title = 'นัดหมายวันนี้'
                time_display = f"เวลา {time_str}" if time_str else ""
                msg = f"คุณมีนัดหมาย {dept_name} {time_display} (อีก {int(total_seconds/3600)} ชม.)"
                notifications.append({
                    'type': 'reminder',
                    'title': title,
                    'message': msg,
                    'date': date_str,
                    'time': time_str,
                    'patient_name': patient_name,
                    'user_id': b['id_users'],
                    'is_new': False,
                    'meta': 'แจ้งเตือน'
                })
            else:
                title = 'เตือนนัดหมายพรุ่งนี้'
                time_display = f"เวลา {time_str}" if time_str else ""
                msg = f"พรุ่งนี้คุณมีนัดหมาย {dept_name} {time_display}"
                notifications.append({
                    'type': 'reminder',
                    'title': title,
                    'message': msg,
                    'date': date_str,
                    'time': time_str,
                    'patient_name': patient_name,
                    'user_id': b['id_users'],
                    'is_new': False,
                    'meta': 'แจ้งเตือน'
                })
            
    # Cancelled notifications
    cancelled_bookings = db.execute("SELECT * FROM bookings WHERE booking_Status IN ('cancelled', 'ยกเลิก')").fetchall()
    
    for row in cancelled_bookings:
         b = dict(row)
         updated_at = None
         if 'updated_at' in b.keys() and b['updated_at']:
             try: updated_at = datetime.fromisoformat(b['updated_at'])
             except: pass
         
         if updated_at and (now - updated_at).total_seconds() < 86400: # 24h
            try: details = json.loads(b['detail'])
            except: details = {}
            dept_name = details.get('departmentName', '-')
            patient_name = details.get('patientName', '-')
            
            notifications.append({
                 'type': 'system',
                 'title': 'ยกเลิกสำเร็จ',
                 'message': f"คุณได้ยกเลิกนัดหมาย {dept_name} เรียบร้อยแล้ว",
                 'date': b['booking_at'].split(' ')[0] if b['booking_at'] else '', 
                 'time': '', 
                 'patient_name': patient_name,
                 'user_id': b['id_users'],
                 'is_new': True,
                 'meta': 'ยกเลิกแล้ว'
            })


    return jsonify(notifications)
