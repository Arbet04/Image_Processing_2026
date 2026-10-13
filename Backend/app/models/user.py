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

from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, utcnow


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    tasks = db.relationship('ImageTask', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
