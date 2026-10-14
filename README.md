# Image Genny — Image_Processing_2026

เว็บสร้างภาพจากข้อความ (Text-to-Image) แบบ distributed: แต่ละส่วนรันแยกโปรแกรม และแยกเครื่องได้

```
Browser ──► nginx :80 ──► Backend :5000 ──► AI Service :8001 ──► Forge Neo :7860 (GPU)
            (Frontend)    (Flask)  │        (FastAPI + คิว)      (Stable Diffusion)
                                   └──► ฐานข้อมูล: SQLite ในเครื่อง Backend (ตอนนี้)
                                        หรือ PostgreSQL :5432 ที่เครื่องเพื่อน (ต่อผ่าน IP)
```

| ส่วน | โฟลเดอร์ | port | ทำอะไร | วิธีรัน |
|---|---|---|---|---|
| Forge Neo | (ติดตั้งแยก) | 7860 | เจนรูปด้วย GPU | ผ่าน Stability Matrix |
| AI Service | [ai-service/](ai-service/) | 8001 | รับงานจาก Backend ต่อคิว ส่งให้ Forge Neo | [ai-service/README.md](ai-service/README.md) |
| Backend | [Backend/](Backend/) | 5000 | login, เก็บข้อมูลลง DB, ส่งงานให้ AI Service | [Backend/README.md](Backend/README.md) |
| Frontend | [Frontend/ai_studio/](Frontend/ai_studio/) | — | หน้าเว็บ HTML/JS (ไม่มีขั้นตอน build) | [Frontend/ai_studio/README.md](Frontend/ai_studio/README.md) |
| nginx | [nginx/](nginx/) | 80 | เสิร์ฟหน้าเว็บ และส่งต่อ `/api/` ไป Backend | [nginx/README.md](nginx/README.md) |
| Database | [Database/](Database/) | 5432 | เก็บผู้ใช้และประวัติการเจนรูป — ตอนนี้ใช้ SQLite ไว้ก่อน, PostgreSQL อยู่เครื่องเพื่อน (Backend สร้างตารางเอง) | [Database/README.md](Database/README.md) |

---

## สิ่งที่ต้องมีก่อน

| อะไร | ใครต้องมี | หมายเหตุ |
|---|---|---|
| Windows 10/11 | ทุกคน | คำสั่งในเอกสารนี้เป็น PowerShell |
| Python 3.11 ขึ้นไป (ทดสอบกับ 3.13) | AI Service, Backend | เช็คด้วย `py -3 --version` |
| Git | ทุกคน | ใช้ clone โปรเจค |
| Stability Matrix + Forge Neo + checkpoint อย่างน้อย 1 ตัว | AI Service | ต้องมี GPU NVIDIA |
| nginx for Windows | Frontend (ถ้าใช้ nginx) | ดู [nginx/README.md](nginx/README.md) |
| PostgreSQL | เฉพาะเครื่องเพื่อนที่ทำ Database | ดู [Database/README.md](Database/README.md) — เครื่องอื่นไม่ต้องติดตั้ง (ตอนนี้ Backend ใช้ SQLite ไว้ก่อน) |

clone โปรเจค (ทุกเครื่อง):

```powershell
git clone https://github.com/Arbet04/Image_Processing_2026.git
cd Image_Processing_2026
```

