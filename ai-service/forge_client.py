"""
Forge Client — ไฟล์เดียวในโปรเจกต์ที่ "รู้จัก" Forge Neo โดยตรง
====================================================================
หลักการ: ไฟล์อื่น (main.py, queue_manager.py) ไม่จำเป็นต้องรู้เลยว่า
Forge Neo มี endpoint ชื่ออะไร ส่ง JSON รูปแบบไหน — แค่เรียกใช้ 2 ฟังก์ชัน
ในไฟล์นี้ก็พอ ถ้าวันหนึ่งเปลี่ยนไปใช้เอนจินสร้างรูปตัวอื่น ก็แก้แค่ไฟล์นี้
ไฟล์เดียว ไฟล์อื่นไม่กระทบเลย
"""

import time  # ← ใช้จับเวลา
import httpx  # ← ตัวส่ง HTTP ไปหา server อื่น ใช้กับ await ได้

from config import FORGE_BASE_URL, FORGE_TIMEOUT_SECONDS  # ← ค่าตั้งค่าจาก config.py
from models import GenerateRequest  # ← รูปแบบคำขอจาก models.py


class ForgeConnectionError(Exception):  # ← ต่อ Forge ไม่ได้เลย (main.py ตอบ 503)
    """
    โยน exception นี้เมื่อ "เชื่อมต่อ Forge Neo ไม่ได้เลย"
    (เช่น ยังไม่ได้เปิด Forge Neo ทิ้งไว้ หรือรอนานเกินไปจนหมดเวลา)
    ไฟล์ main.py จะจับ exception นี้แล้วตอบกลับเป็น HTTP 503
    """
    pass  # ← ไม่มีโค้ดเพิ่ม ใช้แค่ชื่อคลาสแยกประเภทปัญหา


class ForgeGenerationError(Exception):  # ← ต่อได้ แต่ Forge ทำงานไม่สำเร็จ (main.py ตอบ 502)
    """
    โยน exception นี้เมื่อ "เชื่อมต่อได้ แต่ Forge Neo ทำงานไม่สำเร็จ"
    (เช่น checkpoint หาย, parameter ผิด, ไม่มีรูปกลับมา)
    ไฟล์ main.py จะจับ exception นี้แล้วตอบกลับเป็น HTTP 502
    """
    pass  # ← ไม่มีโค้ดเพิ่ม ใช้แค่ชื่อคลาสบอกชนิดของปัญหา


async def check_health() -> bool:  # ← เช็คว่า Forge ยังตอบอยู่ไหม คืน True/False
    """
    เช็คแบบเร็วๆ ว่า Forge Neo ยังตอบสนองอยู่หรือไม่ (timeout แค่ 5 วินาที)

    ใครเรียกใช้ฟังก์ชันนี้: main.py -> endpoint GET /health
    ฟังก์ชันนี้ส่งต่อไปไหน: ไม่มี ทำงานจบในตัวเอง แค่คืนค่า True/False กลับไป
    """
    try:  # ← ลองถาม Forge ถ้าต่อไม่ได้ไปที่ except
        async with httpx.AsyncClient(timeout=5) as client:  # ← ตัวส่ง HTTP ชั่วคราว รอได้ 5 วินาที
            resp = await client.get(f"{FORGE_BASE_URL}/sdapi/v1/options")  # ← ถาม Forge ที่ /sdapi/v1/options (await = รอคำตอบ)
            return resp.status_code == 200  # ← ตอบ 200 = พร้อมใช้งาน
    except httpx.RequestError:  # ← ต่อไม่ได้ ไม่ว่าด้วยเหตุผลใด
        # เชื่อมต่อไม่ได้ไม่ว่าด้วยเหตุผลอะไร (ปิดเครื่อง, ผิด URL, ฯลฯ) ถือว่าไม่พร้อมใช้งาน
        return False  # ← ถือว่าไม่พร้อม


