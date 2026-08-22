"""
FastAPI Wrapper สำหรับ Forge Neo
=================================
งานของไฟล์นี้: เปิด API ของตัวเองให้ Flask backend (คนที่ 2) เรียกใช้
โดยข้างในไปเรียก Forge Neo อีกทีผ่าน forge_client.py

วิธีรัน (ต้องเปิด Forge Neo ทิ้งไว้ก่อน):
    uvicorn main:app --reload --port 8001

ทดสอบ:
    เปิด http://127.0.0.1:8001/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import GenerateRequest, GenerateResponse, HealthResponse
from forge_client import generate_image, check_health, ForgeConnectionError, ForgeGenerationError
from config import FORGE_BASE_URL

app = FastAPI(
    title="Image Processing 2026 - AI Service",
    description="ห่อ API ของ Forge Neo ให้ทีมอื่นเรียกใช้ง่ายขึ้น",
    version="0.1.0",
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
    """เช็คว่า service นี้เชื่อม Forge Neo ได้อยู่ไหม ใช้ debug ตอนอะไรๆ ไม่ทำงาน"""
    reachable = await check_health()
    return HealthResponse(forge_reachable=reachable, forge_url=FORGE_BASE_URL)


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    Endpoint หลักสำหรับสร้างรูปจาก prompt
    ตอนนี้เป็นแบบ synchronous (รอจนเสร็จค่อยตอบกลับ)
    ขั้นต่อไปจะเปลี่ยนเป็นระบบ Queue เพื่อไม่ให้ค้างตอนมีหลาย request พร้อมกัน
    """
    try:
        result = await generate_image(req)
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
    return {"message": "AI Service กำลังทำงาน ไปที่ /docs เพื่อทดสอบ API"}
