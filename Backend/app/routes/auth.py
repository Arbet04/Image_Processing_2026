from flask import Blueprint, request, jsonify, current_app
from app.extensions import db, utcnow
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username)
    user.set_password(password)
    # บัญชีที่ชื่อตรงกับ ADMIN_USERNAME ใน .env ได้สิทธิ์ผู้ดูแลระบบ
    if username == current_app.config['ADMIN_USERNAME']:
        user.role = 'admin'
    db.session.add(user)
    db.session.commit()

    current_app.logger.info(f"Registered new user: {username}")
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    if user.status != 'active':
        # ตรวจหลังรหัสผ่านถูกแล้วเท่านั้น คนที่ไม่รู้รหัสผ่านจึงไม่รู้ว่าบัญชีไหนถูกระงับ
        current_app.logger.info(f"Blocked login for suspended user: {username}")
        return jsonify({'error': 'บัญชีนี้ถูกระงับ กรุณาติดต่อผู้ดูแลระบบ'}), 403

    user.last_login = utcnow()
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    current_app.logger.info(f"User logged in: {username}")
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    # current_user ถูกโหลดจาก DB แล้ว (บัญชีที่ถูกระงับ/ไม่มีอยู่ ถูกตอบ 401 ไปก่อนถึงตรงนี้)
    # หน้าเว็บเรียกตอนเปิดหน้าเพื่ออัปเดต role ล่าสุด
    return jsonify(current_user.to_dict()), 200
