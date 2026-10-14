# AI Service (FastAPI ห่อ Forge Neo)

รับคำขอเจนรูปจาก Backend ต่อคิวให้เจนทีละรูป แล้วส่งต่อให้ Forge Neo ตัว AI Service เองไม่ได้เจนรูป จึงไม่ต้องติดตั้ง torch

```
Backend ──► [1] Uvicorn :8001 ──► [2] main.py ──► [3] models.py ──► [4] queue_manager.py ──► [5] forge_client.py ──► Forge Neo :7860
```

**ต้องรันบนเครื่องเดียวกับ Forge Neo** (เครื่องที่มี GPU)

---

## 1. สิ่งที่ต้องมีก่อน

- Python 3.11 ขึ้นไป (ทดสอบกับ 3.13) — เช็คด้วย `py -3 --version`
- Forge Neo ติดตั้งผ่าน Stability Matrix และมี checkpoint อย่างน้อย 1 ตัว
- clone โปรเจคแล้ว (ดู [README หลัก](../README.md))

---

## 2. ติดตั้ง (ทำครั้งแรกครั้งเดียว)

เปิด PowerShell ที่โฟลเดอร์โปรเจค แล้วรันทีละบรรทัด:

```powershell
cd ai-service
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

| บรรทัด | ทำอะไร |
|---|---|
| `py -3 -m venv .venv` | สร้าง virtual environment ในโฟลเดอร์ `ai-service\.venv` |
| `Activate.ps1` | เปิดใช้ venv — บรรทัดคำสั่งจะขึ้น `(.venv)` นำหน้า |
| `pip install -r requirements.txt` | ติดตั้ง fastapi, uvicorn, pydantic, httpx, python-dotenv |
| `Copy-Item .env.example .env` | สร้างไฟล์ตั้งค่า (ค่าเริ่มต้นใช้ได้เลย ไม่ต้องแก้) |

ถ้าเคยติดตั้ง package ไว้ใน `.venv` ที่โฟลเดอร์โปรเจค (root) แล้ว ใช้ตัวนั้นต่อได้ — activate ด้วย `..\.venv\Scripts\Activate.ps1` แทน

ถ้า `Activate.ps1` ขึ้น error `running scripts is disabled on this system` ให้รันคำสั่งนี้ครั้งเดียว แล้ว activate ใหม่:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 3. ตั้งค่า (`.env`)

### ไฟล์ `.env` ไม่ได้อยู่ใน Git — ต้องสร้างเองทุกเครื่อง

- `.env` เก็บค่าเฉพาะเครื่อง จึงอยู่ใน `.gitignore` — clone หรือ pull มาแล้ว **จะไม่มีไฟล์นี้**
- ใน Git มีแค่ `.env.example` ซึ่งเป็นตัวอย่าง ใช้คัดลอกเป็น `.env` (บรรทัดสุดท้ายของข้อ 2)
- เช็คว่าสร้างแล้ว (ใน `ai-service`): `Test-Path .env` ต้องได้ `True`
- เช็คว่า Git ไม่เห็นไฟล์นี้: `git status` ต้อง **ไม่มี** `ai-service/.env` ในรายการ
- ถ้าลืมสร้าง AI Service ยังรันได้ เพราะ `config.py` มีค่าเริ่มต้นเท่ากับ `.env.example` แต่ควรสร้างไว้เพื่อแก้ค่าได้
- ห้าม commit หรือส่งไฟล์ `.env` ให้คนอื่น ถ้าเผลอ `git add` ไปแล้ว ให้เอาออกด้วย `git rm --cached .env`

### ค่าใน `.env`

| ตัวแปร | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `FORGE_BASE_URL` | `http://127.0.0.1:7860` | ที่อยู่ Forge Neo — ใช้ `127.0.0.1` เสมอ (Forge รับเฉพาะจากเครื่องตัวเอง) |
| `FORGE_TIMEOUT_SECONDS` | `300` | รอ Forge ได้นานสุดต่อ 1 รูป ต้องน้อยกว่า `AI_SERVICE_TIMEOUT` ของ Backend (600) |
| `MAX_QUEUE_SIZE` | `3` | จำนวนงานที่รอคิวได้ (ไม่นับงานที่กำลังเจน) เกินนี้ตอบ 503 ทันที |

