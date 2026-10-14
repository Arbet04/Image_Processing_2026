# ตั้งค่า nginx สำหรับ Image Genny

nginx ลงที่ **เครื่อง Frontend** ทำ 2 หน้าที่: เสิร์ฟหน้าเว็บ และส่งต่อ `/api/...` ไปที่ Backend (reverse proxy)

```
Browser → nginx (เครื่อง Frontend :80) ─┬→ login.html / index.html / config.js
                                        └→ /api/...  →  Backend (:5000) → AI Service (:8001) → Forge Neo (:7860)
```

ผู้ใช้ทุกคนเปิดเว็บที่ `http://<IP เครื่อง Frontend>/` — ไม่ต้องยิงไปที่ port 5000 ตรงๆ อีก

## ไฟล์ตั้งค่ากับ Git

nginx **ไม่มีไฟล์ `.env`** และไฟล์ที่ nginx ใช้จริงอยู่ **นอก repo ทั้งหมด** จึงไม่ขึ้น Git:

| ไฟล์ที่ใช้จริง | สร้างจาก (ใน repo) |
|---|---|
| `C:\nginx\conf\nginx.conf` | `nginx\nginx.conf` — เป็นตัวอย่าง ต้องคัดลอกแล้วแก้ IP (ข้อ 4) |
| `C:\image-project\frontend\*` | `Frontend\ai_studio\*` — ต้องคัดลอกมาเอง (ข้อ 2) |

clone เครื่องใหม่ต้องทำข้อ 2–4 ใหม่ทุกครั้ง แก้ IP ในไฟล์ที่ `C:\nginx\conf\` เท่านั้น ไม่ต้องแก้และไม่ต้อง commit `nginx\nginx.conf` ใน repo

## สิ่งที่ต้องมีก่อน

- IP ของเครื่อง Backend (ให้คนทำ Backend หาด้วย `ipconfig`)
- Backend เปิดอยู่ และเครื่องนี้ต่อถึงได้ — ทดสอบด้วย:
  ```powershell
  curl.exe http://<IP Backend>:5000/api/health
  ```
  ต้องได้ `"status": "ok"` ถ้าไม่ได้ ให้แก้ฝั่ง Backend ก่อน (firewall / IP / เครือข่าย) nginx ช่วยไม่ได้

---

## ติดตั้ง (ทำครั้งแรกครั้งเดียว)

คำสั่งทั้งหมดรันใน PowerShell ข้อ 2 และ 4 ต้องอยู่ที่โฟลเดอร์โปรเจค (`Image_Processing_2026`) เพราะคัดลอกไฟล์จาก repo

### 1. ติดตั้ง nginx

1. ดาวน์โหลด **Stable version** แบบ Windows (`nginx-x.y.z.zip`) จาก https://nginx.org/en/download.html
2. แตกไฟล์ แล้วเปลี่ยนชื่อโฟลเดอร์เป็น `C:\nginx` (ต้องมี `C:\nginx\nginx.exe`)
3. ทดสอบ:
   ```powershell
   cd C:\nginx
   .\nginx.exe
   ```
   terminal จะดูเหมือนค้าง (เป็นปกติ) เปิด `http://localhost` ต้องเห็นหน้า **Welcome to nginx!**
   แล้วปิดโดยเปิด terminal อีกอันรัน `cd C:\nginx; .\nginx.exe -s quit`

### 2. วางไฟล์หน้าเว็บ

```powershell
cd <โฟลเดอร์ Image_Processing_2026>
New-Item -ItemType Directory -Force C:\image-project\frontend
Copy-Item Frontend\ai_studio\login.html, Frontend\ai_studio\index.html, Frontend\ai_studio\config.js C:\image-project\frontend\
```

(ใช้ path สั้นๆ ที่ไม่มีช่องว่าง — ถ้าจะชี้ไปที่โฟลเดอร์ใน repo โดยตรงก็ได้ แต่ถ้า path มีช่องว่างต้องครอบด้วย `"..."` ใน `nginx.conf`)

### 3. แก้ `config.js` ในโฟลเดอร์ที่ nginx เสิร์ฟ

เปิด `C:\image-project\frontend\config.js` แล้วแก้เป็น:

```js
const BACKEND_URL = '';
```

ค่าว่างแปลว่าให้หน้าเว็บยิงไปที่ `/api/...` ของ nginx เอง แล้ว nginx ส่งต่อให้ Backend
**แก้เฉพาะไฟล์ใน `C:\image-project\frontend`** — ไม่ต้องแก้ไฟล์ใน repo

### 4. ใส่ config

```powershell
cd <โฟลเดอร์ Image_Processing_2026>
Copy-Item C:\nginx\conf\nginx.conf C:\nginx\conf\nginx.conf.bak
Copy-Item nginx\nginx.conf C:\nginx\conf\nginx.conf
```

(บรรทัดแรกสำรองไฟล์เดิมไว้เป็น `nginx.conf.bak`)

แล้วเปิด `C:\nginx\conf\nginx.conf` แก้ 2 จุดที่มี `<<<` กำกับ:

| บรรทัด | แก้เป็น | ข้อควรระวัง |
|---|---|---|
| `root` | `C:/image-project/frontend;` (โฟลเดอร์จากข้อ 2) | ใช้ `/` ไม่ใช่ `\` |
| `proxy_pass` | `http://<IP Backend>:5000;` | **ไม่มี** `/` ต่อท้าย |

