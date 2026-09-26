"""
ตั้งค่าพื้นฐานสำหรับเชื่อมต่อ Forge Neo
ไฟล์นี้ไม่ทำอะไรเป็นพิเศษ แค่เก็บค่าคงที่ไว้ที่เดียว ให้ไฟล์อื่น import ไปใช้
แก้ FORGE_BASE_URL ตรงนี้ถ้าพอร์ตไม่ใช่ 7860
"""

import os
from dotenv import load_dotenv

load_dotenv()  # โหลดค่าจากไฟล์ .env (ถ้ามี) เข้ามาเป็น environment variable

# URL ของ Forge Neo ที่รันอยู่บนเครื่อง (เปลี่ยนได้ผ่าน environment variable FORGE_BASE_URL
# โดยไม่ต้องแก้โค้ด เช่น ตอน deploy คนละเครื่อง)
FORGE_BASE_URL = os.getenv("FORGE_BASE_URL", "http://127.0.0.1:7860")

# เวลาที่ยอมรอ Forge Neo ตอบกลับ (วินาที) — generate รูปอาจใช้เวลานาน ตั้งไว้กว้างๆ
FORGE_TIMEOUT_SECONDS = int(os.getenv("FORGE_TIMEOUT_SECONDS", "300"))

# จำนวนงานสูงสุดที่ยอมให้รอคิวพร้อมกัน (ไม่นับงานที่กำลังทำ) — เกินนี้ตอบ 503 ทันที
# แทนที่จะให้ client รอจน timeout แล้ว GPU ยังเจนรูปที่ไม่มีใครรอรับอยู่
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "3"))

# ค่าเริ่มต้นเวลา client ไม่ระบุมาใน request
DEFAULT_STEPS = 20
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512
