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
    uvicorn main:app --host 0.0.0.0 --port 8001
ทดสอบ: เปิด http://127.0.0.1:8001/docs
"""

from fastapi import FastAPI, HTTPException  # ← FastAPI = ตัวแอป, HTTPException = ตอบ error พร้อม status code
from fastapi.middleware.cors import CORSMiddleware  # ← ตัวจัดการ CORS

from models import GenerateRequest, GenerateResponse, HealthResponse  # ← รูปแบบข้อมูลเข้า/ออก
from forge_client import check_health, ForgeConnectionError, ForgeGenerationError  # ← ฟังก์ชันเช็ค Forge และ error 2 ชนิด
from queue_manager import enqueue_generate, QueueFullError  # ← ฟังก์ชันต่อคิว และ error คิวเต็ม
from config import FORGE_BASE_URL  # ← URL ของ Forge

app = FastAPI(  # ← สร้างแอป (คำสั่ง uvicorn main:app ชี้มาที่ตัวแปรนี้)
    title="Image Processing 2026 - AI Service",  # ← ชื่อที่แสดงในหน้า /docs
    description="ห่อ API ของ Forge Neo ให้ทีมอื่นเรียกใช้ง่ายขึ้น",  # ← คำอธิบายในหน้า /docs
    version="0.2.0",  # ← เวอร์ชันในหน้า /docs
)

# เปิด CORS กว้างๆ ไว้เพื่อให้หน้าทดสอบ test-forge-api.html เรียกจาก browser ได้
# (Flask backend เรียกแบบ server-to-server ไม่เกี่ยวกับ CORS / หน้าเว็บหลักไม่ได้เรียก service นี้ตรงๆ)
# service นี้ไม่มีการตรวจ login — ตอน deploy จริงควรให้เฉพาะเครื่อง Backend เข้าถึง port 8001 ได้
app.add_middleware(  # ← ติดตั้งชั้นที่ทุกคำขอต้องผ่านก่อนถึง endpoint
    CORSMiddleware,  # ← อนุญาตให้หน้าเว็บจากที่อื่นเรียก API นี้ได้
    allow_origins=["*"],  # ← ทุกที่มา
    allow_methods=["*"],  # ← ทุก method (GET, POST, ...)
    allow_headers=["*"],  # ← ทุก header
)


@app.get("/health", response_model=HealthResponse)  # ← ผูกฟังก์ชันด้านล่างกับ GET /health
async def health():  # ← เช็คว่าต่อ Forge ได้ไหม
    """
    เช็คว่า service นี้เชื่อม Forge Neo ได้อยู่ไหม ใช้ debug ตอนอะไรๆ ไม่ทำงาน

    ส่งงานต่อไปที่: check_health() ในไฟล์ forge_client.py
    """
    reachable = await check_health()  # ← ถาม Forge ว่ายังอยู่ไหม
    return HealthResponse(forge_reachable=reachable, forge_url=FORGE_BASE_URL)  # ← ตอบว่าต่อ Forge ได้ไหม (FastAPI แปลงเป็น JSON ให้)


@app.post("/generate", response_model=GenerateResponse)  # ← ผูกฟังก์ชันด้านล่างกับ POST /generate (endpoint หลักที่ Backend เรียก)
async def generate(req: GenerateRequest):  # ← FastAPI ตรวจข้อมูลให้ก่อนเข้าฟังก์ชัน (ผิด = ตอบ 422)
    """
    Endpoint หลักของทั้งระบบ — รับ prompt จาก client (Flask backend:
    Backend/app/services/ai_client.py) แล้วสร้างรูปกลับไปให้

    ถ้าไม่สำเร็จจะตอบเป็น HTTP error พร้อม {"detail": "ข้อความ"}:
      503 = คิวเต็ม หรือ ต่อ Forge Neo ไม่ได้/หมดเวลา, 502 = Forge Neo generate ไม่สำเร็จ

    ส่งงานต่อไปที่: enqueue_generate() ในไฟล์ queue_manager.py
                    (ซึ่งข้างในจะไปเรียก generate_image() ในไฟล์ forge_client.py
                    อีกทีหนึ่ง เพื่อคุยกับ Forge Neo จริงๆ)
    """
    try:  # ← ลองเจนรูป ถ้าพลาดไปที่ except ตามชนิดของปัญหา
        result = await enqueue_generate(req)  # ← เข้าคิว แล้วรอจนได้รูป (await = คืนการทำงานให้ event loop ระหว่างรอ)
        return GenerateResponse(  # ← ตอบ 200 พร้อมรูป
            success=True,  # ← บอกว่าสำเร็จ
            image_base64=result["image_base64"],  # ← รูปแบบ base64
            elapsed_seconds=result["elapsed_seconds"],  # ← เวลาที่ใช้เจน
        )

    except QueueFullError as e:  # ← คิวเต็ม
        # คิวเต็ม — ตอบ 503 ทันทีแทนการให้ client รอจน timeout
        raise HTTPException(status_code=503, detail=str(e))  # ← ตอบ 503 (Service Unavailable) พร้อมข้อความในช่อง detail

    except ForgeConnectionError as e:  # ← ต่อ Forge ไม่ได้ หรือหมดเวลา
        # Forge Neo ไม่ได้เปิดอยู่ หรือ timeout — ส่ง 503 (Service Unavailable) กลับไป
        raise HTTPException(status_code=503, detail=str(e))  # ← ตอบ 503 (Service Unavailable)

    except ForgeGenerationError as e:  # ← Forge เจนไม่สำเร็จ
        # Forge Neo เปิดอยู่แต่ generate ไม่สำเร็จ — ส่ง 502 (Bad Gateway) กลับไป
        raise HTTPException(status_code=502, detail=str(e))  # ← ตอบ 502 (Bad Gateway)


@app.get("/")  # ← ผูกฟังก์ชันด้านล่างกับ GET /
async def root():  # ← หน้าแรก ใช้เช็คว่า service เปิดอยู่
    """หน้าแรกไว้เช็คเฉยๆ ว่า service รันอยู่ ไม่ได้ทำงานอะไรต่อ"""
    return {"message": "AI Service กำลังทำงาน ไปที่ /docs เพื่อทดสอบ API"}  # ← บอกว่า service รันอยู่
