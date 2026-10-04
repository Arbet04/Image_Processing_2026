# Backend/app/models/image_task.py
#
# โมเดล ImageTask — ตาราง image_tasks เก็บประวัติการเจนรูปของแต่ละ user
# ใช้ใน routes/image.py: สร้าง 1 แถวต่อ 1 คำขอเจนรูป (POST /api/image/generate)
# แล้วอัปเดต status + รูปเมื่อ AI Service ตอบกลับ
#
# หมายเหตุสำคัญ: คอลัมน์ image_url เก็บค่าเป็น base64 string ของรูป (ไม่ใช่ URL จริง)
# ชื่อคอลัมน์คงไว้ตามเดิมเพื่อไม่ต้องทำ migration — ใน DB ต้องเป็นชนิด TEXT (รูปละ ~2 MB)

from app.extensions import db, utcnow


class ImageTask(db.Model):
    __tablename__ = 'image_tasks'

    # PK ของแต่ละงานเจนรูป
    id = db.Column(db.Integer, primary_key=True)

    # เจ้าของงานนี้ (FK ไปตาราง users) — ใช้กรองประวัติของแต่ละคนใน get_history()
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # prompt ที่ user ส่งมาตอนขอเจนรูป
    prompt = db.Column(db.Text, nullable=False)

    # สถานะงาน: 'processing' -> 'completed' หรือ 'failed'
    # (งานที่ค้าง 'processing' ตอนเปิด server จะถูกเปลี่ยนเป็น 'failed' ใน app/__init__.py)
    status = db.Column(db.String(20), nullable=False, default='processing')

    # ผลลัพธ์รูป — เก็บเป็น base64 string ที่ได้จาก ai-service (คอลัมน์ชื่อเดิมเพื่อไม่ต้อง migrate)
    image_url = db.Column(db.Text, nullable=True)

    # เวลาสร้างงาน ใช้ sort ประวัติ (order_by(ImageTask.created_at.desc()))
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def to_dict(self, include_image=True):
        """
        แปลง object เป็น dict สำหรับส่งกลับเป็น JSON ให้ Frontend
        เรียกใช้ใน image.py: generate_image(), get_task() และ get_history()
        include_image=False จะไม่ส่ง base64 ของรูป (ใช้ตอนดึงประวัติ เพราะรูปละหลาย MB)
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'prompt': self.prompt,
            'status': self.status,
            'image_url': self.image_url if include_image else None,  # จริง ๆ คือ base64 string ของรูป
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
