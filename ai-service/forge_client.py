"""
ฟังก์ชันคุยกับ Forge Neo โดยตรง
แยกไฟล์นี้ออกมาต่างหาก เพื่อว่าถ้าวันหนึ่งเปลี่ยนไปใช้ ComfyUI หรือ backend อื่น
จะแก้แค่ไฟล์นี้ไฟล์เดียว ไม่ต้องไปยุ่งกับ main.py
"""

import time
import httpx

from config import FORGE_BASE_URL, FORGE_TIMEOUT_SECONDS
from models import GenerateRequest


class ForgeConnectionError(Exception):
    """โยน exception นี้เมื่อเชื่อมต่อ Forge Neo ไม่ได้เลย (ปิดเครื่อง/ยังไม่ได้รัน)"""
    pass


class ForgeGenerationError(Exception):
    """โยน exception นี้เมื่อ Forge Neo ตอบกลับมาแต่เกิด error ระหว่าง generate"""
    pass


async def check_health() -> bool:
    """เช็คว่า Forge Neo ตอบสนองอยู่หรือไม่ ใช้เวลาไม่นาน (timeout สั้น)"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{FORGE_BASE_URL}/sdapi/v1/options")
            return resp.status_code == 200
    except httpx.RequestError:
        return False


async def generate_image(req: GenerateRequest) -> dict:
    """
    ยิง request ไปที่ /sdapi/v1/txt2img ของ Forge Neo
    คืนค่าเป็น dict {image_base64, elapsed_seconds}
    """
    payload = {
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt,
        "steps": req.steps,
        "width": req.width,
        "height": req.height,
        "seed": req.seed,
    }

    start = time.time()

    try:
        async with httpx.AsyncClient(timeout=FORGE_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{FORGE_BASE_URL}/sdapi/v1/txt2img", json=payload)
    except httpx.ConnectError:
        raise ForgeConnectionError(
            f"เชื่อมต่อ Forge Neo ไม่ได้ที่ {FORGE_BASE_URL} — เช็คว่าเปิด Forge Neo ทิ้งไว้หรือยัง"
        )
    except httpx.TimeoutException:
        raise ForgeConnectionError(
            f"Forge Neo ไม่ตอบสนองภายใน {FORGE_TIMEOUT_SECONDS} วินาที — ลองลด steps หรือขนาดรูปดู"
        )

    if resp.status_code != 200:
        raise ForgeGenerationError(f"Forge Neo ตอบกลับผิดพลาด: {resp.status_code} {resp.text[:200]}")

    data = resp.json()
    images = data.get("images")

    if not images:
        raise ForgeGenerationError("ไม่พบรูปภาพใน response จาก Forge Neo")

    elapsed = round(time.time() - start, 2)

    return {
        "image_base64": images[0],
        "elapsed_seconds": elapsed,
    }
