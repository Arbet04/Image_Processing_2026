import os
from flask import Flask
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

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(image_bp, url_prefix='/api/image')

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

    return app
