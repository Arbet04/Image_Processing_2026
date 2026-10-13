import logging  # ← ใช้เขียน log
from datetime import datetime, timezone  # ← ใช้อ่านเวลาปัจจุบัน
from flask_sqlalchemy import SQLAlchemy  # ← ตัวเชื่อมฐานข้อมูล
from flask_jwt_extended import JWTManager  # ← ระบบ token (JWT)
from flask_cors import CORS  # ← ตัวจัดการ CORS

db = SQLAlchemy()  # ← ตัวจัดการฐานข้อมูล ทุกไฟล์ import ตัวนี้ไปใช้ร่วมกัน
jwt = JWTManager()  # ← ตัวจัดการ token
cors = CORS()  # ← ตัวจัดการ CORS

def utcnow():  # ← คืนเวลาปัจจุบันแบบ UTC
    # เวลาปัจจุบันแบบ UTC ไม่มี timezone ติด (เหมือน datetime.utcnow() ที่ Python เลิกแนะนำแล้ว)
    return datetime.now(timezone.utc).replace(tzinfo=None)  # ← ตัดข้อมูล timezone ออกเพื่อให้เก็บลงฐานข้อมูลได้เหมือนเดิม

def setup_logger(app):  # ← ตั้งค่า log ของแอป
    logging.basicConfig(  # ← กำหนดรูปแบบ log ทั้งโปรแกรม
        level=logging.INFO,  # ← แสดงตั้งแต่ระดับ INFO ขึ้นไป
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'  # ← รูปแบบ: [เวลา] ระดับ in ไฟล์: ข้อความ
    )
    app.logger.setLevel(logging.INFO)  # ← log ของแอปแสดงตั้งแต่ระดับ INFO
    app.logger.info("Flask Backend initialized")  # ← ข้อความแรกตอนเปิด Backend
