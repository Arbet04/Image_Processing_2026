# Backend/app/models/user.py
#
# โมเดล User — ตาราง users เก็บบัญชีผู้ใช้ ใช้ใน routes/auth.py (register / login / me)
# รหัสผ่านเก็บเป็น hash ของ werkzeug ในคอลัมน์ password_hash เท่านั้น ไม่เก็บรหัสผ่านตรงๆ
#
# ชื่อตาราง/คอลัมน์ใน DB ต้องตรงกับไฟล์นี้ — db.create_all() สร้างเฉพาะตารางที่ยังไม่มี
# ไม่เพิ่มคอลัมน์ให้ตารางเดิม (ถ้าไม่ตรงจะเจอ error แบบ "no such column: users.role")
#
# role:   'user' (ค่าเริ่มต้น) หรือ 'admin' — admin ตั้งจาก ADMIN_USERNAME ใน .env และใช้ /api/admin/... ได้
# status: 'active' (ค่าเริ่มต้น) หรือ 'suspended' — บัญชีที่ถูกระงับ login ไม่ได้ และ token เดิมใช้ไม่ได้ทันที
# last_login: อัปเดตทุกครั้งที่ login สำเร็จ

from werkzeug.security import generate_password_hash, check_password_hash  # ← ฟังก์ชันแปลงรหัสผ่านเป็น hash และตรวจรหัสผ่าน
from app.extensions import db, utcnow  # ← ตัวจัดการฐานข้อมูล และฟังก์ชันเวลา


class User(db.Model):  # ← 1 object = 1 แถวในตาราง users
    __tablename__ = 'users'  # ← ชื่อตารางในฐานข้อมูล

    id = db.Column(db.Integer, primary_key=True)  # ← เลขประจำตัวผู้ใช้ (primary key) เพิ่มให้อัตโนมัติ
    username = db.Column(db.String(80), unique=True, nullable=False)  # ← ชื่อผู้ใช้ ห้ามซ้ำ ห้ามว่าง
    password_hash = db.Column(db.String(255), nullable=False)  # ← รหัสผ่านที่แปลงเป็น hash แล้ว
    role = db.Column(db.String(20), nullable=False, default='user')  # ← สิทธิ์: 'user' หรือ 'admin'
    status = db.Column(db.String(20), nullable=False, default='active')  # ← สถานะ: 'active' หรือ 'suspended'
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)  # ← เวลาที่สมัคร ใส่ให้อัตโนมัติ
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)  # ← เวลาที่แก้ไขล่าสุด อัปเดตให้อัตโนมัติ
    last_login = db.Column(db.DateTime, nullable=True)  # ← เวลาที่ login ล่าสุด (ว่างได้)

    tasks = db.relationship('ImageTask', backref='user', lazy=True)  # ← user.tasks = งานเจนรูปทั้งหมดของคนนี้

    def set_password(self, password):  # ← ตั้งรหัสผ่าน
        self.password_hash = generate_password_hash(password)  # ← แปลงเป็น hash ก่อนเก็บ ย้อนกลับเป็นรหัสผ่านเดิมไม่ได้

    def check_password(self, password):  # ← ตรวจว่ารหัสผ่านที่พิมพ์มาถูกไหม
        return check_password_hash(self.password_hash, password)  # ← เทียบกับ hash ที่เก็บไว้ คืน True/False

    def to_dict(self):  # ← แปลงเป็น dict เพื่อส่งเป็น JSON (ไม่ส่ง password_hash ออกไป)
        return {  # ← ข้อมูลผู้ใช้ที่หน้าเว็บเห็น
            'id': self.id,  # ← เลขประจำตัว
            'username': self.username,  # ← ชื่อผู้ใช้
            'role': self.role,  # ← หน้าเว็บใช้ตัดสินว่าจะแสดงเมนู admin ไหม
            'status': self.status,  # ← ใช้งานปกติ หรือ ถูกระงับ
            'created_at': self.created_at.isoformat() if self.created_at else None,  # ← แปลงเวลาเป็นข้อความ (ISO) ถ้าไม่มีให้เป็น None
            'last_login': self.last_login.isoformat() if self.last_login else None,  # ← แปลงเวลาเป็นข้อความ ถ้ายังไม่เคย login ให้เป็น None
        }
