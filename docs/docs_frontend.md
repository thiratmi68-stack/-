# Frontend Documentation

## User (Patient) - Frontend Pages

### Authentication
- `index.html`: **Login Page** - หน้าเข้าสู่ระบบสำหรับผู้ป่วย 
- `register.html`: **Registration Page** - หน้าลงทะเบียนผู้ป่วยใหม่ 

### Dashboard & Main
- `home.html`: **Main Dashboard** - หน้าหลักแสดงเมนูและข้อมูลเบื้องต้น 

### Booking Process (Flow)
1. `booking.html`: **Select Logic** - หน้าเลือกแพทย์หรือแผนก  ,
**Select Schedule** - หน้าเลือกวันและเวลาที่ต้องการจอง 
3. `confirm.html`: **Confirm Booking** - หน้าตรวจสอบและยืนยันข้อมูลการจอง 
4. `myticket.html`: **Booking Success,Delete** - หน้าแสดงตั๋ว/QR Code เมื่อจองสำเร็จ และยกเลิกการจอง 
5. `reschedule.html`: **Reschedule Details** - หน้าเลือกวันและเวลาที่ต้องเลื่อนการจอง 

### History & Management
- `history.html`: **Booking History** - หน้าดูประวัติการจองทั้งหมด
- `details.html`: **Booking Details** - หน้าดูรายละเอียดการจองแต่ละรายการ 


### Notifications
- `notification.html`: **Notification Center** - หน้าดูรายการแจ้งเตือนต่างๆ

### slot
---

## Admin (Staff) - Frontend Pages

### Dashboard & Management
- `admin.html`: **Unified Admin Dashboard** - หน้าจัดการรวมสำหรับเจ้าหน้าที่:
    - ดูรายการจองทั้งหมด (All Bookings)
    - จัดการรายชื่อแพทย์ (Manage Doctors)
    - จัดการเจ้าหน้าที่ (Manage Staff)