แก้ `.env` แล้วต้องปิด AI Service (Ctrl+C) แล้วเปิดใหม่

---

## 4. รัน (ทำทุกครั้ง)

### 4.1 เปิด Forge Neo ก่อน

เปิดผ่าน Stability Matrix แล้วรอจนหน้าต่าง log ขึ้น:

```
Running on local URL:  http://127.0.0.1:7860
```

### 4.2 เปิด AI Service (terminal ใหม่)

```powershell
cd ai-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

ต้องเห็น:

```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

- `--host 0.0.0.0` **ห้ามลืม** — ถ้าไม่ใส่ Backend ที่อยู่เครื่องอื่นจะต่อไม่ได้
- เปิด terminal นี้ทิ้งไว้ตลอด log ของคิว เช่น `Task 5 queued`, `Task 5 started` จะขึ้นที่นี่
- ปิดด้วย `Ctrl+C`

---

## 5. ตรวจว่าใช้ได้

รันใน PowerShell อีกหน้าต่าง (เครื่องเดียวกัน):

**5.1 เช็ค Forge Neo และ AI Service**

```powershell
curl.exe http://127.0.0.1:8001/health
```

ผลที่ควรได้:

```json
{"forge_reachable":true,"forge_url":"http://127.0.0.1:7860"}
```

**5.2 ลองเจนรูปจริง** (ใช้เวลาตามความเร็ว GPU)

```powershell
$body = '{"prompt": "a cute cat sitting on a chair", "steps": 20, "width": 512, "height": 512}'
$r = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/generate -ContentType 'application/json' -Body $body
$r.success; $r.elapsed_seconds
[IO.File]::WriteAllBytes("$PWD\test.png", [Convert]::FromBase64String($r.image_base64))
```

ต้องได้ `True` ตามด้วยเวลาที่ใช้ และมีไฟล์ `test.png` ในโฟลเดอร์ปัจจุบัน (`*.png` อยู่ใน `.gitignore` ไม่ขึ้น Git)

**5.3 หน้าทดสอบใน browser** — เปิด `http://127.0.0.1:8001/docs` → `POST /generate` → **Try it out**
หรือเปิดไฟล์ `test-forge-api.html` ใน browser

**5.4 ทดสอบจากเครื่อง Backend** (ถ้ารันแยกเครื่อง)

1. หา IP เครื่องนี้ด้วย `ipconfig` (หรือ Tailscale IP `100.x.x.x`)
2. เปิด firewall ให้ port 8001 (PowerShell แบบ Run as Administrator):
   ```powershell
   New-NetFirewallRule -DisplayName "Image Genny AI Service 8001" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
   ```
3. ที่เครื่อง Backend รัน `curl.exe http://<IP เครื่องนี้>:8001/health` ต้องได้ผลเหมือนข้อ 5.1
4. บอก IP ให้ Backend ใส่ใน `Backend\.env` เป็น `AI_SERVICE_URL=http://<IP เครื่องนี้>:8001`

---

## 6. API

| method | path | ทำอะไร |
|---|---|---|
| `POST` | `/generate` | เจนรูป (endpoint หลักที่ Backend เรียก) |
| `GET` | `/health` | เช็คว่าต่อ Forge Neo ได้ไหม (ไม่ผ่านคิว) |
| `GET` | `/` | เช็คว่า service เปิดอยู่ |
| `GET` | `/docs` | หน้าทดสอบ API อัตโนมัติของ FastAPI |

**คำขอ** `POST /generate`

```json
{
  "task_id": 5,
  "prompt": "a cute cat sitting on a chair",
  "negative_prompt": "blurry, low quality",
  "steps": 20,
  "width": 512,
  "height": 512,
  "seed": -1
}
```

ใส่แค่ `prompt` ก็ได้ ช่องอื่นใช้ค่าเริ่มต้น เงื่อนไข: `prompt` ห้ามว่าง, `steps` 1–150, `width`/`height` 64–2048, `seed` -1 = สุ่ม, `task_id` ใช้แค่ใน log

