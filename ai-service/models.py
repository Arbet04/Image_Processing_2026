"""
Pydantic models — ใช้กำหนดรูปแบบข้อมูลที่ API รับเข้า/ส่งออก
FastAPI จะ validate ให้อัตโนมัติ ถ้าฟิลด์ไม่ตรง type จะ error ก่อนเข้าโค้ดเราเอง
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="คำอธิบายรูปที่ต้องการสร้าง")
    negative_prompt: str = Field("", description="สิ่งที่ไม่ต้องการให้ปรากฏในรูป")
    steps: int = Field(20, ge=1, le=150, description="จำนวน sampling steps")
    width: int = Field(512, ge=64, le=2048, description="ความกว้างรูป (px)")
    height: int = Field(512, ge=64, le=2048, description="ความสูงรูป (px)")
    seed: Optional[int] = Field(-1, description="-1 = สุ่มทุกครั้ง")


class GenerateResponse(BaseModel):
    success: bool
    image_base64: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    forge_reachable: bool
    forge_url: str
