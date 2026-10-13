# Backend/app/routes/admin.py
#
# API สำหรับผู้ดูแลระบบ (role = 'admin') — ระงับ / ปลดระงับบัญชีผู้ใช้
# การระงับคือการตั้ง users.status = 'suspended' (ไม่ลบบัญชีและไม่ลบรูป จึงปลดระงับได้)
# บัญชีที่ถูกระงับจะ login ไม่ได้ และ token เดิมใช้ไม่ได้ทันที (ดู user_lookup_loader ใน app/__init__.py)

from functools import wraps  # ← ตัวช่วยเขียน decorator
from flask import Blueprint, jsonify, current_app  # ← Blueprint, ตอบ JSON และตัวแอปปัจจุบัน
from flask_jwt_extended import jwt_required, current_user  # ← บังคับ login และอ่านผู้ใช้ปัจจุบัน
from sqlalchemy import func  # ← ฟังก์ชันของ SQL เช่น count
from app.extensions import db  # ← ตัวจัดการฐานข้อมูล
from app.models.user import User  # ← ตารางผู้ใช้
from app.models.image_task import ImageTask  # ← ตารางงานเจนรูป

admin_bp = Blueprint('admin', __name__)  # ← กลุ่ม endpoint ของผู้ดูแลระบบ (ต่อจาก /api/admin)


def admin_required(fn):  # ← decorator ใช้ครอบ endpoint ที่ admin เท่านั้นเข้าได้
    # ต้อง login และ role ใน DB ต้องเป็น 'admin' (อ่านจาก DB ทุกครั้ง ไม่เชื่อค่าที่ browser ส่งมา)
    @wraps(fn)  # ← รักษาชื่อของฟังก์ชันเดิมไว้
    @jwt_required()  # ← ต้อง login ก่อน
    def wrapper(*args, **kwargs):  # ← ฟังก์ชันที่ทำงานแทนตัวจริง
        if current_user.role != 'admin':  # ← ไม่ใช่ admin
            return jsonify({'error': 'ต้องเป็นผู้ดูแลระบบเท่านั้น'}), 403  # ← ตอบ 403 (ไม่มีสิทธิ์)
        return fn(*args, **kwargs)  # ← เป็น admin จึงเรียกฟังก์ชันตัวจริง
    return wrapper  # ← คืนฟังก์ชันที่ครอบการตรวจสิทธิ์แล้ว


@admin_bp.route('/users', methods=['GET'])  # ← ผูกฟังก์ชันด้านล่างกับ GET /api/admin/users
@admin_required  # ← เฉพาะ admin
def list_users():  # ← รายชื่อผู้ใช้ทั้งหมด
    # รายชื่อผู้ใช้ทั้งหมด พร้อมจำนวนงานเจนรูปของแต่ละคน
    counts = dict(  # ← ทำเป็น dict: เลขผู้ใช้ -> จำนวนงาน
        db.session.query(ImageTask.user_id, func.count(ImageTask.id)).group_by(ImageTask.user_id).all()  # ← นับจำนวนงานเจนรูปแยกตามเจ้าของ
    )
    users = User.query.order_by(User.id).all()  # ← ผู้ใช้ทุกคน เรียงตามเลข id
    return jsonify([{**u.to_dict(), 'image_count': counts.get(u.id, 0)} for u in users]), 200  # ← ตอบข้อมูลผู้ใช้แต่ละคน พร้อมจำนวนรูป (ไม่มีงาน = 0)


def _set_status(user_id, new_status):  # ← ใช้ร่วมกันทั้งระงับและปลดระงับ
    user = db.session.get(User, user_id)  # ← หาผู้ใช้จากเลข id
    if not user:  # ← ไม่มีผู้ใช้นี้
        return jsonify({'error': 'ไม่พบผู้ใช้นี้'}), 404  # ← ตอบ 404
    if user.id == current_user.id:  # ← พยายามระงับตัวเอง
        return jsonify({'error': 'ระงับบัญชีของตัวเองไม่ได้'}), 400  # ← ตอบ 400
    if user.role == 'admin':  # ← เป้าหมายเป็น admin
        # กันไม่ให้ admin ระงับกันเองจนไม่เหลือผู้ดูแลระบบ
        return jsonify({'error': 'ระงับบัญชีผู้ดูแลระบบไม่ได้'}), 400  # ← ตอบ 400

    user.status = new_status  # ← เปลี่ยนสถานะเป็น 'suspended' หรือ 'active'
    db.session.commit()  # ← บันทึกลงฐานข้อมูล มีผลทันที
    current_app.logger.info(f"Admin {current_user.username} set user {user.username} status to {new_status}")  # ← เขียน log ว่าใครเปลี่ยนสถานะของใคร
    return jsonify(user.to_dict()), 200  # ← ตอบข้อมูลผู้ใช้หลังเปลี่ยน


@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])  # ← ผูกกับ POST /api/admin/users/<เลขผู้ใช้>/suspend
@admin_required  # ← เฉพาะ admin
def suspend_user(user_id):  # ← ระงับบัญชี
    return _set_status(user_id, 'suspended')  # ← ตั้งสถานะเป็นถูกระงับ


@admin_bp.route('/users/<int:user_id>/unsuspend', methods=['POST'])  # ← ผูกกับ POST /api/admin/users/<เลขผู้ใช้>/unsuspend
@admin_required  # ← เฉพาะ admin
def unsuspend_user(user_id):  # ← ปลดระงับบัญชี
    return _set_status(user_id, 'active')  # ← ตั้งสถานะกลับเป็นใช้งานปกติ
