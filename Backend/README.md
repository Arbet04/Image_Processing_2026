# Flask Backend Service (Distributed System Project)

โครงสร้างระบบ Backend สำหรับเชื่อมต่อ Frontend, AI Service และ Database

## 🚀 วิธีการ Setup และ รันโครงการ

### 1. ติดตั้ง Dependencies
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. กำหนดค่า Environment Variables (.env)
แก้ไขไฟล์ `.env` ตาม IP Address จริงในเครือข่าย LAN:
- `AI_SERVICE_URL`: IP Address ของเครื่อง AI Server (เช่น `http://192.168.1.30:5000`)
- `DATABASE_URL`: สำหรับ SQLite ให้ใช้ `sqlite:///app.db` หรือหากเปลี่ยนเป็น PostgreSQL ใช้ `postgresql://user:pass@192.168.1.40:5432/dbname`

### 3. รัน Server
```bash
python app.py
```
*ระบบจะเปิดรับ Connection จากทุก IP บน Port 5000 (`host='0.0.0.0'`)*

---

## 📌 Endpoints ที่มีให้ใช้งาน

### Auth API (`/api/auth`)
- `POST /api/auth/register` - สมัครสมาชิก (`username`, `password`)
- `POST /api/auth/login` - เข้าสู่ระบบ (`username`, `password`) -> ได้รับ `access_token`
- `GET /api/auth/me` - ดูข้อมูลผู้ใช้ปัจจุบัน (ต้องส่ง Bearer Token)

### Image API (`/api/image`)
- `POST /api/image/generate` - สั่งสร้างรูปภาพ (ส่ง Request ต่อไปที่ AI Service)
- `GET /api/image/history` - ดึงประวัติการสร้างรูปภาพของผู้ใช้
