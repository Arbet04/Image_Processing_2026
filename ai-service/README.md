# AI Service (FastAPI Wrapper สำหรับ Forge Neo)

ห่อ API ของ Forge Neo อีกชั้น เพื่อให้ Flask backend (คนที่ 2) เรียกใช้ได้ง่ายขึ้น
โดยไม่ต้องรู้รายละเอียดของ Forge Neo เลย

## โครงสร้างไฟล์

- `main.py` — จุดเริ่มต้น เปิด endpoint `/generate`, `/health`
- `forge_client.py` — ฟังก์ชันคุยกับ Forge Neo โดยตรง
- `models.py` — กำหนดรูปแบบข้อมูล request/response
- `config.py` — ตั้งค่า URL และ timeout

## วิธีติดตั้ง

1. ให้แน่ใจว่า activate `.venv` ของโปรเจกต์แล้ว
2. ติดตั้ง dependency เพิ่ม (ถ้ายังไม่มี):
   ```
   pip install fastapi uvicorn httpx
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

## ขั้นต่อไป (ยังไม่ทำในเวอร์ชันนี้)

- เพิ่มระบบ Queue (Celery + Redis) กัน endpoint ค้างเวลามีหลาย request พร้อมกัน
- เพิ่ม endpoint `/edit` สำหรับ image-to-image
- เพิ่มการเซฟรูปลงไฟล์ + คืน path แทนการส่ง base64 ตรงๆ (ประหยัด bandwidth เวลารูปใหญ่)
