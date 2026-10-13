from flask import Blueprint, request, jsonify, current_app  # ← Blueprint = กลุ่ม endpoint, request = คำขอที่เข้ามา, jsonify = ตอบเป็น JSON
from app.extensions import db, utcnow  # ← ฐานข้อมูล และฟังก์ชันเวลา
from app.models.user import User  # ← ตารางผู้ใช้
from flask_jwt_extended import create_access_token, jwt_required, current_user  # ← สร้าง token, บังคับ login, อ่านผู้ใช้ปัจจุบัน

auth_bp = Blueprint('auth', __name__)  # ← กลุ่ม endpoint ของระบบสมาชิก (ต่อจาก /api/auth)

@auth_bp.route('/register', methods=['POST'])  # ← ผูกฟังก์ชันด้านล่างกับ POST /api/auth/register
def register():  # ← สมัครสมาชิก
    data = request.get_json() or {}  # ← อ่าน JSON ที่หน้าเว็บส่งมา ถ้าไม่มีให้เป็น dict ว่าง
    username = data.get('username')  # ← ชื่อผู้ใช้ที่กรอก
    password = data.get('password')  # ← รหัสผ่านที่กรอก

    if not username or not password:  # ← กรอกไม่ครบ
        return jsonify({'error': 'Username and password required'}), 400  # ← ตอบ 400 (คำขอไม่ถูกต้อง)

    if User.query.filter_by(username=username).first():  # ← มีชื่อนี้ในระบบแล้วหรือยัง
        return jsonify({'error': 'Username already exists'}), 400  # ← ตอบ 400 ชื่อซ้ำ

    user = User(username=username)  # ← สร้างผู้ใช้ใหม่ (ยังไม่บันทึก)
    user.set_password(password)  # ← เก็บรหัสผ่านเป็น hash
    # บัญชีที่ชื่อตรงกับ ADMIN_USERNAME ใน .env ได้สิทธิ์ผู้ดูแลระบบ
    if username == current_app.config['ADMIN_USERNAME']:  # ← ชื่อตรงกับ ADMIN_USERNAME ใน .env หรือไม่
        user.role = 'admin'  # ← ให้สิทธิ์ผู้ดูแลระบบ
    db.session.add(user)  # ← เตรียมเพิ่มลงฐานข้อมูล
    db.session.commit()  # ← บันทึกลงฐานข้อมูลจริง

    current_app.logger.info(f"Registered new user: {username}")  # ← เขียน log ว่ามีผู้สมัครใหม่
    return jsonify({'message': 'User registered successfully'}), 201  # ← ตอบ 201 (สร้างสำเร็จ) หน้าเว็บจะสลับไปแท็บเข้าสู่ระบบ

@auth_bp.route('/login', methods=['POST'])  # ← ผูกฟังก์ชันด้านล่างกับ POST /api/auth/login
def login():  # ← เข้าสู่ระบบ
    data = request.get_json() or {}  # ← อ่าน JSON ที่หน้าเว็บส่งมา
    username = data.get('username')  # ← ชื่อผู้ใช้ที่กรอก
    password = data.get('password')  # ← รหัสผ่านที่กรอก

    if not username or not password:  # ← กรอกไม่ครบ
        return jsonify({'error': 'Username and password required'}), 400  # ← ตอบ 400

    user = User.query.filter_by(username=username).first()  # ← หาผู้ใช้จากชื่อ (ตัวพิมพ์เล็ก/ใหญ่ต้องตรง)
    if not user or not user.check_password(password):  # ← ไม่มีชื่อนี้ หรือรหัสผ่านผิด
        return jsonify({'error': 'Invalid username or password'}), 401  # ← ตอบ 401 โดยไม่บอกว่าผิดที่ชื่อหรือรหัสผ่าน

    if user.status != 'active':  # ← บัญชีถูกระงับ
        # ตรวจหลังรหัสผ่านถูกแล้วเท่านั้น คนที่ไม่รู้รหัสผ่านจึงไม่รู้ว่าบัญชีไหนถูกระงับ
        current_app.logger.info(f"Blocked login for suspended user: {username}")  # ← เขียน log ว่ากันการ login ไว้
        return jsonify({'error': 'บัญชีนี้ถูกระงับ กรุณาติดต่อผู้ดูแลระบบ'}), 403  # ← ตอบ 403 พร้อมข้อความว่าถูกระงับ

    user.last_login = utcnow()  # ← จำเวลาที่ login ครั้งนี้
    db.session.commit()  # ← บันทึกลงฐานข้อมูล

    access_token = create_access_token(identity=str(user.id))  # ← สร้าง token ที่ข้างในเก็บเลข id ของผู้ใช้
    current_app.logger.info(f"User logged in: {username}")  # ← เขียน log ว่า login สำเร็จ
    return jsonify({  # ← ตอบ 200 หน้าเว็บจะเก็บข้อมูลนี้ไว้แล้วไปหน้าหลัก
        'access_token': access_token,  # ← หน้าเว็บแนบ token นี้ไปกับทุกคำขอหลังจากนี้
        'user': user.to_dict()  # ← ข้อมูลผู้ใช้ รวม role
    }), 200

@auth_bp.route('/me', methods=['GET'])  # ← ผูกฟังก์ชันด้านล่างกับ GET /api/auth/me
@jwt_required()  # ← ต้องแนบ token ที่ถูกต้อง ไม่งั้นได้ 401
def get_me():  # ← ข้อมูลของผู้ใช้ที่ login อยู่
    # current_user ถูกโหลดจาก DB แล้ว (บัญชีที่ถูกระงับ/ไม่มีอยู่ ถูกตอบ 401 ไปก่อนถึงตรงนี้)
    # หน้าเว็บเรียกตอนเปิดหน้าเพื่ออัปเดต role ล่าสุด
    return jsonify(current_user.to_dict()), 200  # ← ตอบข้อมูลล่าสุดจากฐานข้อมูล