**ทุกคำสั่งในเอกสารนี้เริ่มที่โฟลเดอร์ `Image_Processing_2026`** — เปิด terminal ใหม่ทุกครั้งต้อง `cd` มาที่โฟลเดอร์นี้ก่อน
(ใน VS Code เปิดโฟลเดอร์โปรเจคแล้วกด `` Ctrl+` `` จะได้ terminal ที่อยู่ในโฟลเดอร์นี้เลย)

### ไฟล์ที่ไม่ได้อยู่ใน Git (ต้องสร้าง/แก้เองทุกเครื่อง)

clone มาแล้วจะ **ไม่มี** ไฟล์เหล่านี้ เพราะเก็บค่าเฉพาะเครื่อง (IP, รหัสผ่าน, คีย์ลับ) และอยู่ใน `.gitignore`

| ไฟล์ | ของใคร | สร้างจาก | วิธีทำ |
|---|---|---|---|
| `ai-service\.env` | AI Service | `ai-service\.env.example` | [ai-service/README.md](ai-service/README.md) ข้อ 2–3 |
| `Backend\.env` | Backend | `Backend\.env.example` | [Backend/README.md](Backend/README.md) ข้อ 2–3 |
| `C:\nginx\conf\nginx.conf` | nginx | `nginx\nginx.conf` (ตัวอย่างใน repo) | [nginx/README.md](nginx/README.md) ข้อ 4 — อยู่นอก repo |
| `C:\image-project\frontend\config.js` | nginx | `Frontend\ai_studio\config.js` | [nginx/README.md](nginx/README.md) ข้อ 2–3 — อยู่นอก repo |
| `Backend\instance\app.db` | Backend | Backend สร้างเองตอนเปิด | ไม่ต้องทำอะไร (ข้อมูล SQLite อยู่เฉพาะเครื่อง Backend) |

- **ห้าม commit หรือส่งไฟล์ `.env` ให้คนอื่น** — ค่าที่ต้องได้จากเพื่อน (IP, รหัสผ่าน DB) ให้ถามกันเป็นการส่วนตัว แล้วพิมพ์ลงไฟล์ของตัวเอง
- เช็คว่า Git ไม่เห็นไฟล์ `.env`: `git status` ต้องไม่มี `.env` ในรายการ ถ้าเผลอ `git add` ไปแล้ว ใช้ `git rm --cached <path ของไฟล์ .env>`
- `Frontend\ai_studio\config.js` **อยู่ใน Git** — แก้ IP ในเครื่องตัวเองได้ แต่อย่า commit IP ของตัวเองขึ้นไป (ค่าใน repo ควรเป็น `http://127.0.0.1:5000`)

---

## ลำดับการเปิด (สำคัญ)

เปิด **จากหลังไปหน้า** เพราะแต่ละส่วนต้องต่อไปหาส่วนถัดไปได้:

1. **PostgreSQL** (เฉพาะเมื่อเปลี่ยนจาก SQLite ไปใช้แล้ว) — อยู่เครื่องเพื่อน เป็น Windows Service เปิดเองตอนเปิดเครื่อง ขอแค่เครื่องนั้นเปิดอยู่
2. **Forge Neo** — รอจนขึ้น `Running on local URL: http://127.0.0.1:7860`
3. **AI Service** — `python -m uvicorn main:app --host 0.0.0.0 --port 8001`
4. **Backend** — `python app.py`
5. **nginx** หรือ web server ของ Frontend
6. เปิด browser

ข้อ 3–5 ใช้ terminal แยกกันคนละอัน และต้องเปิดทิ้งไว้ตลอด ปิด terminal = ส่วนนั้นหยุดทำงาน
ถ้าเปิดผิดลำดับ ระบบไม่พัง แต่จะได้ error จนกว่าส่วนที่อยู่ข้างหลังจะเปิด (เช่น Backend เปิดก่อน PostgreSQL จะเปิดไม่ขึ้น)

---

## แบบที่ 1: รันทุกอย่างในเครื่องเดียว (ทดสอบเอง)

เหมาะสำหรับเครื่องที่มี GPU และ Forge Neo ค่าเริ่มต้นในโค้ดทั้งหมดชี้ไปที่ `127.0.0.1` อยู่แล้ว **ไม่ต้องแก้ IP**
ฐานข้อมูลใช้ SQLite ตามค่าเริ่มต้นใน `Backend\.env.example` ได้เลย ไม่ต้องติดตั้ง PostgreSQL

**ก่อนเริ่ม — Forge Neo:** เปิดผ่าน Stability Matrix

**Terminal 1 — AI Service** (ครั้งแรกทำขั้นตอนติดตั้งใน [ai-service/README.md](ai-service/README.md) ก่อน)

```powershell
cd ai-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

**Terminal 2 — Backend** (ครั้งแรกทำขั้นตอนติดตั้งใน [Backend/README.md](Backend/README.md) ก่อน)

```powershell
cd Backend
.\venv\Scripts\Activate.ps1
python app.py
```

**Terminal 3 — Frontend** (ไม่ใช้ nginx)

```powershell
cd Frontend\ai_studio
py -3 -m http.server 5500
```

เปิด `http://localhost:5500/login.html` → สมัครสมาชิก → เข้าสู่ระบบ → สร้างภาพ

---

## แบบที่ 2: รันแยกเครื่อง (ผ่าน nginx)

```
เครื่อง A (Frontend)            เครื่อง B (Backend)             เครื่อง C (AI)
nginx :80              ──►      Backend :5000          ──►      AI Service :8001 ──► Forge Neo :7860
เสิร์ฟหน้าเว็บ + /api/                │                          (Forge อยู่เครื่องเดียวกับ AI Service)
                                    ▼
                         ตอนนี้: SQLite ในเครื่อง B (ไม่ต้องตั้งค่า)
                         ภายหลัง: PostgreSQL :5432 ที่เครื่อง D (เครื่องเพื่อน ต่อผ่าน IP)
```

**ตอนนี้ใช้ SQLite ไว้ก่อน** จึงข้ามทุกอย่างที่เกี่ยวกับเครื่อง D ได้ (IP ของ D, firewall 5432, ลำดับ 1 ในขั้นที่ 3, ด่าน 0)
ทำส่วนของเครื่อง D เมื่อพร้อมย้ายไป PostgreSQL ที่เครื่องเพื่อนแล้ว

### ขั้นที่ 1: จด IP ของทุกเครื่องก่อน

ทุกเครื่องต้องอยู่เครือข่ายเดียวกัน (Wi-Fi เดียวกัน หรือ Tailscale เดียวกัน) แต่ละเครื่องหา IP ของตัวเองด้วย:

```powershell
ipconfig
```

ดูบรรทัด `IPv4 Address` ของ Wi-Fi (หรือ IP `100.x.x.x` ของ Tailscale) แล้วจดลงตาราง:

| เครื่อง | IP | ใช้ใส่ที่ไหน |
|---|---|---|
| B (Backend) | `__________` | `proxy_pass` ใน `nginx.conf` ของเครื่อง A และ `pg_hba.conf` ของเครื่อง D |
| C (AI Service) | `__________` | `AI_SERVICE_URL` ใน `Backend\.env` ของเครื่อง B |
| D (Database — เมื่อใช้ PostgreSQL) | `__________` | `DATABASE_URL` ใน `Backend\.env` ของเครื่อง B |

**IP วง Wi-Fi เปลี่ยนได้ทุกครั้งที่ต่อ Wi-Fi ใหม่** — เช็คซ้ำก่อนนัดทดสอบทุกครั้ง (Tailscale IP ไม่เปลี่ยน)

### ขั้นที่ 2: เปิด Firewall ให้ port ที่เครื่องอื่นต้องต่อเข้ามา

เปิด PowerShell แบบ **Run as Administrator** บนเครื่องที่ระบุ:

```powershell
# เครื่อง C (AI Service) — ให้ Backend ต่อเข้ามา
New-NetFirewallRule -DisplayName "Image Genny AI Service 8001" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow

# เครื่อง B (Backend) — ให้ nginx ต่อเข้ามา
New-NetFirewallRule -DisplayName "Image Genny Backend 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow

# เครื่อง A (Frontend) — ให้ผู้ใช้เปิดเว็บ
New-NetFirewallRule -DisplayName "Image Genny nginx 80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
```

เครื่อง D (Database) เปิด port 5432 ตาม [Database/README.md](Database/README.md) ข้อ 4 (เฉพาะเมื่อใช้ PostgreSQL)

ถ้าต้องการให้เฉพาะเครื่องที่ต้องใช้เข้าถึงได้ ให้เพิ่ม `-RemoteAddress <IP เครื่องที่ต่อเข้ามา>` เช่น เครื่อง C ใส่ IP ของเครื่อง B
(AI Service ไม่มีการตรวจ login ใครเข้าถึง port 8001 ได้ก็สั่งเจนรูปได้ทันที)

### ขั้นที่ 3: ตั้งค่าและเปิดทีละเครื่อง (จากหลังไปหน้า)

ครั้งแรกแต่ละเครื่องต้องทำขั้นตอน "ติดตั้ง" ใน README ของส่วนตัวเองก่อน (รวมถึงสร้างไฟล์ `.env` จาก `.env.example` — ไฟล์นี้ไม่ได้มากับ Git)

| ลำดับ | เครื่อง | ตั้งค่า | เปิด | ทดสอบ (ต้องผ่านก่อนไปข้อถัดไป) |
|---|---|---|---|---|
| 1 | D (ข้ามได้ถ้ายังใช้ SQLite) | สร้าง database `image_processing_2026` และ user `app_user` ([Database/README.md](Database/README.md) ข้อ 2–4) | เปิดเองอัตโนมัติ (Windows Service) | เครื่อง B: `Test-NetConnection <IP D> -Port 5432` ได้ `True` |
| 2 | C | `ai-service\.env` ใช้ค่าเริ่มต้น ไม่ต้องแก้ | เปิด Forge Neo แล้ว `python -m uvicorn main:app --host 0.0.0.0 --port 8001` | เครื่อง B: `curl.exe http://<IP C>:8001/health` ได้ `"forge_reachable":true` |
| 3 | B | `Backend\.env`: `AI_SERVICE_URL=http://<IP C>:8001` — `DATABASE_URL` คงไว้เป็น `sqlite:///app.db` (ถ้าใช้ PostgreSQL ดู [Backend/README.md](Backend/README.md) ข้อ 3.3) | `python app.py` | เครื่อง A: `curl.exe http://<IP B>:5000/api/health` ได้ `"status":"ok"` |
| 4 | A | `C:\nginx\conf\nginx.conf`: `proxy_pass http://<IP B>:5000;` และ `C:\image-project\frontend\config.js`: `BACKEND_URL = ''` | `cd C:\nginx` แล้ว `.\nginx.exe` | เครื่อง A: `curl.exe http://localhost/api/health` ได้ `"status":"ok"` |

### ขั้นที่ 4: ใช้งาน

ผู้ใช้ทุกคนเปิด `http://<IP เครื่อง A>/` → สมัคร → เข้าสู่ระบบ → สร้างภาพ

---

## เช็คทีละด่าน (ใช้ตอนมีปัญหา)

ทดสอบจาก **ด่านหลังสุดไล่มาข้างหน้า** ด่านไหนไม่ผ่าน ปัญหาอยู่ที่ด่านนั้น

| ด่าน | ทดสอบจากเครื่อง | คำสั่ง | ผลที่ควรได้ |
|---|---|---|---|
| 0. PostgreSQL (เฉพาะเมื่อใช้) | B | `Test-NetConnection <IP D> -Port 5432` | `TcpTestSucceeded : True` |
| 1. Forge Neo | C | `curl.exe http://127.0.0.1:7860/sdapi/v1/sd-models` | รายชื่อ checkpoint (JSON) |
| 2. AI Service | C | `curl.exe http://127.0.0.1:8001/health` | `"forge_reachable":true` |
| 3. AI Service ข้ามเครื่อง | B | `curl.exe http://<IP C>:8001/health` | เหมือนข้อ 2 |
| 4. Backend | B | `curl.exe http://127.0.0.1:5000/api/health` | `"status":"ok"` |
| 5. Backend ข้ามเครื่อง | A | `curl.exe http://<IP B>:5000/api/health` | เหมือนข้อ 4 |
| 6. nginx | A | `curl.exe http://localhost/api/health` | เหมือนข้อ 4 |

ด่าน 2 ได้ `"forge_reachable":false` = Forge Neo ไม่ได้เปิด
ด่าน 0, 3 หรือ 5 ค้างจน timeout หรือได้ `False` = IP ผิด, firewall ไม่ได้เปิด, หรือไม่ได้อยู่เครือข่ายเดียวกัน
ด่าน 4 ไม่ผ่าน และ terminal ของ Backend มี error ตอนเปิด = ต่อฐานข้อมูลไม่ได้ ดู [Database/README.md](Database/README.md) ข้อ 8

---

## ค่าตั้งค่าที่ต้องสัมพันธ์กัน

| ค่า | อยู่ที่ | ค่าเริ่มต้น | กฎ |
|---|---|---|---|
| `FORGE_TIMEOUT_SECONDS` | `ai-service\.env` | 300 | ต้องน้อยกว่า `AI_SERVICE_TIMEOUT` |
| `AI_SERVICE_TIMEOUT` | `Backend\.env` | 600 | รวมเวลารอคิว จึงต้องมากกว่า Forge |
| `proxy_read_timeout` | `nginx.conf` | 600s | ต้องไม่น้อยกว่า `AI_SERVICE_TIMEOUT` ไม่งั้นได้ 504 |
| `AI_SERVICE_URL` | `Backend\.env` | `http://127.0.0.1:8001` | port **8001** ไม่ใช่ 5000 |
| `DATABASE_URL` | `Backend\.env` | `sqlite:///app.db` (ใช้อยู่ตอนนี้) | เปลี่ยนไป PostgreSQL ที่เครื่องเพื่อน ต้องขึ้นต้นด้วย `postgresql+psycopg2://` และใช้ IP เครื่องเพื่อน |
| `BACKEND_URL` | `Frontend\ai_studio\config.js` | `http://127.0.0.1:5000` | ใช้ nginx ให้ตั้งเป็น `''` |

ไฟล์ `.env` ไม่ขึ้น Git — ดูหัวข้อ "ไฟล์ที่ไม่ได้อยู่ใน Git" ด้านบน
