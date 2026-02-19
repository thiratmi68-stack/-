# Frontend Documentation



## สมาชิกในทีมและการแบ่งงาน (Team Members & Route Assignments)
1. นางสาวกฤติมา ทองมวล
Role: Login, Register 
**Backend File:** `backend/routes/auth.py`
Authentication
- `index.html`: **Login Page** - หน้าเข้าสู่ระบบ
    - **API:** `POST /api/login`
- `register.html`: **Registration Page** - หน้าลงทะเบียนผู้ป่วยใหม่
    - **API:** `POST /api/register`
- `index.html`: **Login Page** - หน้าเข้าสู่ระบบ
    - **API:** `POST /api/admin/login`

2. นายจิรัฐิติกาล ลาเลิศ
Role: Booking(เลือกแผนก/แพทย์), confirm
**Backend File:** `backend/routes/doctors.py`, `backend/routes/bookings.py`
- `booking.html`: **Select Logic** - หน้าเลือกแพทย์หรือแผนก
    - **API:** `GET /api/doctors`, `GET /api/departments`
- `confirm.html`: **Confirm Booking** - หน้าตรวจสอบและยืนยันข้อมูลการจอง
    - **API:** `POST /api/bookings`
- `myticket.html`: **Booking Success,Delete** - หน้าแสดงตั๋ว/QR Code 6 เมื่อจองสำเร็จ และยกเลิกการจอง 
    - **API:** `DELETE /api/bookings/{booking_id}`
**SYSTEM** ระบบตัดคิวอัตโนมัติ

3. นายธีรัช มิฉะนั้น
Role: home, datetime
**Backend File:** `backend/routes/doctors.py`
- `home.html`: **Main Dashboard** - หน้าหลักแสดงเมนูและข้อมูลเบื้องต้น
    - **API:** `GET /api/doctors`, `GET /api/departments` (For display)
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:   
    - **API:** `POST /api/admin/login` (For display)
- `booking.html`: **Select Schedule** - หน้าเลือกวันและเวลาที่ต้องการจอง
    - **API:** `GET /api/doctors/{id}/slots` (with slots)

4. นายทีปกรณ์ แก่นกุล 
Role: datetime, details
**Backend File:** `backend/routes/doctors.py`, `backend/routes/bookings.py`
- `booking.html`: **Select Schedule** - หน้าเลือกวันและเวลาที่ต้องการจอง
    - **API** `GET /api/admin/slots`
- `details.html`: **Booking Details** - หน้าดูรายละเอียดการจองแต่ละรายการ
    - **API:** `GET /api/bookings/{booking_id}`
- `reschedule.html`: **Reschedule Details** - เลือกวันและเวลาที่ต้องเลื่อนการจอง
    - **API:** `PUT /api/bookings/{booking_id}`

5. นายวุฒิภัทร วิริยเสนกุล
Role: history, notification
**Backend File:** `backend/routes/bookings.py`, `backend/routes/notifications.py`
- `history.html`: **Booking History** - หน้าดูประวัติการจองทั้งหมด
    - **API:** `GET /api/bookings`
- `notification.html`: **Notification Center** - หน้าดูรายการแจ้งเตือนต่างๆ
    - **API:** `GET /api/notifications`
**SYSTEM** ระบบแจ้งเตือน

6. นายพงศกร กอคูณ
Role: QR Code scan, canel Booking
**Backend File:** `backend/routes/bookings.py`
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:
    - ดูรายการจองทั้งหมด (All Bookings)
        - **API:** `GET /api/bookings`
    - ตรวจสอบรายชื่อการจอง (Check Booking List)
        - **API:** `PUT /api/bookings/{booking_id}` (Update Status)


7. นายรัชชานนท์ อรรถพันธ์
Role: admin(ตรวจสอบรายชื่อ), admin(ดูประวัติการจอง)
**Backend File:** `backend/routes/bookings.py`
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:
    - จัดการ slots (manage slots)
        - **API**  `POST /api/admin/slots` ,`PUT /api/admin/slots/{slot_id}` ,`DELETE /api/admin/slots/{slot_id}`

8. นายอภิสิทธิ์ พรหมมา
Role: admin(home), admin(จัดการรายชื่อแพทย์)
**Backend File:** `backend/routes/admin.py` (Create/Update/Delete), `backend/routes/doctors.py` (List)
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:
    - จัดการรายชื่อแพทย์ (Manage Doctors)
        - **API:** `GET /api/doctors` (List), `POST /api/admin/doctors` (Create), `PUT /api/admin/doctors/{doctor_id}` (Update), `DELETE /api/admin/doctors/{doctor_id}` (Delete)