# Backend/app/models/image_task.py
#
# โมเดล ImageTask — ตาราง image_tasks เก็บประวัติการเจนรูปของแต่ละ user
# ใช้ใน routes/image.py: สร้าง 1 แถวต่อ 1 คำขอเจนรูป (POST /api/image/generate)
# แล้วอัปเดต status + รูปเมื่อ AI Service ตอบกลับ
#
# หมายเหตุสำคัญ: คอลัมน์ image_url เก็บค่าเป็น base64 string ของรูป (ไม่ใช่ URL จริง)
# ชื่อคอลัมน์คงไว้ตามเดิมเพื่อไม่ต้องทำ migration — ใน DB ต้องเป็นชนิด TEXT (รูปละ ~2 MB)

from app.extensions import db, utcnow  # ← ตัวจัดการฐานข้อมูล และฟังก์ชันเวลา


class ImageTask(db.Model):  # ← 1 object = 1 งานเจนรูป = 1 แถวในตาราง image_tasks
    __tablename__ = 'image_tasks'  # ← ชื่อตารางในฐานข้อมูล

    # PK ของแต่ละงานเจนรูป
    id = db.Column(db.Integer, primary_key=True)  # ← เลขงาน (primary key) ส่งไปให้ AI Service เป็น task_id

    # เจ้าของงานนี้ (FK ไปตาราง users) — ใช้กรองประวัติของแต่ละคนใน get_history()
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # ← เจ้าของงาน อ้างไปที่ users.id (foreign key)

    # prompt ที่ user ส่งมาตอนขอเจนรูป
    prompt = db.Column(db.Text, nullable=False)  # ← คำอธิบายรูปที่ผู้ใช้พิมพ์

    # สถานะงาน: 'processing' -> 'completed' หรือ 'failed'
    # (งานที่ค้าง 'processing' ตอนเปิด server จะถูกเปลี่ยนเป็น 'failed' ใน app/__init__.py)
    status = db.Column(db.String(20), nullable=False, default='processing')  # ← processing, completed หรือ failed

    # ผลลัพธ์รูป — เก็บเป็น base64 string ที่ได้จาก ai-service (คอลัมน์ชื่อเดิมเพื่อไม่ต้อง migrate)
    image_url = db.Column(db.Text, nullable=True)  # ← รูปในรูปแบบ base64 (ว่างได้ระหว่างที่ยังเจนไม่เสร็จ)

    # เวลาสร้างงาน ใช้ sort ประวัติ (order_by(ImageTask.created_at.desc()))
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)  # ← เวลาที่สร้างงาน ใช้เรียงประวัติ

    def to_dict(self, include_image=True):  # ← แปลงเป็น dict เพื่อส่งเป็น JSON
        """
        แปลง object เป็น dict สำหรับส่งกลับเป็น JSON ให้ Frontend
        เรียกใช้ใน image.py: generate_image(), get_task() และ get_history()
        include_image=False จะไม่ส่ง base64 ของรูป (ใช้ตอนดึงประวัติ เพราะรูปละหลาย MB)
        """
        return {  # ← ข้อมูลงานที่หน้าเว็บได้รับ
            'id': self.id,  # ← เลขงาน
            'user_id': self.user_id,  # ← เจ้าของงาน
            'prompt': self.prompt,  # ← คำอธิบายรูป
            'status': self.status,  # ← สถานะงาน
            'image_url': self.image_url if include_image else None,  # จริง ๆ คือ base64 string ของรูป
            'created_at': self.created_at.isoformat() if self.created_at else None,  # ← แปลงเวลาเป็นข้อความ (ISO)
        }
