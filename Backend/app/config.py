import os  # ← ใช้อ่านค่า environment variable
from datetime import timedelta  # ← ใช้กำหนดช่วงเวลา (อายุ token)
from dotenv import load_dotenv  # ← ตัวอ่านไฟล์ .env

load_dotenv()  # ← โหลดค่าจากไฟล์ .env เข้าเป็น environment variable

class Config:  # ← ค่าตั้งค่าทั้งหมดของ Backend
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')  # ← คีย์ลับของ Flask
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-key')  # ← คีย์ที่ใช้เซ็น token ถ้ารั่วคนอื่นปลอม token ได้
    # อายุ token (ชั่วโมง) — default ของ Flask-JWT-Extended คือ 15 นาที ซึ่งสั้นเกินไปสำหรับการใช้งานจริง
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_EXPIRES_HOURS', '24')))  # ← token ใช้ได้กี่ชั่วโมง (ค่าเริ่มต้น 24)
    
    # ชื่อผู้ใช้ที่จะได้สิทธิ์ผู้ดูแลระบบ (role = 'admin') — ตั้งใน .env  พิมพ์ให้ตรงตัวพิมพ์เล็ก/ใหญ่
    # ถ้ามีบัญชีชื่อนี้อยู่แล้วจะได้สิทธิ์ตอนเปิด server ถ้ายังไม่มีจะได้สิทธิ์ตอนสมัคร
    # เว้นว่าง = ไม่ตั้ง admin อัตโนมัติ
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '').strip()  # ← ชื่อผู้ใช้ที่จะเป็น admin (.strip() ตัดช่องว่างหัวท้าย)

    # Database — ตอนนี้ใช้ SQLite (ไฟล์ instance/app.db) ถ้าจะใช้ PostgreSQL ให้ตั้ง DATABASE_URL ใน .env
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')  # ← ที่อยู่ฐานข้อมูล ค่าเริ่มต้นคือไฟล์ SQLite ชื่อ app.db
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # ← ปิดฟีเจอร์ที่ไม่ได้ใช้ ลดการใช้หน่วยความจำ
    
    # AI Service (FastAPI) รันที่ port 8001 — ค่า default ใช้ได้เมื่อรันเครื่องเดียวกัน
    # ถ้าอยู่คนละเครื่อง ให้ตั้งใน .env เป็น IP เครื่อง AI Service (IP วง LAN หรือ Tailscale)
    # เช่น AI_SERVICE_URL=http://172.20.x.x:8001  (ระวัง: port 8001 ไม่ใช่ 5000)
    AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', 'http://127.0.0.1:8001')  # ← ที่อยู่ของ AI Service (port 8001)
    # เวลาที่ Backend ยอมรอ AI Service (วินาที) — ต้องมากกว่า FORGE_TIMEOUT_SECONDS ฝั่ง ai-service
    # เพราะรวมเวลารอคิวด้วย
    AI_SERVICE_TIMEOUT = int(os.environ.get('AI_SERVICE_TIMEOUT', '600'))  # ← รอ AI Service ได้นานสุดกี่วินาที รวมเวลารอคิว (ค่าเริ่มต้น 600)
