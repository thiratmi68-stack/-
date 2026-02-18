# Frontend Documentation



## สมาชิกในทีมและการแบ่งงาน (Team Members & Route Assignments)
1. นางสาวกฤติมา ทองมวล
Role: Login, Register 
**Backend File:** `backend/routes/auth.py`
Authentication
- `index.html`: **Login Page** - หน้าเข้าสู่ระบบสำหรับผู้ป่วย
    - **API:** `POST /api/login`
- `register.html`: **Registration Page** - หน้าลงทะเบียนผู้ป่วยใหม่
    - **API:** `POST /api/register`

2. นายจิรัฐิติกาล ลาเลิศ
Role: Booking(เลือกแผนก/แพทย์), confirm
**Backend File:** `backend/routes/doctors.py`, `backend/routes/bookings.py`
- `booking.html`: **Select Logic** - หน้าเลือกแพทย์หรือแผนก
    - **API:** `GET /api/doctors`, `GET /api/departments`
- `confirm.html`: **Confirm Booking** - หน้าตรวจสอบและยืนยันข้อมูลการจอง
    - **API:** `POST /api/bookings`

3. นายธีรัช มิฉะนั้น
Role: home, datetime
**Backend File:** `backend/routes/doctors.py`
- `home.html`: **Main Dashboard** - หน้าหลักแสดงเมนูและข้อมูลเบื้องต้น
    - **API:** `GET /api/doctors`, `GET /api/departments` (For display)
- `datetime.html`: **Select Schedule** - หน้าเลือกวันและเวลาที่ต้องการจอง
    - **API:** `GET /api/doctors/{id}/slots` (with slots)

4. นายทีปกรณ์ แก่นกุล 
Role: datetime, details
**Backend File:** `backend/routes/doctors.py`, `backend/routes/bookings.py`
- `datetime.html`: **Select Schedule** - หน้าเลือกวันและเวลาที่ต้องการจอง
    - **API:** `GET /api/doctors/{id}/slots`
- `details.html`: **Booking Details** - หน้าดูรายละเอียดการจองแต่ละรายการ
    - **API:** `GET /api/bookings/{booking_id}`

5. นายวุฒิภัทร วิริยเสนกุล
Role: history, notification
**Backend File:** `backend/routes/bookings.py`, `backend/routes/notifications.py`
- `history.html`: **Booking History** - หน้าดูประวัติการจองทั้งหมด
    - **API:** `GET /api/bookings`
- `notification.html`: **Notification Center** - หน้าดูรายการแจ้งเตือนต่างๆ
    - **API:** `GET /api/notifications`

6. นายพงศกร กอคูณ
Role: QR Code scan, canel Booking
**Backend File:** `backend/routes/bookings.py`
- `myticket.html`: **Booking Success** - หน้าแสดงตั๋ว/QR Code เมื่อจองสำเร็จ
    - **API:** `GET /api/bookings/{booking_id}`
- `details.html`: **Booking Details** - หน้าดูรายละเอียดการจองแต่ละรายการ
    - **API:** `DELETE /api/bookings/{booking_id}` (Cancel), `PUT /api/bookings/{booking_id}` (Reschedule)

7. นายรัชชานนท์ อรรถพันธ์
Role: admin(ตรวจสอบรายชื่อ), admin(ดูประวัติการจอง)
**Backend File:** `backend/routes/bookings.py`
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:
    - ดูรายการจองทั้งหมด (All Bookings)
        - **API:** `GET /api/bookings`
    - ตรวจสอบรายชื่อการจอง (Check Booking List)
        - **API:** `PUT /api/bookings/{booking_id}` (Update Status)

8. นายอภิสิทธิ์ พรหมมา
Role: admin(home), admin(จัดการรายชื่อแพทย์)
**Backend File:** `backend/routes/admin.py` (Create/Update/Delete), `backend/routes/doctors.py` (List)
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:
    - หน้าหลักadmin (Admin Home)
        - **API:** `POST /api/admin/login`
    - จัดการรายชื่อแพทย์ (Manage Doctors)
        - **API:** `GET /api/doctors` (List), `POST /api/admin/doctors` (Create), `PUT /api/admin/doctors/{doctor_id}` (Update), `DELETE /api/admin/doctors/{doctor_id}` (Delete)



## User (Patient) - Frontend Pages

### Authentication
- `index.html`: **Login Page** - หน้าเข้าสู่ระบบสำหรับผู้ป่วย
- `register.html`: **Registration Page** - หน้าลงทะเบียนผู้ป่วยใหม่

### Dashboard & Main
- `home.html`: **Main Dashboard** - หน้าหลักแสดงเมนูและข้อมูลเบื้องต้น

### Booking Process (Flow)
1. `booking.html`: **Select Logic** - หน้าเลือกแพทย์หรือแผนก
2. `datetime.html`: **Select Schedule** - หน้าเลือกวันและเวลาที่ต้องการจอง
3. `confirm.html`: **Confirm Booking** - หน้าตรวจสอบและยืนยันข้อมูลการจอง
4. `myticket.html`: **Booking Success** - หน้าแสดงตั๋ว/QR Code เมื่อจองสำเร็จ

### History & Management
- `history.html`: **Booking History** - หน้าดูประวัติการจองทั้งหมด
- `details.html`: **Booking Details** - หน้าดูรายละเอียดการจองแต่ละรายการ

### Notifications
- `notification.html`: **Notification Center** - หน้าดูรายการแจ้งเตือนต่างๆ

---

## Admin (Staff) - Frontend Pages

### Dashboard & Management
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:
    - ดูรายการจองทั้งหมด (All Bookings)
    - จัดการรายชื่อแพทย์ (Manage Doctors)
    - จัดการเจ้าหน้าที่ (Manage Staff)
