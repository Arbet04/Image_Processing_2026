# Backend (Flask)

ตัวกลางระหว่างหน้าเว็บกับ AI Service: จัดการสมัคร/login (JWT), เก็บข้อมูลผู้ใช้และประวัติการเจนรูปลงฐานข้อมูล แล้วส่งงานเจนรูปต่อไปที่ AI Service

```
Frontend / nginx ──► Backend :5000 ──► AI Service :8001 ──► Forge Neo
                        │
                        └─► ฐานข้อมูล: SQLite ในเครื่องนี้ (ตอนนี้)
                            หรือ PostgreSQL :5432 ที่เครื่องเพื่อน (ดู Database/README.md)
```

---

## 1. สิ่งที่ต้องมีก่อน

- Python 3.11 ขึ้นไป (ทดสอบกับ 3.13) — เช็คด้วย `py -3 --version`
- clone โปรเจคแล้ว (ดู [README หลัก](../README.md))
- รู้ IP เครื่อง AI Service (ถ้าอยู่คนละเครื่อง)

**ฐานข้อมูลตอนนี้: SQLite** — ค่าเริ่มต้นใน `.env.example` ใช้ SQLite ไว้ก่อน เพื่อให้ clone แล้วรันได้ทันทีโดยไม่ต้องติดตั้งอะไรเพิ่ม
PostgreSQL ของโปรเจคอยู่ที่ **เครื่องเพื่อน (คนทำ Database)** ต้องต่อผ่าน IP — ถ้าจะเปลี่ยนไปใช้ ดูข้อ 3.3
ทั้งสองแบบ Backend สร้างตารางให้เองตอนเปิดครั้งแรก ไม่ต้องรัน SQL

---

## 2. ติดตั้ง (ทำครั้งแรกครั้งเดียว)

เปิด PowerShell ที่โฟลเดอร์โปรเจค แล้วรันทีละบรรทัด:

```powershell
cd Backend
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

| บรรทัด | ทำอะไร |
|---|---|
| `py -3 -m venv venv` | สร้าง virtual environment ในโฟลเดอร์ `Backend\venv` |
| `Activate.ps1` | เปิดใช้ venv — บรรทัดคำสั่งจะขึ้น `(venv)` นำหน้า |
| `pip install -r requirements.txt` | ติดตั้ง Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Cors, requests, python-dotenv, psycopg2-binary |
| `Copy-Item .env.example .env` | สร้างไฟล์ตั้งค่า — **ต้องแก้ต่อในข้อ 3** |

ถ้า `Activate.ps1` ขึ้น error `running scripts is disabled on this system` ให้รันคำสั่งนี้ครั้งเดียว แล้ว activate ใหม่:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 3. ตั้งค่า (`.env`)

### ไฟล์ `.env` ไม่ได้อยู่ใน Git — ต้องสร้างเองทุกเครื่อง

- `.env` เก็บคีย์ลับ, IP และรหัสผ่านฐานข้อมูล จึงอยู่ใน `.gitignore` — clone หรือ pull มาแล้ว **จะไม่มีไฟล์นี้**
- ใน Git มีแค่ `.env.example` ซึ่งเป็นตัวอย่างที่ไม่มีค่าลับ ใช้คัดลอกเป็น `.env` (บรรทัดสุดท้ายของข้อ 2) แล้วแก้ตามข้อ 3.1–3.4
- เช็คว่าสร้างแล้ว (ใน `Backend`): `Test-Path .env` ต้องได้ `True`
- เช็คว่า Git ไม่เห็นไฟล์นี้: `git status` ต้อง **ไม่มี** `Backend/.env` ในรายการ
- ถ้าลืมสร้าง Backend ยังเปิดได้ แต่จะใช้คีย์ลับค่าเริ่มต้นที่ไม่ปลอดภัย (มีคำเตือน `SECRET_KEY/JWT_SECRET_KEY ยังเป็นค่า default` ใน log) และต่อ AI Service ได้เฉพาะเครื่องเดียวกัน
- ค่าที่ต้องได้จากเพื่อน (IP เครื่อง AI Service, IP กับรหัสผ่าน PostgreSQL) ให้ถามกันเป็นการส่วนตัว แล้วพิมพ์ลง `.env` ของตัวเอง
- ห้าม commit หรือส่งไฟล์ `.env` ให้คนอื่น ถ้าเผลอ `git add` ไปแล้ว ให้เอาออกด้วย `git rm --cached .env`

### แก้ค่าใน `.env`

เปิดไฟล์ `Backend\.env` แล้วแก้ตามนี้:

**3.1 คีย์ลับ 2 ตัว** — สร้างค่าสุ่มด้วยคำสั่งนี้ 2 ครั้ง แล้วนำไปใส่คนละค่า:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

```
SECRET_KEY=<ค่าสุ่มค่าที่ 1>
JWT_SECRET_KEY=<ค่าสุ่มค่าที่ 2>
```

ห้ามแชร์ค่านี้ให้คนอื่น ใครรู้ `JWT_SECRET_KEY` จะปลอม token เข้าระบบเป็นใครก็ได้

**3.2 ที่อยู่ AI Service**

| กรณี | ค่า |
|---|---|
| AI Service อยู่เครื่องเดียวกัน | `AI_SERVICE_URL=http://127.0.0.1:8001` (ค่าเริ่มต้น) |
| AI Service อยู่เครื่องอื่น | `AI_SERVICE_URL=http://<IP เครื่อง AI Service>:8001` |

