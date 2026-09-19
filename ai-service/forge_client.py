"""
Forge Client — ไฟล์เดียวในโปรเจกต์ที่ "รู้จัก" Forge Neo โดยตรง
====================================================================
หลักการ: ไฟล์อื่น (main.py, queue_manager.py) ไม่จำเป็นต้องรู้เลยว่า
Forge Neo มี endpoint ชื่ออะไร ส่ง JSON รูปแบบไหน — แค่เรียกใช้ 2 ฟังก์ชัน
ในไฟล์นี้ก็พอ ถ้าวันหนึ่งเปลี่ยนไปใช้เอนจินสร้างรูปตัวอื่น ก็แก้แค่ไฟล์นี้
ไฟล์เดียว ไฟล์อื่นไม่กระทบเลย
"""

import time
import httpx

from config import FORGE_BASE_URL, FORGE_TIMEOUT_SECONDS
from models import GenerateRequest


class ForgeConnectionError(Exception):
    """
    โยน exception นี้เมื่อ "เชื่อมต่อ Forge Neo ไม่ได้เลย"
    (เช่น ยังไม่ได้เปิด Forge Neo ทิ้งไว้ หรือรอนานเกินไปจนหมดเวลา)
    ไฟล์ main.py จะจับ exception นี้แล้วตอบกลับเป็น HTTP 503
    """
    pass


class ForgeGenerationError(Exception):
    """
    โยน exception นี้เมื่อ "เชื่อมต่อได้ แต่ Forge Neo ทำงานไม่สำเร็จ"
    (เช่น checkpoint หาย, parameter ผิด, ไม่มีรูปกลับมา)
    ไฟล์ main.py จะจับ exception นี้แล้วตอบกลับเป็น HTTP 502
    """
    pass


async def check_health() -> bool:
    """
    เช็คแบบเร็วๆ ว่า Forge Neo ยังตอบสนองอยู่หรือไม่ (timeout แค่ 5 วินาที)

    ใครเรียกใช้ฟังก์ชันนี้: main.py -> endpoint GET /health
    ฟังก์ชันนี้ส่งต่อไปไหน: ไม่มี ทำงานจบในตัวเอง แค่คืนค่า True/False กลับไป
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{FORGE_BASE_URL}/sdapi/v1/options")
            return resp.status_code == 200
    except httpx.RequestError:
        # เชื่อมต่อไม่ได้ไม่ว่าด้วยเหตุผลอะไร (ปิดเครื่อง, ผิด URL, ฯลฯ) ถือว่าไม่พร้อมใช้งาน
        return False


async def generate_image(req: GenerateRequest) -> dict:
    """
    ฟังก์ชันหลัก — ยิง request ไปที่ /sdapi/v1/txt2img ของ Forge Neo เพื่อสร้างรูปจริง

    รับข้อมูลมาจากไหน: req (ชนิด GenerateRequest จาก models.py) ถูกส่งเข้ามาจาก
                       queue_manager.py (ซึ่งได้รับต่อมาจาก main.py อีกที)

    ฟังก์ชันนี้ส่งต่อไปไหน: คืนค่า dict {image_base64, elapsed_seconds} กลับไปให้
                           queue_manager.py แล้วไหลต่อไปที่ main.py เพื่อตอบ client

    ถ้ามีปัญหา: โยน ForgeConnectionError หรือ ForgeGenerationError ออกไป ให้
               main.py เป็นคนจับแล้วแปลงเป็น HTTP error code ที่เหมาะสมต่อไป
    """
    # ประกอบข้อมูลให้ตรงตามรูปแบบที่ Forge Neo (สไตล์ A1111 API) ต้องการ
    payload = {
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt,
        "steps": req.steps,
        "width": req.width,
        "height": req.height,
        "seed": req.seed,
    }

    start = time.time()  # จับเวลาเริ่มต้น ไว้คำนวณว่า generate ใช้เวลาเท่าไร

    try:
        async with httpx.AsyncClient(timeout=FORGE_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{FORGE_BASE_URL}/sdapi/v1/txt2img", json=payload)

    except httpx.ConnectError:
        # กรณีที่ 1: หา Forge Neo ไม่เจอเลย (ปิดเครื่องอยู่ / ผิดพอร์ต)
        raise ForgeConnectionError(
            f"เชื่อมต่อ Forge Neo ไม่ได้ที่ {FORGE_BASE_URL} — เช็คว่าเปิด Forge Neo ทิ้งไว้หรือยัง"
        )
    except httpx.TimeoutException:
        # กรณีที่ 2: เจอ Forge Neo แต่มันตอบช้าเกินไป (เกิน FORGE_TIMEOUT_SECONDS)
        raise ForgeConnectionError(
            f"Forge Neo ไม่ตอบสนองภายใน {FORGE_TIMEOUT_SECONDS} วินาที — ลองลด steps หรือขนาดรูปดู"
        )

    if resp.status_code != 200:
        # กรณีที่ 3: Forge Neo ตอบกลับมาแต่ status code ไม่ใช่ 200 (มีบางอย่างผิดพลาด)
        raise ForgeGenerationError(f"Forge Neo ตอบกลับผิดพลาด: {resp.status_code} {resp.text[:200]}")

    data = resp.json()
    images = data.get("images")

    if not images:
        # กรณีที่ 4: status code 200 แต่ไม่มีรูปแนบมาด้วย (ผิดปกติ)
        raise ForgeGenerationError("ไม่พบรูปภาพใน response จาก Forge Neo")

    elapsed = round(time.time() - start, 2)

    # ส่งผลลัพธ์กลับเป็น dict ธรรมดา (ไม่ใช่ Pydantic model) เพราะจุดนี้เป็นแค่
    # ข้อมูลภายในที่ queue_manager.py กับ main.py จะเอาไปแปลงเป็น response เองอีกที
    return {
        "image_base64": images[0],
        "elapsed_seconds": elapsed,
    }
