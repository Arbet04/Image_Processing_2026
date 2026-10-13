from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, jwt, cors, setup_logger

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Setup logger
    setup_logger(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.image import image_bp
    from app.routes.admin import admin_bp
    from app.models.user import User

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(image_bp, url_prefix='/api/image')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # ทุก endpoint ที่ใช้ @jwt_required() จะโหลดผู้ใช้จาก DB ผ่านฟังก์ชันนี้ก่อนเสมอ
    # คืน None เมื่อบัญชีไม่มีแล้วหรือไม่ได้ active (เช่นถูกระงับ) -> token เดิมใช้ไม่ได้ทันที
    # ไม่ต้องรอ token หมดอายุ  (ใช้ flask_jwt_extended.current_user เพื่ออ่านผู้ใช้ใน route ได้)
    @jwt.user_lookup_loader
    def load_user(_jwt_header, jwt_data):
        user = db.session.get(User, int(jwt_data['sub']))
        return user if user and user.status == 'active' else None

    @jwt.user_lookup_error_loader
    def user_lookup_error(_jwt_header, _jwt_data):
        # 401 ทำให้หน้าเว็บล้าง session แล้วพากลับไปหน้า login
        message = 'บัญชีนี้ถูกระงับหรือไม่มีอยู่แล้ว กรุณาเข้าสู่ระบบใหม่'
        return jsonify({'error': message, 'msg': message}), 401

    # เช็คว่า Backend ทำงานอยู่ (ไม่ต้อง login) — ใช้ทดสอบว่า nginx ส่งต่อ /api/ มาถึง Backend
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok', 'service': 'Image Processing Backend'}), 200

    if app.config['JWT_SECRET_KEY'] == 'dev-jwt-secret-key' or app.config['SECRET_KEY'] == 'dev-secret-key':
        app.logger.warning("SECRET_KEY/JWT_SECRET_KEY ยังเป็นค่า default — ตั้งค่าใน .env ก่อนใช้งานจริง ไม่งั้นใครก็ปลอม token ได้")

    # Create Database Tables if not exist
    with app.app_context():
        db.create_all()

        # งานที่ค้าง 'processing' ตอนเปิด server แปลว่า server ถูกปิด/crash ระหว่างรอ AI Service
        # จะไม่มีทางเสร็จแล้ว จึงเปลี่ยนเป็น 'failed' ให้หมด
        from app.models.image_task import ImageTask
        stale = ImageTask.query.filter_by(status='processing').update({'status': 'failed'})
        db.session.commit()
        if stale:
            app.logger.warning(f"Marked {stale} stale processing task(s) as failed")

        # ตั้งผู้ดูแลระบบจาก ADMIN_USERNAME ใน .env (ถ้าบัญชีนั้นมีอยู่แล้ว)
        admin_name = app.config['ADMIN_USERNAME']
        if admin_name:
            admin = User.query.filter_by(username=admin_name).first()
            if admin and admin.role != 'admin':
                admin.role = 'admin'
                db.session.commit()
                app.logger.info(f"Granted admin role to user: {admin_name}")
            elif not admin:
                app.logger.warning(f"ADMIN_USERNAME '{admin_name}' ยังไม่มีบัญชี — จะได้สิทธิ์ admin ตอนสมัครด้วยชื่อนี้")

    return app