port คือ **8001** (ของ AI Service) ไม่ใช่ 5000

**3.3 ฐานข้อมูล**

| กรณี | ค่า |
|---|---|
| **SQLite (ตอนนี้ใช้แบบนี้)** | `DATABASE_URL=sqlite:///app.db` — ค่าเริ่มต้นใน `.env.example` ไม่ต้องแก้ ไฟล์ฐานข้อมูลอยู่ที่ `Backend\instance\app.db` |
| PostgreSQL ที่เครื่องเพื่อน | `DATABASE_URL=postgresql+psycopg2://app_user:<รหัสผ่าน>@<IP เครื่องเพื่อน>:5432/image_processing_2026` |

จะเปลี่ยนเป็น PostgreSQL ได้เมื่อเพื่อนเปิดให้เครื่องนี้ต่อเข้าไปแล้ว ([Database/README.md](../Database/README.md) ข้อ 4) — ทดสอบก่อนด้วย
`Test-NetConnection <IP เครื่องเพื่อน> -Port 5432` ต้องได้ `TcpTestSucceeded : True`

- ต้องขึ้นต้นด้วย `postgresql+psycopg2://` **ไม่ใช่** `postgresql://` เฉยๆ (Backend จะเปิดไม่ขึ้น)
- IP เครื่องเพื่อนเปลี่ยนเมื่อต่อ Wi-Fi ใหม่ — ถ้า Backend เปิดไม่ขึ้นเพราะต่อ DB ไม่ได้ ให้เช็ค IP ก่อน หรือสลับกลับเป็น SQLite ชั่วคราว
- ข้อมูลใน SQLite กับ PostgreSQL แยกกัน สลับแล้วต้องสมัครสมาชิกใหม่

**3.4 ผู้ดูแลระบบ** (ถ้าต้องการใช้หน้าจัดการผู้ใช้)

```
ADMIN_USERNAME=<ชื่อผู้ใช้ที่จะเป็น admin>
```

ต้องตรงตัวพิมพ์เล็ก/ใหญ่กับชื่อที่สมัคร ถ้าบัญชีมีอยู่แล้วจะได้สิทธิ์ตอนเปิด server ถ้ายังไม่มีจะได้สิทธิ์ตอนสมัคร
ควรสมัครชื่อนี้เองก่อนเปิดให้คนอื่นใช้ ไม่งั้นใครสมัครชื่อนี้ก่อนจะได้สิทธิ์ admin

