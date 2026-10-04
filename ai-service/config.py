"""
ตั้งค่าพื้นฐานของ ai-service (URL ของ Forge Neo, timeout, ขนาดคิว)
ไฟล์นี้ไม่ทำอะไรเป็นพิเศษ แค่เก็บค่าไว้ที่เดียว ให้ไฟล์อื่น import ไปใช้
ค่าทั้งหมดเปลี่ยนได้ผ่านไฟล์ .env (ดูตัวอย่างใน .env.example) โดยไม่ต้องแก้โค้ด
"""

import os
from dotenv import load_dotenv

load_dotenv()  # โหลดค่าจากไฟล์ .env (ถ้ามี) เข้ามาเป็น environment variable

# URL ของ Forge Neo — ปกติรันอยู่เครื่องเดียวกับ ai-service จึงใช้ 127.0.0.1
# (Forge Neo รับ request จาก 127.0.0.1 เท่านั้น ถ้าใส่ IP วง LAN ของเครื่องตัวเองจะต่อไม่ติด
# เว้นแต่จะเปิด Forge ด้วย --listen)
FORGE_BASE_URL = os.getenv("FORGE_BASE_URL", "http://127.0.0.1:7860")

# เวลาที่ยอมรอ Forge Neo ตอบกลับต่อ 1 รูป (วินาที) — generate รูปอาจใช้เวลานาน ตั้งไว้กว้างๆ
# ต้องน้อยกว่า AI_SERVICE_TIMEOUT ฝั่ง Backend (default 600) เพราะ Backend รอรวมเวลาคิวด้วย
FORGE_TIMEOUT_SECONDS = int(os.getenv("FORGE_TIMEOUT_SECONDS", "300"))

# จำนวนงานสูงสุดที่ยอมให้รอคิวพร้อมกัน (ไม่นับงานที่กำลังทำ) — เกินนี้ตอบ 503 ทันที
# แทนที่จะให้ client รอจน timeout แล้ว GPU ยังเจนรูปที่ไม่มีใครรอรับอยู่
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "3"))

# หมายเหตุ: ค่าเริ่มต้นของ steps / width / height อยู่ใน GenerateRequest (models.py)