**คำตอบเมื่อสำเร็จ (200)**

```json
{"success": true, "image_base64": "iVBORw0KGgo...", "elapsed_seconds": 12.3}
```

**คำตอบเมื่อไม่สำเร็จ** — `{"detail": "ข้อความ"}`

| code | สาเหตุ |
|---|---|
| 422 | ข้อมูลผิดเงื่อนไข เช่น prompt ว่าง, steps เกิน 150 |
| 503 | คิวเต็ม หรือต่อ Forge Neo ไม่ได้ / หมดเวลา |
| 502 | ต่อ Forge Neo ได้ แต่ Forge เจนไม่สำเร็จ |

---

## 7. ไฟล์

| ไฟล์ | ขั้น | ทำอะไร |
|---|---|---|
| `main.py` | [2] | สร้างแอป FastAPI, endpoint ทั้งหมด, แปลง error เป็นรหัส HTTP |
| `models.py` | [3] | รูปแบบข้อมูลเข้า/ออก ให้ Pydantic ตรวจ |
| `queue_manager.py` | [4] | คิว `asyncio.Semaphore(1)` เจนทีละรูปตามลำดับที่มาถึง |
| `forge_client.py` | [5] | ไฟล์เดียวที่คุยกับ Forge Neo (`/sdapi/v1/txt2img`) |
| `config.py` | — | อ่านค่าจาก `.env` |
| `.env.example` | — | ตัวอย่างไฟล์ตั้งค่า |
| `test-forge-api.html` | — | หน้าทดสอบยิง `/generate` ตรงๆ ไม่ผ่าน Backend |

ในโค้ดมีป้ายขั้น `[1]`–`[5]`, `[4.1]`–`[4.5]`, `[5.1]`–`[5.5]` และ `[หยุด]` ค้นด้วย Ctrl+F ได้

---

## 8. ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `uvicorn : The term 'uvicorn' is not recognized` | ยังไม่ได้ activate venv หรือยังไม่ได้ `pip install` — ใช้ `python -m uvicorn` หลัง activate |
| `ModuleNotFoundError: No module named 'fastapi'` | รันจาก venv ผิดตัว — activate `ai-service\.venv` แล้ว `pip install -r requirements.txt` |
| `Error loading ASGI app. Could not import module "main"` | ไม่ได้ `cd ai-service` ก่อนรัน |
| `[Errno 10048] ... only one usage of each socket address` | port 8001 ถูกใช้อยู่ (เปิด AI Service ซ้อน) — ปิดตัวเก่า หรือหาด้วย `netstat -ano \| findstr :8001` |
| `/health` ได้ `"forge_reachable":false` | Forge Neo ยังไม่เปิด หรือยังโหลดไม่เสร็จ |
| `/generate` ได้ 404 จาก Forge (`/sdapi/v1/txt2img`) | Forge Neo ไม่ได้เปิด API — เพิ่ม `--api` ใน Launch Options ของ Stability Matrix |
| `/generate` ได้ 503 หมดเวลา | รูปใหญ่หรือ steps สูง GPU เจนไม่ทันใน 300 วินาที — ลดขนาด/steps หรือเพิ่ม `FORGE_TIMEOUT_SECONDS` |
| เครื่อง Backend ต่อไม่ได้ แต่เครื่องตัวเองได้ | ไม่ได้ใส่ `--host 0.0.0.0`, firewall ไม่เปิด 8001, IP เปลี่ยน หรืออยู่คนละเครือข่าย |

## ความปลอดภัย

AI Service **ไม่มีการตรวจ login** ใครเข้าถึง port 8001 ได้ก็สั่งเจนรูปได้ทันที (ข้ามระบบ login และการระงับบัญชีของ Backend)
ตอนใช้งานจริงให้ตั้ง firewall รับเฉพาะ IP ของเครื่อง Backend โดยเพิ่ม `-RemoteAddress <IP Backend>` ในคำสั่ง `New-NetFirewallRule`