**3.5 ค่าอื่น** (ปกติไม่ต้องแก้)

| ตัวแปร | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `AI_SERVICE_TIMEOUT` | `600` | รอ AI Service ได้นานสุด (วินาที) รวมเวลารอคิว ต้องมากกว่า `FORGE_TIMEOUT_SECONDS` ของ AI Service (300) |
| `JWT_EXPIRES_HOURS` | `24` | token ใช้ได้กี่ชั่วโมง หมดแล้วต้อง login ใหม่ |
| `FLASK_DEBUG` | `0` | `1` = เปิด debugger ใช้เฉพาะตอนทดสอบในเครื่องตัวเอง |

แก้ `.env` แล้วต้องปิด Backend (Ctrl+C) แล้วเปิดใหม่

---

## 4. รัน (ทำทุกครั้ง)

เปิด AI Service ไว้ก่อน (ดู [ai-service/README.md](../ai-service/README.md)) แล้ว:

```powershell
cd Backend
.\venv\Scripts\Activate.ps1
python app.py
```

ต้องเห็น:

```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://<IP เครื่องนี้>:5000
```

- Backend เปิดรับจากทุกเครื่องที่ port 5000 อยู่แล้ว (`host='0.0.0.0'` ใน `app.py`)
- เปิด terminal นี้ทิ้งไว้ตลอด log ของทุกคำขอจะขึ้นที่นี่
- ปิดด้วย `Ctrl+C`

---

## 5. ตรวจว่าใช้ได้

รันใน PowerShell อีกหน้าต่าง:

**5.1 Backend เปิดอยู่**

```powershell
curl.exe http://127.0.0.1:5000/api/health
```

ต้องได้ `{"service": "Image Processing Backend", "status": "ok"}`

**5.2 ต่อ AI Service ได้** (รันบนเครื่อง Backend)

ใช้ค่าเดียวกับ `AI_SERVICE_URL` ใน `.env` แล้วต่อท้ายด้วย `/health` เช่น

```powershell
curl.exe http://172.20.x.x:8001/health
```

ต้องได้ `"forge_reachable":true` ถ้าค้างหรือ error แปลว่า Backend จะเจนรูปไม่ได้ — ดูข้อ 5.4 ใน [ai-service/README.md](../ai-service/README.md)

**5.3 ทดสอบครบทั้งเส้นทาง** (สมัคร → login → เจนรูป)

```powershell
$api = 'http://127.0.0.1:5000/api'
$cred = '{"username": "testuser", "password": "test1234"}'
Invoke-RestMethod -Method Post -Uri "$api/auth/register" -ContentType 'application/json' -Body $cred
$token = (Invoke-RestMethod -Method Post -Uri "$api/auth/login" -ContentType 'application/json' -Body $cred).access_token
$headers = @{ Authorization = "Bearer $token" }
$r = Invoke-RestMethod -Method Post -Uri "$api/image/generate" -Headers $headers -ContentType 'application/json' -Body '{"prompt": "a cute cat", "steps": 20}'
$r.status
```

ต้องได้ `completed` (ถ้ารันซ้ำ บรรทัด register จะ error ว่ามีชื่อนี้แล้ว ข้ามไปได้)

**5.4 ทดสอบจากเครื่องอื่น** (ถ้า nginx / Frontend อยู่คนละเครื่อง)

1. หา IP เครื่องนี้ด้วย `ipconfig`
2. เปิด firewall ให้ port 5000 (PowerShell แบบ Run as Administrator):
   ```powershell
   New-NetFirewallRule -DisplayName "Image Genny Backend 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
   ```
3. ที่เครื่องอื่นรัน `curl.exe http://<IP เครื่องนี้>:5000/api/health` ต้องได้ผลเหมือนข้อ 5.1
4. บอก IP ให้คนทำ nginx ใส่ใน `proxy_pass`

---

## 6. Endpoints

