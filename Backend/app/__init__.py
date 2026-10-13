from flask import Flask, jsonify  # ← Flask = ตัวแอป, jsonify = แปลง dict เป็นคำตอบ JSON
from app.config import Config  # ← ค่าตั้งค่าจาก config.py
from app.extensions import db, jwt, cors, setup_logger  # ← ฐานข้อมูล, ระบบ token, CORS และตัวตั้งค่า log

def create_app(config_class=Config):  # ← สร้างและประกอบแอปทั้งหมด (ถูกเรียกจาก app.py)
    app = Flask(__name__)  # ← สร้างตัวแอป
    app.config.from_object(config_class)  # ← โหลดค่าตั้งค่าจาก class Config

    # Initialize extensions
    db.init_app(app)  # ← ผูกฐานข้อมูลเข้ากับแอป
    jwt.init_app(app)  # ← ผูกระบบ token (JWT) เข้ากับแอป
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})  # ← อนุญาตให้หน้าเว็บจากที่อยู่อื่นเรียก /api/* ได้
    
    # Setup logger
    setup_logger(app)  # ← ตั้งรูปแบบข้อความ log

    # Register Blueprints
    from app.routes.auth import auth_bp  # ← กลุ่ม endpoint สมัคร/เข้าสู่ระบบ
    from app.routes.image import image_bp  # ← กลุ่ม endpoint สร้างรูป/ประวัติ
    from app.routes.admin import admin_bp  # ← กลุ่ม endpoint ของผู้ดูแลระบบ
    from app.models.user import User  # ← ตารางผู้ใช้

    app.register_blueprint(auth_bp, url_prefix='/api/auth')  # ← URL ที่ขึ้นต้นด้วย /api/auth ไปที่ routes/auth.py
    app.register_blueprint(image_bp, url_prefix='/api/image')  # ← URL ที่ขึ้นต้นด้วย /api/image ไปที่ routes/image.py
    app.register_blueprint(admin_bp, url_prefix='/api/admin')  # ← URL ที่ขึ้นต้นด้วย /api/admin ไปที่ routes/admin.py

    # ทุก endpoint ที่ใช้ @jwt_required() จะโหลดผู้ใช้จาก DB ผ่านฟังก์ชันนี้ก่อนเสมอ
    # คืน None เมื่อบัญชีไม่มีแล้วหรือไม่ได้ active (เช่นถูกระงับ) -> token เดิมใช้ไม่ได้ทันที
    # ไม่ต้องรอ token หมดอายุ  (ใช้ flask_jwt_extended.current_user เพื่ออ่านผู้ใช้ใน route ได้)
    @jwt.user_lookup_loader  # ← ฟังก์ชันด้านล่างถูกเรียกทุกครั้งที่มีคำขอแนบ token มา
    def load_user(_jwt_header, jwt_data):  # ← หาว่า token นี้เป็นของผู้ใช้คนไหน
        user = db.session.get(User, int(jwt_data['sub']))  # ← ค้นผู้ใช้จากเลข id ที่อยู่ใน token (ช่อง 'sub')
        return user if user and user.status == 'active' else None  # ← ไม่มีบัญชีหรือถูกระงับ = คืน None แล้วคำขอนั้นถูกปฏิเสธ

    @jwt.user_lookup_error_loader  # ← ฟังก์ชันด้านล่างถูกเรียกเมื่อ load_user คืน None
    def user_lookup_error(_jwt_header, _jwt_data):  # ← สร้างคำตอบปฏิเสธ
        # 401 ทำให้หน้าเว็บล้าง session แล้วพากลับไปหน้า login
        message = 'บัญชีนี้ถูกระงับหรือไม่มีอยู่แล้ว กรุณาเข้าสู่ระบบใหม่'  # ← ข้อความที่ส่งกลับไปให้หน้าเว็บ
        return jsonify({'error': message, 'msg': message}), 401  # ← ตอบ 401 (หน้าเว็บจะพากลับไปหน้า login)

    # เช็คว่า Backend ทำงานอยู่ (ไม่ต้อง login) — ใช้ทดสอบว่า nginx ส่งต่อ /api/ มาถึง Backend
    @app.route('/api/health', methods=['GET'])  # ← ผูกฟังก์ชันด้านล่างกับ GET /api/health
    def health_check():  # ← เช็คว่า Backend รันอยู่ (ไม่ต้อง login)
        return jsonify({'status': 'ok', 'service': 'Image Processing Backend'}), 200  # ← ตอบ 200 พร้อม status: ok

    if app.config['JWT_SECRET_KEY'] == 'dev-jwt-secret-key' or app.config['SECRET_KEY'] == 'dev-secret-key':  # ← ยังใช้คีย์ลับค่าเริ่มต้นอยู่หรือไม่
        app.logger.warning("SECRET_KEY/JWT_SECRET_KEY ยังเป็นค่า default — ตั้งค่าใน .env ก่อนใช้งานจริง ไม่งั้นใครก็ปลอม token ได้")  # ← เตือนใน log ให้ตั้งค่าใน .env

    # Create Database Tables if not exist
    with app.app_context():  # ← ต้องอยู่ในบล็อกนี้ถึงจะใช้ฐานข้อมูลได้ตอนเปิดแอป
        db.create_all()  # ← สร้างตารางที่ยังไม่มี (ไม่แก้ตารางที่มีอยู่แล้ว)

        # งานที่ค้าง 'processing' ตอนเปิด server แปลว่า server ถูกปิด/crash ระหว่างรอ AI Service
        # จะไม่มีทางเสร็จแล้ว จึงเปลี่ยนเป็น 'failed' ให้หมด
        from app.models.image_task import ImageTask  # ← ตารางงานเจนรูป
        stale = ImageTask.query.filter_by(status='processing').update({'status': 'failed'})  # ← เปลี่ยนงานที่ค้าง 'processing' ให้เป็น 'failed' คืนจำนวนแถวที่เปลี่ยน
        db.session.commit()  # ← บันทึกการเปลี่ยนแปลงลงฐานข้อมูล
        if stale:  # ← ถ้ามีงานค้าง
            app.logger.warning(f"Marked {stale} stale processing task(s) as failed")  # ← แจ้งใน log ว่าเคลียร์ไปกี่งาน

        # ตั้งผู้ดูแลระบบจาก ADMIN_USERNAME ใน .env (ถ้าบัญชีนั้นมีอยู่แล้ว)
        admin_name = app.config['ADMIN_USERNAME']  # ← ชื่อ admin ที่ตั้งไว้ใน .env
        if admin_name:  # ← ถ้าตั้งชื่อไว้
            admin = User.query.filter_by(username=admin_name).first()  # ← หาบัญชีที่ชื่อตรงกัน
            if admin and admin.role != 'admin':  # ← มีบัญชีแล้วแต่ยังไม่เป็น admin
                admin.role = 'admin'  # ← ให้สิทธิ์ผู้ดูแลระบบ
                db.session.commit()  # ← บันทึกลงฐานข้อมูล
                app.logger.info(f"Granted admin role to user: {admin_name}")  # ← แจ้งใน log ว่าให้สิทธิ์แล้ว
            elif not admin:  # ← ยังไม่มีบัญชีชื่อนี้
                app.logger.warning(f"ADMIN_USERNAME '{admin_name}' ยังไม่มีบัญชี — จะได้สิทธิ์ admin ตอนสมัครด้วยชื่อนี้")  # ← เตือนว่าจะได้สิทธิ์ตอนสมัครด้วยชื่อนี้

    return app  # ← ส่งแอปที่ประกอบเสร็จแล้วกลับไปให้ app.py
