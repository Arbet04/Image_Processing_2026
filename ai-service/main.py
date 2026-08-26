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

from models import GenerateRequest, GenerateResponse, HealthResponse, ChatRequest, ChatResponse
from forge_client import check_health, ForgeConnectionError, ForgeGenerationError
from gemini_client import handle_chat_message
from queue_manager import start_worker, enqueue_generate, queue_size
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


@app.on_event("startup")
async def on_startup():
    # เริ่ม worker ตัวเดียวไว้คอยดึงงานจากคิวมาทำทีละงาน
    start_worker()


@app.get("/health", response_model=HealthResponse)
async def health():
    """เช็คว่า service นี้เชื่อม Forge Neo ได้อยู่ไหม ใช้ debug ตอนอะไรๆ ไม่ทำงาน"""
    reachable = await check_health()
    return HealthResponse(forge_reachable=reachable, forge_url=FORGE_BASE_URL)


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    Endpoint หลักสำหรับสร้างรูปจาก prompt
    รูปแบบ request/response เหมือนเดิมทุกอย่าง ไม่มีอะไรเปลี่ยนสำหรับฝั่ง Backend —
    แค่ข้างในตอนนี้ต่อคิวก่อนยิงหา Forge Neo กันงานชนกันเวลามีหลาย request พร้อมกัน
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


@app.get("/queue/status")
async def queue_status():
    """ดูจำนวนงานที่ยังรอคิวอยู่ตอนนี้ ไว้ debug เวลาสงสัยว่าทำไมช้า"""
    return {"pending_jobs": queue_size()}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Endpoint สำหรับ chatbot — คุยธรรมดาได้ และถ้า user ขอรูป
    Gemini จะตัดสินใจเรียก Forge Neo ให้เองอัตโนมัติ (ดู gemini_client.py)
    """
    try:
        result = await handle_chat_message(req.session_id, req.message)
        return ChatResponse(
            success=True,
            text=result["text"],
            image_base64=result["image_base64"],
        )

    except Exception as e:
        # ครอบกว้างไว้ก่อน เพราะ error จาก Gemini SDK มีหลายแบบ
        # (เช่น API key ผิด, โควตาหมด, network หลุด)
        raise HTTPException(status_code=502, detail=f"Chatbot เกิดข้อผิดพลาด: {str(e)}")


@app.get("/")
async def root():
    return {"message": "AI Service กำลังทำงาน ไปที่ /docs เพื่อทดสอบ API"}
