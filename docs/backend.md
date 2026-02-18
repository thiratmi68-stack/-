# API Documentation

Base URL: `http://localhost:5000` (Default Flask Port)

## User (Patient)

### Authentication
- **POST** `/api/register` ลงทะเบียนผู้ป่วยใหม่
- **POST** `/api/login` เข้าสู่ระบบผู้ป่วย

### Browsing & Information
- **GET** `/api/doctors` ดึงรายชื่อแพทย์ทั้งหมด (รองรับ filter: `?department=`, `?specialist=`)
- **GET** `/api/departments` ดึงรายชื่อแผนกทั้งหมด

### My Bookings
- **POST** `/api/bookings` สร้างการจองใหม่ (Booking)
- **GET** `/api/bookings` ดึงประวัติการจองของฉัน (My Booking History)
- **GET** `/api/bookings/{booking_id}` ดูรายละเอียดการจอง
- **PUT** `/api/bookings/{booking_id}` อัพเดทข้อมูลการจอง (เช่น เลื่อนนัด - Reschedule)
- **DELETE** `/api/bookings/{booking_id}` ยกเลิกการจอง

### Notifications
- **GET** `/api/notifications` ดึงรายการแจ้งเตือน (นัดหมายใกล้ถึง, จองสำเร็จ)

---

## Admin (Staff)

### Authentication
- **POST** `/api/admin/login` เข้าสู่ระบบเจ้าหน้าที่ (Admin/Staff)

### Operations & Dashboard
- **GET** `/api/bookings` ดึงรายการจองทั้งหมด (Admin Dashboard / All History)
- **PUT** `/api/bookings/{booking_id}` อัพเดทสถานะการจอง (เช่น Check-in, Completed)

### Doctor Management
- **POST** `/api/admin/doctors` เพิ่มรายชื่อแพทย์ใหม่
- **PUT** `/api/admin/doctors/{doctor_id}` แก้ไขข้อมูลแพทย์ (ตารางออกตรวจ, สถานะ)
- **DELETE** `/api/admin/doctors/{doctor_id}` ลบรายชื่อแพทย์

--