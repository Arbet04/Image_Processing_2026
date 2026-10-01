# ตั้งค่า nginx สำหรับ Image Genny

nginx ลงที่ **เครื่อง Frontend** ทำ 2 หน้าที่: เสิร์ฟหน้าเว็บ และส่งต่อ `/api/...` ไปที่ Backend (reverse proxy)

```
Browser → nginx (เครื่อง Frontend :80) ─┬→ login.html / index.html / config.js
                                        └→ /api/...  →  Backend (:5000) → AI Service (:8001) → Forge Neo (:7860)
```

ผู้ใช้ทุกคนเปิดเว็บที่ `http://<IP เครื่อง Frontend>/` — ไม่ต้องยิงไปที่ port 5000 ตรงๆ อีก

## ขั้นตอน

### 1. ติดตั้ง nginx
ดาวน์โหลดจากเว็บ nginx แล้วแตกไฟล์ไว้ที่ `C:\nginx\` จากนั้นทดสอบ

```
cd C:\nginx
.\nginx.exe
```

เปิด `http://localhost` ต้องเห็นหน้า **Welcome to nginx!**

### 2. วางไฟล์หน้าเว็บ
คัดลอก 3 ไฟล์จาก `Frontend/ai_studio/` ไปไว้ที่ `C:\image-project\frontend\`

- `login.html`
- `index.html`
- `config.js`

(ใช้ path สั้นๆ ที่ไม่มีช่องว่าง — ถ้าจะชี้ไปที่โฟลเดอร์ใน repo โดยตรงก็ได้ แต่ถ้า path มีช่องว่างต้องครอบด้วย `"..."` ใน `nginx.conf`)

### 3. แก้ `config.js` ในโฟลเดอร์ที่ nginx เสิร์ฟ
```js
const BACKEND_URL = '';
```

ค่าว่างแปลว่าให้หน้าเว็บยิงไปที่ `/api/...` ของ nginx เอง แล้ว nginx ส่งต่อให้ Backend
**แก้เฉพาะตอนใช้ nginx** — ถ้าเปิดหน้าเว็บโดยไม่ผ่าน nginx ต้องใส่ IP ของ Backend ตามเดิม

### 4. ใส่ config
1. สำรองไฟล์เดิม: เปลี่ยนชื่อ `C:\nginx\conf\nginx.conf` เป็น `nginx.conf.default`
2. คัดลอก `nginx/nginx.conf` จาก repo นี้ไปเป็น `C:\nginx\conf\nginx.conf`
3. แก้ 2 จุดที่มี `<<<` กำกับ
   - `root` — โฟลเดอร์หน้าเว็บจากข้อ 2 (ใช้ `/` ไม่ใช่ `\`)
   - `proxy_pass` — IP เครื่อง Backend เช่น `http://172.20.57.86:5000` (ไม่มี `/` ต่อท้าย)

### 5. ตรวจและโหลด config
```
.\nginx.exe -t
.\nginx.exe -s reload
```

`-t` ต้องขึ้น `syntax is ok` และ `test is successful` ก่อนถึงจะ reload

### 6. ทดสอบ
ต้องเปิด Backend (`python app.py`) ไว้ก่อน

| ทดสอบ | ผลที่ควรได้ |
|---|---|
| `http://localhost/` | หน้า login ของ Image Genny |
| `http://localhost/api/health` | `{"service": "Image Processing Backend", "status": "ok"}` |
| สมัคร → login → สร้างภาพ | ได้รูป และ terminal ของ Backend มี log ขึ้น |

จากเครื่องอื่นให้เปลี่ยน `localhost` เป็น IP เครื่อง Frontend และเปิด Windows Firewall ให้ port **80** บนเครื่อง Frontend

## คำสั่งที่ใช้บ่อย

| คำสั่ง | ทำอะไร |
|---|---|
| `nginx.exe` | เปิด nginx |
| `nginx.exe -t` | ตรวจ config |
| `nginx.exe -s reload` | โหลด config ใหม่ |
| `nginx.exe -s quit` | ปิด nginx |

## ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| เปิด nginx ไม่ขึ้น `bind() to 0.0.0.0:80 failed` | มีโปรแกรมอื่นใช้ port 80 — เปลี่ยนเป็น `listen 8080;` แล้วเปิดเว็บที่ `http://localhost:8080` |
| หน้าเว็บขึ้น 404 | `root` ผิด หรือใช้ `\` — ดู `C:\nginx\logs\error.log` |
| `/api/health` ขึ้น 502 Bad Gateway | Backend ไม่ได้เปิด, IP ใน `proxy_pass` ผิด หรือ firewall เครื่อง Backend ไม่เปิด port 5000 |
| `/api/health` ขึ้น 404 | ใส่ `/` ต่อท้าย `proxy_pass` หรือ Backend ยังเป็นโค้ดเก่าที่ไม่มี `/api/health` |
| เจนรูปแล้วได้ 504 Gateway Time-out | ไม่มี `proxy_read_timeout 600s;` ใน `location /api/` |
| หน้าเว็บขึ้น "ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ Backend ได้" | `config.js` ที่ nginx เสิร์ฟยังไม่ได้แก้เป็น `''` — แก้แล้วกด Ctrl+F5 |
| แก้ config แล้วไม่มีผล | ยังไม่ได้ `nginx.exe -s reload` หรือมี nginx ค้างหลายตัว (ปิดทั้งหมดด้วย `taskkill /f /im nginx.exe` แล้วเปิดใหม่) |