**ต้องแก้ไฟล์ใน `C:\nginx\conf\`** ไม่ใช่ไฟล์ `nginx/nginx.conf` ใน repo — nginx อ่านเฉพาะไฟล์ใน `C:\nginx\conf\`

### 5. เปิด firewall ให้ port 80

PowerShell แบบ **Run as Administrator**:

```powershell
New-NetFirewallRule -DisplayName "Image Genny nginx 80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
```

---

## รัน (ทำทุกครั้ง)

```powershell
cd C:\nginx
.\nginx.exe -t
.\nginx.exe
```

- `-t` ต้องขึ้น `syntax is ok` และ `test is successful` ก่อน ถ้าไม่ผ่านจะบอกเลขบรรทัดที่ผิด
- `.\nginx.exe` จะไม่แสดงอะไร และ terminal ดูเหมือนค้าง — เป็นปกติ nginx ทำงานอยู่ เปิด terminal นี้ทิ้งไว้
- คำสั่ง `-s reload` / `-s quit` ให้รันใน **terminal อีกอัน** (ต้อง `cd C:\nginx` ก่อนเสมอ)
- ถ้า nginx เปิดอยู่แล้วและเพิ่งแก้ config ให้ใช้ `.\nginx.exe -s reload` แทนการเปิดซ้ำ

## ตรวจว่าใช้ได้

| ทดสอบ | ผลที่ควรได้ | ถ้าไม่ได้ |
|---|---|---|
| `curl.exe http://localhost/api/health` | `{"service": "Image Processing Backend", "status": "ok"}` | ดูตารางปัญหาด้านล่าง |
| เปิด `http://localhost/` | หน้า login ของ Image Genny | `root` ผิด |
| สมัคร → login → สร้างภาพ | ได้รูป และ terminal ของ Backend มี log ขึ้น | ดู `C:\nginx\logs\error.log` |
| เครื่องอื่นเปิด `http://<IP เครื่องนี้>/` | หน้า login | firewall port 80 ยังไม่เปิด |

## หลัง `git pull` ได้หน้าเว็บเวอร์ชันใหม่

nginx เสิร์ฟสำเนาใน `C:\image-project\frontend` ไม่ใช่ไฟล์ใน repo จึงต้องคัดลอกใหม่ (ไม่ทับ `config.js`):

```powershell
cd <โฟลเดอร์ Image_Processing_2026>
Copy-Item Frontend\ai_studio\login.html, Frontend\ai_studio\index.html C:\image-project\frontend\
```

แล้วกด **Ctrl+F5** ใน browser (ไม่ต้อง reload nginx)

## คำสั่งที่ใช้บ่อย (รันใน `C:\nginx`)

| คำสั่ง | ทำอะไร |
|---|---|
| `.\nginx.exe` | เปิด nginx |
| `.\nginx.exe -t` | ตรวจ config |
| `.\nginx.exe -s reload` | โหลด config ใหม่ |
| `.\nginx.exe -s quit` | ปิด nginx |
| `taskkill /f /im nginx.exe` | ปิด nginx ทุกตัวที่ค้างอยู่ |

## ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| เปิด nginx ไม่ขึ้น `bind() to 0.0.0.0:80 failed` | มีโปรแกรมอื่นใช้ port 80 — เปลี่ยนเป็น `listen 8080;` แล้วเปิดเว็บที่ `http://localhost:8080` |
| หน้าเว็บขึ้น 404 | `root` ผิด หรือใช้ `\` — ดู `C:\nginx\logs\error.log` |
| `/api/health` ขึ้น 502 Bad Gateway | Backend ไม่ได้เปิด, IP ใน `proxy_pass` ผิด หรือ firewall เครื่อง Backend ไม่เปิด port 5000 — ดู `error.log` ว่า nginx ต่อไปที่ IP ไหน (`upstream: "http://..."`) |
| `error.log` ยังแสดง IP เก่า ทั้งที่แก้แล้ว | แก้ผิดไฟล์ (ไฟล์ใน repo) หรือยังไม่ได้ reload — แก้ที่ `C:\nginx\conf\nginx.conf` แล้ว `taskkill /f /im nginx.exe` และเปิดใหม่ |
| `/api/health` ขึ้น 404 | ใส่ `/` ต่อท้าย `proxy_pass` หรือ Backend ยังเป็นโค้ดเก่าที่ไม่มี `/api/health` |
| เจนรูปแล้วได้ 504 Gateway Time-out | ไม่มี `proxy_read_timeout 600s;` ใน `location /api/` |
| หน้าเว็บขึ้น "ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ Backend ได้" | `config.js` ใน `C:\image-project\frontend` ยังไม่ได้แก้เป็น `''` — แก้แล้วกด Ctrl+F5 |
| หน้าเว็บเป็นเวอร์ชันเก่า (ไม่มีฟีเจอร์ใหม่) | ยังไม่ได้คัดลอกไฟล์ใหม่หลัง `git pull` — ดูหัวข้อด้านบน |
| แก้ config แล้วไม่มีผล | ยังไม่ได้ `.\nginx.exe -s reload` หรือมี nginx ค้างหลายตัว (`taskkill /f /im nginx.exe` แล้วเปิดใหม่) |
