import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    # อายุ token (ชั่วโมง) — default ของ Flask-JWT-Extended คือ 15 นาที ซึ่งสั้นเกินไปสำหรับการใช้งานจริง
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_EXPIRES_HOURS', '24')))
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Service Connection (Distributed IP)
    # AI Service (FastAPI) รันที่ port 8001 — ตั้งค่าจริงใน .env เป็น IP เครื่อง AI Engineer
    # (Tailscale IP ถ้าใช้ VPN) เช่น AI_SERVICE_URL=http://100.x.x.x:8001
    AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', 'http://127.0.0.1:8001')
    # เวลาที่ Backend ยอมรอ AI Service (วินาที) — ต้องมากกว่า FORGE_TIMEOUT_SECONDS ฝั่ง ai-service
    # เพราะรวมเวลารอคิวด้วย
    AI_SERVICE_TIMEOUT = int(os.environ.get('AI_SERVICE_TIMEOUT', '600'))