async def generate_image(req: GenerateRequest) -> dict:  # ← ฟังก์ชันหลัก: ส่งคำขอเจนรูปไป Forge
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
    payload = {  # ← ข้อมูลที่จะส่งให้ Forge (ชื่อ key ตามที่ Forge กำหนด)
        "prompt": req.prompt,  # ← คำอธิบายรูป
        "negative_prompt": req.negative_prompt,  # ← สิ่งที่ไม่อยากให้มีในรูป
        "steps": req.steps,  # ← จำนวนรอบที่ใช้ปรับภาพ
        "width": req.width,  # ← ความกว้าง (px)
        "height": req.height,  # ← ความสูง (px)
        "seed": req.seed,  # ← เลขสุ่ม (-1 = สุ่มใหม่)
    }

    start = time.time()  # จับเวลาเริ่มต้น ไว้คำนวณว่า generate ใช้เวลาเท่าไร

    try:  # ← ลองส่งคำขอ ถ้าต่อไม่ได้ไปที่ except
        async with httpx.AsyncClient(timeout=FORGE_TIMEOUT_SECONDS) as client:  # ← รอได้นานสุดตามค่าใน config (300 วินาที)
            resp = await client.post(f"{FORGE_BASE_URL}/sdapi/v1/txt2img", json=payload)  # ← ส่งไป Forge แล้วรอจน GPU เจนเสร็จ (ระหว่าง await นี้ event loop ไปทำงานอื่นได้)

    except httpx.ConnectError:  # ← หา Forge ไม่เจอ เช่น ยังไม่ได้เปิด หรือผิด port
        # กรณีที่ 1: หา Forge Neo ไม่เจอเลย (ปิดเครื่องอยู่ / ผิดพอร์ต)
        raise ForgeConnectionError(  # ← โยนปัญหาขึ้นไปให้ main.py
            f"เชื่อมต่อ Forge Neo ไม่ได้ที่ {FORGE_BASE_URL} — เช็คว่าเปิด Forge Neo ทิ้งไว้หรือยัง"
        )
    except httpx.TimeoutException:  # ← Forge ตอบช้าเกินกำหนด
        # กรณีที่ 2: เจอ Forge Neo แต่มันตอบช้าเกินไป (เกิน FORGE_TIMEOUT_SECONDS)
        raise ForgeConnectionError(  # ← โยนปัญหาขึ้นไปให้ main.py
            f"Forge Neo ไม่ตอบสนองภายใน {FORGE_TIMEOUT_SECONDS} วินาที — ลองลด steps หรือขนาดรูปดู"
        )

    if resp.status_code != 200:  # ← Forge ตอบรหัสอื่นที่ไม่ใช่ 200
        # กรณีที่ 3: Forge Neo ตอบกลับมาแต่ status code ไม่ใช่ 200 (มีบางอย่างผิดพลาด)
        raise ForgeGenerationError(f"Forge Neo ตอบกลับผิดพลาด: {resp.status_code} {resp.text[:200]}")  # ← แนบรหัสและข้อความ 200 ตัวอักษรแรก

    data = resp.json()  # ← แปลง JSON เป็น dict
    images = data.get("images")  # ← หยิบรายการรูป (ถ้าไม่มีจะได้ None)

    if not images:  # ← ไม่มีรูปกลับมา
        # กรณีที่ 4: status code 200 แต่ไม่มีรูปแนบมาด้วย (ผิดปกติ)
        raise ForgeGenerationError("ไม่พบรูปภาพใน response จาก Forge Neo")  # ← ถือว่าเจนไม่สำเร็จ

    elapsed = round(time.time() - start, 2)  # ← เวลาที่ใช้ ปัด 2 ตำแหน่ง

    # ส่งผลลัพธ์กลับเป็น dict ธรรมดา (ไม่ใช่ Pydantic model) เพราะจุดนี้เป็นแค่
    # ข้อมูลภายในที่ queue_manager.py กับ main.py จะเอาไปแปลงเป็น response เองอีกที
    return {  # ← ส่งผลกลับให้ queue_manager.py แล้วต่อไปที่ main.py
        "image_base64": images[0],  # ← รูปแรก (เราขอทีละ 1 รูป)
        "elapsed_seconds": elapsed,  # ← เวลาที่ใช้เจน
    }
