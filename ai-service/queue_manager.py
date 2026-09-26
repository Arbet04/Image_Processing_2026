"""
Queue Manager — ต่อคิวงานสร้างรูปด้วย asyncio.Semaphore
============================================================
ทำไมต้องมีไฟล์นี้: GPU เครื่องเรารับงานสร้างรูปได้ทีละ 1 งานเท่านั้น ถ้าปล่อยให้
หลาย request ยิงไปหา Forge Neo พร้อมกันตรงๆ (ไม่ผ่านไฟล์นี้) อาจชนกันหรือทำให้
Forge Neo error ได้ ไฟล์นี้ทำหน้าที่บังคับให้ทุกงานต้อง "รอคิว" ก่อนเริ่มทำงานจริง

หลักการทำงาน (เข้าใจง่ายๆ): Semaphore(1) เหมือนกุญแจห้องน้ำที่มีอยู่ใบเดียว
คนแรกที่มาถึงหยิบกุญแจไปเข้าห้องน้ำ (เริ่ม generate) คนที่มาทีหลังต้องยืนรอ
หน้าห้องจนกว่าคนแรกจะออกมาคืนกุญแจ (generate เสร็จ) ถึงจะเข้าไปทำต่อได้
"""

import asyncio
import logging
from models import GenerateRequest
from forge_client import generate_image
from config import MAX_QUEUE_SIZE

logger = logging.getLogger("uvicorn.error")

# ค่า 1 หมายถึง "อนุญาตให้มีแค่ 1 งานทำพร้อมกันได้เท่านั้น" งานที่มาทีหลัง
# จะถูกทำให้รอโดยอัตโนมัติที่บรรทัด "async with" ด้านล่าง ไม่ต้องเขียน logic คิวเอง
_generation_lock = asyncio.Semaphore(1)

# จำนวนงานที่อยู่ในระบบตอนนี้ (กำลังทำ 1 + รอคิว) — ใช้ตัดสินว่าคิวเต็มหรือยัง
_pending = 0


class QueueFullError(Exception):
    """โยนเมื่อคิวเต็ม main.py จะแปลงเป็น HTTP 503 ให้ client ลองใหม่ภายหลัง"""
    pass


async def enqueue_generate(req: GenerateRequest) -> dict:
    """
    จุดเดียวที่ main.py เรียกใช้ตอนจะสร้างรูป (แทนที่จะเรียก generate_image()
    ตรงๆ) เพื่อให้งานทุกงานต้องผ่านการ "ต่อคิว" นี้ก่อนเสมอ

    รับข้อมูลมาจากไหน: req (GenerateRequest) ถูกส่งเข้ามาจาก main.py

    ฟังก์ชันนี้ส่งต่อไปไหน: เมื่อถึงคิวของตัวเองแล้ว จะเรียก generate_image()
                           ในไฟล์ forge_client.py ให้ไปทำงานสร้างรูปจริง
                           แล้วส่งผลลัพธ์กลับไปให้ main.py ต่อ
    """
    global _pending
    if _pending >= MAX_QUEUE_SIZE + 1:
        raise QueueFullError(f"คิวเต็ม (มีงานรออยู่ {_pending - 1} งาน) กรุณาลองใหม่ภายหลัง")

    _pending += 1
    logger.info(f"Task {req.task_id} queued (in system: {_pending})")
    try:
        async with _generation_lock:
            # โค้ดในบล็อกนี้รับประกันว่ามีแค่ 1 request เท่านั้นที่รันอยู่ในเวลาเดียวกัน
            # request อื่นที่เข้ามาพร้อมกันจะ "ค้างรอ" อยู่ตรงบรรทัด async with ด้านบน
            # โดยอัตโนมัติ จนกว่างานนี้จะทำเสร็จ (ออกจาก block นี้)
            logger.info(f"Task {req.task_id} started")
            return await generate_image(req)
    finally:
        _pending -= 1
