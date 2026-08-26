"""
Queue Manager — คิวง่ายๆ ด้วย asyncio ล้วนๆ ไม่ต้องติดตั้ง Redis/Celery
========================================================================
ทำไมต้องมีไฟล์นี้: GPU เครื่องเรารับงานสร้างรูปได้ทีละ 1 งานเท่านั้นอยู่แล้ว
ถ้ามีหลาย request ยิงเข้ามาพร้อมกัน (เช่น 3 คนกด Generate พร้อมกัน) แล้วปล่อยให้
ยิงไปหา Forge Neo พร้อมกันตรงๆ อาจชนกันหรือทำให้ Forge Neo error ได้

ไฟล์นี้ทำให้ทุก request ต้อง "ต่อคิว" เข้ามาก่อน แล้วมี worker ตัวเดียวคอยดึงงาน
ออกมาทำทีละงานเรียงตามลำดับ (FIFO) — request ที่มาทีหลังแค่รอนานขึ้น ไม่ error
"""

import asyncio
from models import GenerateRequest
from forge_client import generate_image

# คิวเก็บงานที่รออยู่ — แต่ละ item คือ (request, future ที่จะเก็บผลลัพธ์)
_job_queue: asyncio.Queue = asyncio.Queue()
_worker_started = False


async def _worker():
    """
    วนลูปตลอดอายุของโปรแกรม ดึงงานจากคิวออกมาทำทีละงาน
    เพราะมีแค่ worker เดียว จึงรับประกันว่าไม่มีทาง 2 งานยิงไปหา Forge Neo
    พร้อมกันได้เลย
    """
    while True:
        req, future = await _job_queue.get()
        try:
            result = await generate_image(req)
            if not future.cancelled():
                future.set_result(result)
        except Exception as e:
            # โยน exception เดิมกลับไปให้โค้ดที่เรียก enqueue_generate() จัดการ
            # เหมือนกับเรียก generate_image() ตรงๆ ทุกประการ แค่ผ่านคิวก่อน
            if not future.cancelled():
                future.set_exception(e)
        finally:
            _job_queue.task_done()


def start_worker():
    """เรียกครั้งเดียวตอน FastAPI เริ่มทำงาน (ดูใน main.py, startup event)"""
    global _worker_started
    if not _worker_started:
        asyncio.create_task(_worker())
        _worker_started = True


async def enqueue_generate(req: GenerateRequest) -> dict:
    """
    ใส่งานลงคิว แล้วรอผลลัพธ์ของงานตัวเอง
    ระหว่างรอ ไม่บล็อก event loop ทั้งหมด — request อื่นที่เข้ามาพร้อมกัน
    จะถูกใส่ต่อคิวและรอตามลำดับ ไม่ทำให้ทั้งเซิร์ฟเวอร์ค้าง
    """
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    await _job_queue.put((req, future))
    return await future


def queue_size() -> int:
    """จำนวนงานที่ยังรอคิวอยู่ (ไม่รวมงานที่กำลังทำอยู่ตอนนี้) ไว้ debug/แสดงผล"""
    return _job_queue.qsize()
