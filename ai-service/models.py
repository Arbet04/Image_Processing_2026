"""
Pydantic models — กำหนดว่าข้อมูลที่ API รับเข้า/ส่งออกต้องมีหน้าตายังไง
FastAPI ใช้ตรงนี้ตรวจสอบ (validate) ข้อมูลให้อัตโนมัติ ถ้า client ส่งฟิลด์ผิด type
หรือขาดฟิลด์ที่จำเป็น จะ error ทันทีก่อนเข้าโค้ดของเราเองเลย ไม่ต้องเขียน if เช็คเอง
"""

# ─────────────────────────────────────────────────────────────────────────────
# เส้นทางคำขอใน AI Service: Backend ส่ง POST /generate (JSON) มาที่ port 8001 ผ่าน 5 ขั้นก่อนถึง GPU
#   [1] Uvicorn :8001      เปิด port รับ HTTP จาก Backend (รันด้วย uvicorn main:app --host 0.0.0.0)
#   [2] main.py            FastAPI จับคู่ POST /generate กับฟังก์ชัน generate()
#   [3] models.py          Pydantic ตรวจข้อมูล ผิดตอบ 422 ทันที
#   [4] queue_manager.py   เช็คคิวเต็ม รอถึงตา (เจนทีละรูป FIFO)
#   [5] forge_client.py    httpx ส่งไป Forge Neo /sdapi/v1/txt2img
#   แล้ว Forge Neo (port 7860) ใช้ GPU เจนรูป ตอบกลับเป็น base64 ย้อนทางเดิม [5] → [4] → [2] → Backend
#
# จุดที่คำขอถูกหยุดก่อนถึง GPU:  [หยุด] 422 ข้อมูลผิด · [หยุด] 503 คิวเต็ม · [หยุด] 503 ต่อ Forge ไม่ได้
# ─────────────────────────────────────────────────────────────────────────────
# ไฟล์นี้:    ขั้น [3] — กำหนดรูปแบบข้อมูลเข้า/ออก ให้ Pydantic ตรวจอัตโนมัติ
# รับจาก:    JSON ที่ Backend ส่งมา (FastAPI ในขั้น [2] main.py เป็นคนเรียกใช้)
# ส่งต่อไป:  object GenerateRequest ที่ผ่านการตรวจแล้ว → กลับไปที่ [2] main.py แล้วต่อไป [4] และ [5]
# ถ้าไม่ผ่าน: [หยุด] 422 ตอบกลับทันที คำขอไม่เข้าคิว ไม่ถึง GPU
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field  # ← BaseModel = คลาสแม่ของ model, Field = ตั้งค่าเริ่มต้นและเงื่อนไข
from typing import Optional  # ← Optional = ไม่ส่งมาก็ได้ (เป็น None)


# [3] ข้อมูลขาเข้าจาก Backend — prompt ห้ามว่าง · steps 1–150 · width/height 64–2048 · ไม่ส่งมาใช้ค่าเริ่มต้น
class GenerateRequest(BaseModel):  # ← รูปแบบคำขอสร้างรูป (ข้อมูลที่ Backend ต้องส่งมา)
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


# [2] ข้อมูลขาออกเมื่อสำเร็จ — main.py ใช้ห่อรูปที่ได้จาก [5] ส่งกลับ Backend
class GenerateResponse(BaseModel):  # ← รูปแบบคำตอบเมื่อสำเร็จ (ข้อมูลที่ส่งกลับให้ Backend)
    """
    รูปแบบข้อมูลที่ตอบกลับไปหลังสร้างรูปเสร็จ
    ใช้ใน: main.py -> endpoint POST /generate

    กรณี error main.py ตอบเป็น HTTPException ({"detail": "..."}) ไม่ได้ใช้ model นี้
    success จึงเป็น True เสมอ — Backend อ่านรูปจาก image_base64
    """
    success: bool  # ← True เสมอ (ถ้าไม่สำเร็จ main.py ตอบเป็น error แทน ไม่ได้ใช้ model นี้)
    image_base64: Optional[str] = None  # ← รูป PNG แบบ base64
    elapsed_seconds: Optional[float] = None  # ← เวลาที่ Forge ใช้เจน (วินาที) ไม่รวมเวลารอคิว


# [ตรวจสถานะ] คำตอบของ GET /health
class HealthResponse(BaseModel):  # ← คำตอบของ GET /health
    """
    รูปแบบข้อมูลที่ตอบกลับตอนเช็คว่า Forge Neo ยังเชื่อมต่ออยู่ไหม
    ใช้ใน: main.py -> endpoint GET /health
    """
    forge_reachable: bool  # ← ต่อ Forge ได้ไหม (true/false)
    forge_url: str  # ← URL ของ Forge ที่กำลังใช้