### Health
- `GET /api/health` — เช็คว่า Backend ทำงานอยู่ (ไม่ต้อง login) ใช้ทดสอบ nginx

### Auth (`/api/auth`)
- `POST /api/auth/register` — สมัครสมาชิก (`username`, `password`)
- `POST /api/auth/login` — เข้าสู่ระบบ (`username`, `password`) ได้ `access_token` กลับมา (บัญชีที่ถูกระงับได้ 403)
- `GET /api/auth/me` — ข้อมูลผู้ใช้ปัจจุบัน (ต้องส่ง `Authorization: Bearer <token>`)

### Image (`/api/image`) — ต้องส่ง token
- `POST /api/image/generate` — สร้างรูป (`prompt`, `negative_prompt`, `steps`, `width`, `height`, `seed`) ส่งต่อไป AI Service แล้วรอจนเสร็จ ตอบ `image_url` เป็น base64
- `GET /api/image/history` — ประวัติของผู้ใช้ (ไม่รวมรูป ส่ง `?include_images=1` ถ้าต้องการ)
- `GET /api/image/<id>` — งานเดียวพร้อมรูป

### Admin (`/api/admin`) — ต้อง login ด้วยบัญชี `role = 'admin'`
- `GET /api/admin/users` — รายชื่อผู้ใช้ทั้งหมด พร้อมจำนวนรูป (`image_count`)
- `POST /api/admin/users/<id>/suspend` — ระงับบัญชี (login ไม่ได้ และ token เดิมใช้ไม่ได้ทันที) ไม่ลบบัญชีและรูป
- `POST /api/admin/users/<id>/unsuspend` — ปลดระงับ
- ระงับตัวเองหรือ admin คนอื่นไม่ได้ / คนที่ไม่ใช่ admin เรียกได้ 403

---

## 7. ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `ModuleNotFoundError: No module named 'flask_sqlalchemy'` | ยังไม่ได้ activate `venv` หรือยังไม่ได้ `pip install -r requirements.txt` |
| `pip install` ล้มที่ `psycopg2-binary` | Python ใหม่กว่าเวอร์ชันที่ระบุ — `requirements.txt` ต้องเป็น `psycopg2-binary==2.9.10` ขึ้นไป |
| `ModuleNotFoundError: No module named 'psycopg'` | `DATABASE_URL` ขึ้นต้นด้วย `postgresql://` — เปลี่ยนเป็น `postgresql+psycopg2://` |
| `OperationalError ... Connection refused` / `password authentication failed` ตอนเปิด Backend | ต่อ PostgreSQL ไม่ได้ — ดูตารางปัญหาใน [Database/README.md](../Database/README.md) ข้อ 8 |
| `no such column: users.role` (SQLite) | ไฟล์ DB เก่าไม่ตรงกับโค้ด — ปิด Backend แล้วลบ `instance\app.db` แล้วเปิดใหม่ (ข้อมูลทดสอบจะหาย) |
| `column users.role does not exist` (PostgreSQL) | ตาราง `users` เป็นของเก่า — รัน `Database\001_add_user_columns.sql` |
| เจนรูปได้ 502 `Failed to communicate with AI Service` | ดู `details` ในคำตอบ: ต่อ AI Service ไม่ได้ (เช็ค `AI_SERVICE_URL` และข้อ 5.2), คิวเต็ม, หรือ Forge Neo ไม่ได้เปิด |
| `AI_SERVICE_URL` ชี้ไป port 5000 | ผิด — AI Service อยู่ port **8001** |
| หน้า admin ไม่ขึ้น | `ADMIN_USERNAME` ไม่ตรงกับชื่อที่สมัคร (ตัวพิมพ์เล็ก/ใหญ่) หรือแก้ `.env` แล้วยังไม่ได้ restart Backend |
| เครื่องอื่นต่อไม่ได้ แต่เครื่องตัวเองได้ | firewall ไม่เปิด 5000, IP เปลี่ยน หรืออยู่คนละเครือข่าย |
