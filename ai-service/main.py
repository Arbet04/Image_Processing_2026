"""
Main API — ประตูหน้าบ้านของ ai-service
==========================================
มีหน้าที่แค่ 3 อย่าง: รับ request เข้ามา -> ส่งต่อให้ไฟล์อื่นทำงานจริง ->
เอาผลลัพธ์มาตอบกลับ ไฟล์นี้เองไม่ยุ่งกับรายละเอียดของ Forge Neo เลย

Endpoint ที่มี:
  POST /generate  -> ส่ง prompt เข้ามา ได้รูปกลับเป็น base64
  GET  /health    -> เช็คว่าเชื่อม Forge Neo ได้อยู่ไหม
  GET  /          -> เช็คเฉยๆ ว่า service ตัวนี้รันอยู่

วิธีรัน (ต้องเปิด Forge Neo ทิ้งไว้ก่อนเสมอ):
    uvicorn main:app --reload --port 8001
ทดสอบ: เปิด http://127.0.0.1:8001/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import GenerateRequest, GenerateResponse, HealthResponse
from forge_client import check_health, ForgeConnectionError, ForgeGenerationError
from queue_manager import enqueue_generate
from config import FORGE_BASE_URL

app = FastAPI(
    title="Image Processing 2026 - AI Service",
    description="ห่อ API ของ Forge Neo ให้ทีมอื่นเรียกใช้ง่ายขึ้น",
    version="0.2.0",
)

# เปิด CORS กว้างๆ ไว้ก่อนตอน dev เพื่อให้ frontend/Flask เรียกจากคนละพอร์ตได้
# ตอน deploy จริงควรจำกัด origin ให้แคบลง
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    เช็คว่า service นี้เชื่อม Forge Neo ได้อยู่ไหม ใช้ debug ตอนอะไรๆ ไม่ทำงาน

    ส่งงานต่อไปที่: check_health() ในไฟล์ forge_client.py
    """
    reachable = await check_health()
    return HealthResponse(forge_reachable=reachable, forge_url=FORGE_BASE_URL)


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    Endpoint หลักของทั้งระบบ — รับ prompt จาก client (เช่น Flask backend)
    แล้วสร้างรูปกลับไปให้

    ส่งงานต่อไปที่: enqueue_generate() ในไฟล์ queue_manager.py
                    (ซึ่งข้างในจะไปเรียก generate_image() ในไฟล์ forge_client.py
                    อีกทีหนึ่ง เพื่อคุยกับ Forge Neo จริงๆ)
    """
    try:
        result = await enqueue_generate(req)
        return GenerateResponse(
            success=True,
            image_base64=result["image_base64"],
            elapsed_seconds=result["elapsed_seconds"],
        )

    except ForgeConnectionError as e:
        # Forge Neo ไม่ได้เปิดอยู่ หรือ timeout — ส่ง 503 (Service Unavailable) กลับไป
        raise HTTPException(status_code=503, detail=str(e))

    except ForgeGenerationError as e:
        # Forge Neo เปิดอยู่แต่ generate ไม่สำเร็จ — ส่ง 502 (Bad Gateway) กลับไป
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/")
async def root():
    """หน้าแรกไว้เช็คเฉยๆ ว่า service รันอยู่ ไม่ได้ทำงานอะไรต่อ"""
    return {"message": "AI Service กำลังทำงาน ไปที่ /docs เพื่อทดสอบ API"}
