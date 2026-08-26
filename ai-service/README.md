# AI Service (FastAPI Wrapper สำหรับ Forge Neo)

ห่อ API ของ Forge Neo อีกชั้น เพื่อให้ Flask backend (คนที่ 2) เรียกใช้ได้ง่ายขึ้น
โดยไม่ต้องรู้รายละเอียดของ Forge Neo เลย

## โครงสร้างไฟล์

- `main.py` — จุดเริ่มต้น เปิด endpoint `/generate`, `/chat`, `/health`, `/queue/status`
- `queue_manager.py` — คิวง่ายๆ ด้วย `asyncio.Queue` เก็บงานสร้างรูปทุกงาน (ทั้งจาก
  `/generate` ตรงๆ และจาก chatbot) ให้ทำทีละงานเรียงคิว ไม่ให้ Forge Neo โดนยิง
  พร้อมกันหลายงาน — ไม่ต้องติดตั้ง Redis/Celery เพิ่ม
- `forge_client.py` — ฟังก์ชันคุยกับ Forge Neo โดยตรง (เจนรูป)
- `gemini_client.py` — ตัวกลาง chatbot ใช้ Gemini ตัดสินใจว่าจะตอบข้อความ
  หรือสั่ง Forge Neo ให้เจนรูป (Function Calling)
- `models.py` — กำหนดรูปแบบข้อมูล request/response
- `config.py` — ตั้งค่า URL, timeout, Gemini API key

## วิธีติดตั้ง

1. ให้แน่ใจว่า activate `.venv` ของโปรเจกต์แล้ว
2. ติดตั้ง dependency เพิ่ม (ถ้ายังไม่มี):
   ```
   pip install fastapi uvicorn httpx python-dotenv google-genai
   ```
3. สร้างไฟล์ `.env` ในโฟลเดอร์นี้ (ถูกกันโดย `.gitignore` แล้ว ไม่หลุดขึ้น GitHub):
   ```
   GEMINI_API_KEY=คีย์ของคุณจาก https://aistudio.google.com/apikey
   ```

## วิธีรัน

1. เปิด Forge Neo ทิ้งไว้ก่อน (ผ่าน Stability Matrix ตามที่ setup ไว้) ต้องเห็น
   `Running on local URL: http://127.0.0.1:7860`
2. เปิด terminal อีกอันแยกต่างหาก แล้วรัน:
   ```
   uvicorn main:app --reload --port 8001
   ```
3. เปิด browser ไปที่ `http://127.0.0.1:8001/docs`

## ทดสอบ

- `GET /health` — เช็คว่าเชื่อม Forge Neo ได้อยู่ไหม
- `POST /generate` — ส่ง JSON แบบนี้:
  ```json
  {
    "prompt": "a cute cat sitting on a chair",
    "negative_prompt": "blurry, low quality",
    "steps": 20,
    "width": 512,
    "height": 512
  }
  ```
  จะได้ `image_base64` กลับมา เอาไป decode เป็นรูปได้

- `POST /chat` — คุยกับ chatbot ส่ง JSON แบบนี้:
  ```json
  {
    "session_id": "test-user-1",
    "message": "อยากได้รูปหมาสีดำ"
  }
  ```
  ถ้าเป็นคำถามทั่วไป จะได้ `text` กลับมาเฉยๆ (`image_base64` เป็น `null`)
  ถ้าเป็นคำขอสร้างรูป จะได้ทั้ง `text` (คำตอบจาก Gemini) และ `image_base64`
  (รูปจริงจาก Forge Neo) กลับมาพร้อมกัน — ใช้ `session_id` เดียวกันเพื่อให้
  จำบทสนทนาก่อนหน้าได้ (คนละคนควรใช้คนละ `session_id`)

## ขั้นต่อไป (ยังไม่ทำในเวอร์ชันนี้)

- ~~เพิ่มระบบ Queue~~ ✅ ทำแล้ว (ดู `queue_manager.py` — แบบ `asyncio.Queue` ในตัว
  ไม่ต้องใช้ Redis/Celery เหมาะกับ GPU เดียวที่รับงานได้ทีละ 1 อยู่แล้ว)
- เพิ่ม endpoint `/edit` สำหรับ image-to-image (ฝั่ง Frontend จะทำ filter แบบ
  client-side เองไปก่อน — ยังไม่ต้องทำส่วนนี้จนกว่าจะตกลงกับทีมว่าจำเป็น)
- เพิ่มการเซฟรูปลงไฟล์ + คืน path แทนการส่ง base64 ตรงๆ (รอ Backend ยืนยัน
  รูปแบบ response ที่ต้องการก่อน — ตอนนี้ Backend คาดหวัง `image_url` แต่เรายัง
  ส่ง `image_base64` อยู่)
- ย้าย `_chat_sessions` จาก memory ไปเก็บใน Redis/DB (ตอนนี้ถ้า restart service
  ประวัติคุยหายหมด)
- เพิ่ม field เลือก checkpoint/LoRA ใน `GenerateRequest`

## หมายเหตุเรื่อง Queue

- ตอนนี้ `/generate` ยัง **รอจนกว่าจะเสร็จค่อยตอบกลับ** เหมือนเดิมทุกประการ
  (ไม่ต้องแก้อะไรฝั่ง Backend เลย) การมี queue แค่รับประกันว่าไม่มี 2 งานยิงไปหา
  Forge Neo พร้อมกัน — ถ้ามีคนกดพร้อมกันหลายคน คนหลังจะแค่ **รอคิวนานขึ้น**
  ไม่ error
- ดูจำนวนงานที่รอคิวอยู่ได้ที่ `GET /queue/status`
- ถ้ามีคนรอคิวนานจนเกิน timeout ของฝั่ง Backend (`requests.post(..., timeout=120)`
  ใน `ai_client.py`) จะเจอ error timeout ได้ ถ้าคนใช้งานพร้อมกันเยอะขึ้นในอนาคต
  อาจต้องคุยกับทีมเรื่องเพิ่มค่า timeout
