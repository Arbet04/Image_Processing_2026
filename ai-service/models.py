"""
Pydantic models — กำหนดว่าข้อมูลที่ API รับเข้า/ส่งออกต้องมีหน้าตายังไง
FastAPI ใช้ตรงนี้ตรวจสอบ (validate) ข้อมูลให้อัตโนมัติ ถ้า client ส่งฟิลด์ผิด type
หรือขาดฟิลด์ที่จำเป็น จะ error ทันทีก่อนเข้าโค้ดของเราเองเลย ไม่ต้องเขียน if เช็คเอง
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """
    รูปแบบข้อมูลที่ client (เช่น Flask backend) ต้องส่งมาตอนขอสร้างรูป
    ใช้ใน: main.py -> endpoint POST /generate
    """
    prompt: str = Field(..., min_length=1, description="คำอธิบายรูปที่ต้องการสร้าง")
    negative_prompt: str = Field("", description="สิ่งที่ไม่ต้องการให้ปรากฏในรูป")
    steps: int = Field(20, ge=1, le=150, description="จำนวน sampling steps")
    width: int = Field(512, ge=64, le=2048, description="ความกว้างรูป (px)")
    height: int = Field(512, ge=64, le=2048, description="ความสูงรูป (px)")
    seed: Optional[int] = Field(-1, description="-1 = สุ่มทุกครั้ง")


class GenerateResponse(BaseModel):
    """
    รูปแบบข้อมูลที่ตอบกลับไปหลังสร้างรูปเสร็จ (หรือ error)
    ใช้ใน: main.py -> endpoint POST /generate
    """
    success: bool
    image_base64: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """
    รูปแบบข้อมูลที่ตอบกลับตอนเช็คว่า Forge Neo ยังเชื่อมต่ออยู่ไหม
    ใช้ใน: main.py -> endpoint GET /health
    """
    forge_reachable: bool
    forge_url: str
