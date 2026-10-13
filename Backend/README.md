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
คัดลอก `.env.example` เป็น `.env` แล้วแก้ค่าให้ตรงกับเครื่องจริง (ไฟล์ `.env` ไม่ขึ้น Git) — แก้แล้วต้อง restart server:
- `SECRET_KEY`, `JWT_SECRET_KEY`: ตั้งเป็นค่าสุ่มยาวๆ (`python -c "import secrets; print(secrets.token_hex(32))"`)
- `AI_SERVICE_URL`: ที่อยู่ของ AI Service — เครื่องเดียวกันใช้ `http://127.0.0.1:8001` ถ้าคนละเครื่องใส่ IP เครื่องนั้น เช่น `http://172.20.x.x:8001` (port **8001** ไม่ใช่ 5000)
- `DATABASE_URL`: ตอนนี้ใช้ SQLite `sqlite:///app.db` (สร้างไฟล์ `instance/app.db` และตารางให้เอง) หากเปลี่ยนเป็น PostgreSQL ใช้ `postgresql://user:pass@<IP>:5432/dbname`
  - ถ้าเจอ `no such column: users.role` แปลว่าไฟล์ DB เก่าไม่ตรงกับโค้ด — ลบ `instance/app.db` แล้วรันใหม่ (ข้อมูลทดสอบจะหาย)

### 3. รัน Server
```bash
python app.py
```
*ระบบจะเปิดรับ Connection จากทุก IP บน Port 5000 (`host='0.0.0.0'`)*

---

## 📌 Endpoints ที่มีให้ใช้งาน

### Health
- `GET /api/health` - เช็คว่า Backend ทำงานอยู่ (ไม่ต้อง login) ใช้ทดสอบ nginx reverse proxy

### Auth API (`/api/auth`)
- `POST /api/auth/register` - สมัครสมาชิก (`username`, `password`)
- `POST /api/auth/login` - เข้าสู่ระบบ (`username`, `password`) -> ได้รับ `access_token` (บัญชีที่ถูกระงับได้ 403)
- `GET /api/auth/me` - ดูข้อมูลผู้ใช้ปัจจุบัน (ต้องส่ง Bearer Token)

### Admin API (`/api/admin`) — ต้อง login ด้วยบัญชีที่ `role = 'admin'`
- `GET /api/admin/users` - รายชื่อผู้ใช้ทั้งหมด พร้อมจำนวนรูป (`image_count`)
- `POST /api/admin/users/<id>/suspend` - ระงับบัญชี (login ไม่ได้ และ token เดิมใช้ไม่ได้ทันที) ไม่ลบบัญชีและรูป
- `POST /api/admin/users/<id>/unsuspend` - ปลดระงับ
- ระงับตัวเองหรือระงับ admin คนอื่นไม่ได้ / คนที่ไม่ใช่ admin เรียกจะได้ 403

ตั้ง admin: ใส่ `ADMIN_USERNAME=<ชื่อผู้ใช้>` ใน `.env` (ตรงตัวพิมพ์เล็ก/ใหญ่) แล้ว restart — ถ้าบัญชีมีอยู่แล้วจะได้สิทธิ์ตอนเปิด server ถ้ายังไม่มีจะได้สิทธิ์ตอนสมัคร

### Image API (`/api/image`)
- `POST /api/image/generate` - สั่งสร้างรูปภาพ (`prompt`, `negative_prompt`, `steps`, `width`, `height`, `seed`) ส่งต่อไปที่ AI Service แล้วรอจนรูปเสร็จ ตอบกลับ `image_url` เป็น base64
- `GET /api/image/history` - ดึงประวัติการสร้างรูปภาพของผู้ใช้ (ไม่รวมรูป ส่ง `?include_images=1` ถ้าต้องการ)
- `GET /api/image/<id>` - ดึงงานเดียวพร้อมรูป (`image_url` เป็น base64)
