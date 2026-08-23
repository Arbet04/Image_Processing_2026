"""
ตั้งค่าพื้นฐานสำหรับเชื่อมต่อ Forge Neo
แก้ FORGE_BASE_URL ตรงนี้ถ้าพอร์ตไม่ใช่ 7860
"""

import os
from dotenv import load_dotenv

load_dotenv()  # โหลดค่าจากไฟล์ .env (เช่น GEMINI_API_KEY) เข้ามาเป็น environment variable

# URL ของ Forge Neo ที่รันอยู่บนเครื่อง (เปลี่ยนได้ผ่าน environment variable FORGE_BASE_URL)
FORGE_BASE_URL = os.getenv("FORGE_BASE_URL", "http://127.0.0.1:7860")

# เวลาที่ยอมรอ Forge Neo ตอบกลับ (วินาที) — generate รูปอาจใช้เวลานาน ตั้งไว้กว้างๆ
FORGE_TIMEOUT_SECONDS = 120

# ค่าเริ่มต้นเวลาไม่ระบุใน request
DEFAULT_STEPS = 20
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512

# --- Gemini (chatbot) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
