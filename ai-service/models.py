"""
Pydantic models — กำหนดว่าข้อมูลที่ API รับเข้า/ส่งออกต้องมีหน้าตายังไง
FastAPI ใช้ตรงนี้ตรวจสอบ (validate) ข้อมูลให้อัตโนมัติ ถ้า client ส่งฟิลด์ผิด type
หรือขาดฟิลด์ที่จำเป็น จะ error ทันทีก่อนเข้าโค้ดของเราเองเลย ไม่ต้องเขียน if เช็คเอง
"""

from pydantic import BaseModel, Field  # ← BaseModel = คลาสแม่ของ model, Field = ตั้งค่าเริ่มต้นและเงื่อนไข
from typing import Optional  # ← Optional = ไม่ส่งมาก็ได้ (เป็น None)


class GenerateRequest(BaseModel):  # ← รูปแบบคำขอสร้างรูป
    """
    รูปแบบข้อมูลที่ client (Flask backend หรือ test-forge-api.html) ต้องส่งมาตอนขอสร้างรูป
    ค่าที่เกินช่วงที่กำหนด (เช่น steps > 150) FastAPI จะตอบ 422 ให้เองก่อนเข้าคิว
    ใช้ใน: main.py -> endpoint POST /generate
    """
    prompt: str = Field(..., min_length=1, description="คำอธิบายรูปที่ต้องการสร้าง")  # ← บังคับส่ง (...) และห้ามเป็นข้อความว่าง
    negative_prompt: str = Field("", description="สิ่งที่ไม่ต้องการให้ปรากฏในรูป")  # ← ไม่บังคับ ถ้าไม่ส่งจะเป็นข้อความว่าง
    steps: int = Field(20, ge=1, le=150, description="จำนวน sampling steps")  # ← เริ่มต้น 20 ต้องอยู่ระหว่าง 1–150
    width: int = Field(512, ge=64, le=2048, description="ความกว้างรูป (px)")  # ← เริ่มต้น 512 ต้องอยู่ระหว่าง 64–2048
    height: int = Field(512, ge=64, le=2048, description="ความสูงรูป (px)")  # ← เริ่มต้น 512 ต้องอยู่ระหว่าง 64–2048
    seed: Optional[int] = Field(-1, description="-1 = สุ่มทุกครั้ง")  # ← -1 = สุ่มใหม่ทุกครั้ง
    task_id: Optional[int] = Field(None, description="ID ของ ImageTask ฝั่ง Backend (ใช้ใน log เท่านั้น)")  # ← เลขงานจาก Backend ใช้ใน log เท่านั้น


class GenerateResponse(BaseModel):  # ← รูปแบบคำตอบเมื่อสำเร็จ
    """
    รูปแบบข้อมูลที่ตอบกลับไปหลังสร้างรูปเสร็จ
    ใช้ใน: main.py -> endpoint POST /generate

    กรณี error main.py ตอบเป็น HTTPException ({"detail": "..."}) ไม่ได้ใช้ model นี้
    success จึงเป็น True เสมอ — Backend อ่านรูปจาก image_base64
    """
    success: bool  # ← True เสมอ
    image_base64: Optional[str] = None  # ← รูป PNG แบบ base64
    elapsed_seconds: Optional[float] = None  # ← เวลาที่ Forge ใช้เจน (วินาที) ไม่รวมเวลารอคิว


class HealthResponse(BaseModel):  # ← คำตอบของ GET /health
    """
    รูปแบบข้อมูลที่ตอบกลับตอนเช็คว่า Forge Neo ยังเชื่อมต่ออยู่ไหม
    ใช้ใน: main.py -> endpoint GET /health
    """
    forge_reachable: bool  # ← ต่อ Forge ได้ไหม
    forge_url: str  # ← URL ของ Forge ที่กำลังใช้
