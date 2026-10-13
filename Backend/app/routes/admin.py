# Backend/app/routes/admin.py
#
# API สำหรับผู้ดูแลระบบ (role = 'admin') — ระงับ / ปลดระงับบัญชีผู้ใช้
# การระงับคือการตั้ง users.status = 'suspended' (ไม่ลบบัญชีและไม่ลบรูป จึงปลดระงับได้)
# บัญชีที่ถูกระงับจะ login ไม่ได้ และ token เดิมใช้ไม่ได้ทันที (ดู user_lookup_loader ใน app/__init__.py)

from functools import wraps
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.user import User
from app.models.image_task import ImageTask

admin_bp = Blueprint('admin', __name__)


def admin_required(fn):
    # ต้อง login และ role ใน DB ต้องเป็น 'admin' (อ่านจาก DB ทุกครั้ง ไม่เชื่อค่าที่ browser ส่งมา)
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'ต้องเป็นผู้ดูแลระบบเท่านั้น'}), 403
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    # รายชื่อผู้ใช้ทั้งหมด พร้อมจำนวนงานเจนรูปของแต่ละคน
    counts = dict(
        db.session.query(ImageTask.user_id, func.count(ImageTask.id)).group_by(ImageTask.user_id).all()
    )
    users = User.query.order_by(User.id).all()
    return jsonify([{**u.to_dict(), 'image_count': counts.get(u.id, 0)} for u in users]), 200


def _set_status(user_id, new_status):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'ไม่พบผู้ใช้นี้'}), 404
    if user.id == current_user.id:
        return jsonify({'error': 'ระงับบัญชีของตัวเองไม่ได้'}), 400
    if user.role == 'admin':
        # กันไม่ให้ admin ระงับกันเองจนไม่เหลือผู้ดูแลระบบ
        return jsonify({'error': 'ระงับบัญชีผู้ดูแลระบบไม่ได้'}), 400

    user.status = new_status
    db.session.commit()
    current_app.logger.info(f"Admin {current_user.username} set user {user.username} status to {new_status}")
    return jsonify(user.to_dict()), 200


@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@admin_required
def suspend_user(user_id):
    return _set_status(user_id, 'suspended')


@admin_bp.route('/users/<int:user_id>/unsuspend', methods=['POST'])
@admin_required
def unsuspend_user(user_id):
    return _set_status(user_id, 'active')
