# AI Service (FastAPI Wrapper สำหรับ Forge Neo)

ห่อ API ของ Forge Neo อีกชั้น เพื่อให้ Flask backend (คนที่ 2) เรียกใช้ได้ง่ายขึ้น
โดยไม่ต้องรู้รายละเอียดของ Forge Neo เลย

## โครงสร้างไฟล์

- `main.py` — จุดเริ่มต้น เปิด endpoint `/generate`, `/health`
- `queue_manager.py` — ต่อคิวงานสร้างรูปด้วย `asyncio.Semaphore` กันงานชนกัน
  เวลามีหลาย request เข้ามาพร้อมกัน (GPU รับงานได้ทีละ 1 งานเท่านั้น)
- `forge_client.py` — ฟังก์ชันคุยกับ Forge Neo โดยตรง (เจนรูป)
- `models.py` — กำหนดรูปแบบข้อมูล request/response
- `config.py` — ตั้งค่า URL ของ Forge Neo, timeout, ขนาดคิว (อ่านจาก `.env`)
- `.env.example` — ตัวอย่างไฟล์ `.env` (คัดลอกเป็น `.env` แล้วแก้ค่า)
- `test-forge-api.html` — หน้าทดสอบยิง `/generate` ตรงๆ โดยไม่ผ่าน Backend

## วิธีติดตั้ง

1. ให้แน่ใจว่า activate `.venv` ของโปรเจกต์แล้ว
2. ติดตั้ง dependency (ถ้ายังไม่มี):
   ```
   pip install -r requirements.txt
   ```

## วิธีรัน

1. เปิด Forge Neo ทิ้งไว้ก่อน (ผ่าน Stability Matrix ตามที่ setup ไว้) ต้องเห็น
   `Running on local URL: http://127.0.0.1:7860`
2. เปิด terminal อีกอันแยกต่างหาก แล้วรัน:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8001
   ```
   **ห้ามลืม `--host 0.0.0.0`** — ถ้าไม่ใส่ ai-service จะรับ request ได้แค่จาก
   เครื่องตัวเองเท่านั้น (localhost) เพื่อนจากเครื่องอื่นในทีมจะยิงมาไม่ได้เลย
3. เปิด browser ไปที่ `http://127.0.0.1:8001/docs` (ทดสอบในเครื่องตัวเอง)

## ให้เพื่อนในทีมเชื่อมต่อเข้ามา (ทดสอบข้ามเครื่อง)

เพื่อนต้องยิงมาที่ `http://<IP เครื่องนี้>:8001/generate` แทน `127.0.0.1` โดย:

1. หา IP เครื่องนี้ด้วย `ipconfig` (Windows) — หรือถ้าใช้ VPN แบบ mesh
   (เช่น Tailscale) ให้ใช้ IP เสมือนที่ VPN ให้มาแทน
2. เปิด Windows Firewall รับ inbound connection พอร์ต 8001 (Windows Security
   → Firewall & network protection → Advanced settings → Inbound Rules →
   New Rule → Port → 8001 → Allow the connection)
3. บอก IP นี้ให้ Backend ใส่ใน `.env` ของเขา (ตัวแปร `AI_SERVICE_URL`)
4. **IP อาจเปลี่ยนทุกครั้งที่ต่อ WiFi ใหม่** (ยกเว้นใช้ VPN แบบ Tailscale ที่ IP
   คงที่) เช็คให้ตรงกันก่อนนัดทดสอบทุกครั้ง

## ทดสอบ

- `GET /health` — เช็คว่าเชื่อม Forge Neo ได้อยู่ไหม
- `POST /generate` — ส่ง JSON แบบนี้:
  ```json
  {
    "prompt": "a cute cat sitting on a chair",
    "negative_prompt": "blurry, low quality",
    "steps": 20,
    "width": 512,
    "height": 512,
    "seed": -1
  }
  ```
  จะได้ `image_base64` กลับมา เอาไป decode เป็นรูปได้
  ถ้าไม่สำเร็จจะได้ HTTP error พร้อม `{"detail": "..."}` — 503 = คิวเต็ม หรือต่อ Forge Neo ไม่ได้, 502 = Forge Neo generate ไม่สำเร็จ

## การตั้งค่า (`.env`)

- `FORGE_BASE_URL` — ปกติ `http://127.0.0.1:7860` (Forge Neo รับเฉพาะจากเครื่องตัวเอง อย่าใส่ IP วง LAN)
- `FORGE_TIMEOUT_SECONDS` — เวลารอ Forge Neo ต่อ 1 รูป (default 300) ต้องน้อยกว่า `AI_SERVICE_TIMEOUT` ฝั่ง Backend
- `MAX_QUEUE_SIZE` — จำนวนงานที่ยอมให้รอคิว (default 3) เกินนี้ตอบ 503 ทันที

## ขั้นต่อไป (ยังไม่ทำในเวอร์ชันนี้)

- เพิ่ม endpoint สำหรับ image-to-image / inpainting / upscale (ถ้าทีมยังต้องการ — ตอนนี้
  หน้าแก้ไขภาพของ Frontend ทำ ลบ/ครอป/ปรับสี/หมุน แบบ client-side เองทั้งหมด)
- เพิ่มการเซฟรูปลงไฟล์ + คืน path/URL แทนการส่ง base64 ตรงๆ (ตอนนี้ Backend เก็บ
  base64 ลงคอลัมน์ `image_url` ใน DB โดยตรง)
- เพิ่ม field เลือก checkpoint/LoRA ใน `GenerateRequest`
