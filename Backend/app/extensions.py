import logging
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def utcnow():
    # เวลาปัจจุบันแบบ UTC ไม่มี timezone ติด (เหมือน datetime.utcnow() ที่ Python เลิกแนะนำแล้ว)
    return datetime.now(timezone.utc).replace(tzinfo=None)

def setup_logger(app):
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    app.logger.setLevel(logging.INFO)
    app.logger.info("Flask Backend initialized")
