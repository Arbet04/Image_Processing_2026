# Database

> **ตอนนี้ใช้ SQLite อยู่** — `DATABASE_URL=sqlite:///app.db` (ค่าเริ่มต้นใน `Backend\.env.example`)
>
> PostgreSQL ของโปรเจคอยู่ที่ **เครื่องเพื่อน (คนทำ Database)** ถ้าจะต่อต้องใช้ **IP ของเครื่องเพื่อน และทั้งสองเครื่องต้องอยู่ในวงเครือข่ายเดียวกัน** (Wi-Fi เดียวกัน หรือ Tailscale เดียวกัน)
> จึงใส่ SQLite ไว้ก่อน เพื่อให้ทุกคน clone แล้ว **รันทดสอบได้ตามปกติ** โดยไม่ต้องรอต่อเครื่องเพื่อน
> SQLite ไม่ต้องติดตั้งหรือตั้งค่าอะไร — Backend สร้างไฟล์ `Backend\instance\app.db` และตารางให้เองตอนเปิดครั้งแรก
>
> เมื่อพร้อมย้ายไป PostgreSQL: ทำข้อ 2–4 บนเครื่องเพื่อน → เครื่อง Backend ทดสอบข้อ 4.4 ผ่าน → ทำข้อ 5

ฐานข้อมูลเก็บข้อมูลผู้ใช้และประวัติการเจนรูป มีแค่ Backend ที่ต่อเข้ามา

```
ตอนนี้:    Backend :5000 ──► SQLite (ไฟล์ Backend\instance\app.db ในเครื่อง Backend)
ภายหลัง:  Backend :5000 ──(SQLAlchemy + psycopg2, ผ่าน IP)──► PostgreSQL :5432 ที่เครื่องเพื่อน
                                                       database: image_processing_2026
```

**ไม่ต้องเขียน SQL สร้างตารางเอง** — ทั้ง SQLite และ PostgreSQL เปิด Backend ครั้งแรกแล้ว Backend จะสร้างตารางให้ตาม model ในโค้ด (`db.create_all()`)
งานฝั่ง DB คือติดตั้ง PostgreSQL สร้าง database กับ user แล้วให้ Backend ต่อเข้ามาได้

## ข้อมูลที่ไม่ได้อยู่ใน Git

- รหัสผ่าน PostgreSQL และ IP ของเครื่องเพื่อนอยู่ใน `Backend\.env` ของเครื่อง Backend เท่านั้น — `.env` อยู่ใน `.gitignore` จึงไม่ขึ้น Git
- clone มาแล้วจะไม่มี `.env` ต้องสร้างจาก `Backend\.env.example` ([Backend/README.md](../Backend/README.md) ข้อ 2–3)
- คนทำ Database บอก IP และรหัสผ่านให้คนทำ Backend เป็นการส่วนตัว ห้ามเขียนลงไฟล์ใน repo หรือ commit
- ไฟล์ข้อมูลของ PostgreSQL (`C:\Program Files\PostgreSQL\...\data`) อยู่นอก repo ส่วนไฟล์ SQLite (`Backend\instance\app.db`) อยู่ใน `.gitignore` — ข้อมูลผู้ใช้จึงอยู่เฉพาะเครื่องนั้น ไม่ได้ขึ้น Git

---

## 1. สิ่งที่ต้องตัดสินใจก่อน: DB อยู่เครื่องไหน

| แบบ | `DATABASE_URL` ใช้ host | ต้องทำข้อ 4 (เปิดให้เครื่องอื่นต่อ) ไหม |
|---|---|---|
| ก. อยู่เครื่องเดียวกับ Backend | `127.0.0.1` | ไม่ต้อง |
| **ข. อยู่เครื่องแยก (ตอนนี้ใช้แบบนี้ — เครื่องเพื่อน)** | IP เครื่อง DB | ต้อง |

แบบ ข. ต้องรู้ IP ของเครื่อง Backend ด้วย (ให้คนทำ Backend หาด้วย `ipconfig`)
IP วง Wi-Fi เปลี่ยนได้เมื่อต่อใหม่ ทั้ง IP เครื่อง DB และเครื่อง Backend — นัดทดสอบทุกครั้งให้เช็คก่อน (Tailscale IP ไม่เปลี่ยน)

---

## 2. ติดตั้ง PostgreSQL (ครั้งแรกครั้งเดียว — เครื่อง DB)

1. ดาวน์โหลดตัวติดตั้ง Windows จาก https://www.postgresql.org/download/windows/ (ตัวติดตั้งของ EDB)
2. ระหว่างติดตั้ง:
   - ตั้งรหัสผ่านของ user `postgres` (superuser) — **จดไว้** ต้องใช้ในข้อ 3
   - port ใช้ค่าเริ่มต้น `5432`
   - ไม่ต้องติดตั้ง Stack Builder
3. หลังติดตั้ง PostgreSQL จะรันเป็น Windows Service และเปิดเองทุกครั้งที่เปิดเครื่อง เช็คด้วย:
   ```powershell
   Get-Service postgresql*
   ```
   ต้องขึ้น `Running`

คำสั่ง `psql` อยู่ที่ `C:\Program Files\PostgreSQL\<เวอร์ชัน>\bin\psql.exe` (เช่น `...\17\bin\psql.exe`)
ด้านล่างใช้ตัวแปร `$psql` แทน — ตั้งครั้งเดียวต่อ terminal (แก้เลขเวอร์ชันให้ตรงกับที่ติดตั้ง):

```powershell
$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
```

---

## 3. สร้าง database และ user ของโปรเจค (ครั้งแรกครั้งเดียว — เครื่อง DB)

```powershell
& $psql -U postgres
```

ใส่รหัสผ่าน `postgres` จากข้อ 2 แล้วพิมพ์ใน `psql` ทีละบรรทัด (เปลี่ยน `<รหัสผ่าน>` เป็นรหัสที่ตั้งเอง):

```sql
CREATE USER app_user WITH PASSWORD '<รหัสผ่าน>';
CREATE DATABASE image_processing_2026 OWNER app_user;
\q
```

- `OWNER app_user` ทำให้ `app_user` สร้างตารางใน database นี้ได้ (จำเป็นสำหรับ `db.create_all()` ของ Backend)
- รหัสผ่านควรใช้แค่ตัวอักษรอังกฤษกับตัวเลข ถ้ามี `@ : / # %` ต้องแปลงก่อนใส่ใน URL (ดูข้อ 5)
- **ห้าม commit หรือส่งรหัสผ่านนี้ในแชทกลุ่ม** ให้คนทำ Backend พิมพ์ลง `.env` เอง

ทดสอบว่า login ด้วย user ใหม่ได้:

```powershell
& $psql -U app_user -d image_processing_2026 -h 127.0.0.1 -c "SELECT current_user, current_database();"
```

ต้องได้ `app_user | image_processing_2026`

---

## 4. เปิดให้เครื่อง Backend ต่อเข้ามา (เฉพาะแบบ ข.)

ไฟล์ตั้งค่าอยู่ที่ `C:\Program Files\PostgreSQL\<เวอร์ชัน>\data\` ต้องเปิดแก้ด้วยโปรแกรมที่ **Run as Administrator** (เช่น Notepad)

**4.1 `postgresql.conf`** — ให้รับการเชื่อมต่อจากเครือข่าย หาบรรทัด `listen_addresses` แล้วแก้เป็น:

```
listen_addresses = '*'
```

(ถ้าขึ้นต้นด้วย `#` ให้ลบ `#` ออก)

**4.2 `pg_hba.conf`** — อนุญาตเฉพาะเครื่อง Backend เพิ่มบรรทัดนี้ไว้ **ท้ายไฟล์**:

```
host    image_processing_2026    app_user    <IP เครื่อง Backend>/32    scram-sha-256
```

**4.3 restart PostgreSQL และเปิด firewall** (PowerShell แบบ Run as Administrator):

```powershell
Get-Service postgresql* | Restart-Service
New-NetFirewallRule -DisplayName "Image Genny PostgreSQL 5432" -Direction Inbound -Protocol TCP -LocalPort 5432 -RemoteAddress <IP เครื่อง Backend> -Action Allow
```

**4.4 ทดสอบจากเครื่อง Backend:**

```powershell
Test-NetConnection <IP เครื่อง DB> -Port 5432
```

ต้องได้ `TcpTestSucceeded : True` ถ้าได้ `False` ให้เช็ค firewall, `listen_addresses` และว่าอยู่เครือข่ายเดียวกัน

IP ของ Wi-Fi เปลี่ยนได้เมื่อต่อใหม่ — ถ้า IP เครื่อง Backend เปลี่ยน ต้องแก้ `pg_hba.conf` และ firewall ตาม (Tailscale IP ไม่เปลี่ยน)

---

## 5. ให้ Backend ใช้ PostgreSQL (เครื่อง Backend)

**5.1** เปิด `Backend\.env` แล้วแก้ `DATABASE_URL`:

```
DATABASE_URL=postgresql+psycopg2://app_user:<รหัสผ่าน>@<IP เครื่อง DB หรือ 127.0.0.1>:5432/image_processing_2026
```

- ต้องขึ้นต้นด้วย `postgresql+psycopg2://` ให้ตรงกับ driver `psycopg2-binary` ใน `Backend\requirements.txt`
  **ห้ามใช้ `postgresql://` เฉยๆ** — SQLAlchemy 2.1 (ที่ pip ติดตั้งให้) จะไปหา driver ตัวอื่น (`psycopg`) แล้ว Backend เปิดไม่ขึ้น
- ถ้ารหัสผ่านมีอักขระพิเศษ ให้แปลงก่อนด้วย:
  ```powershell
  python -c "import urllib.parse; print(urllib.parse.quote('<รหัสผ่าน>', safe=''))"
  ```

**5.2** restart Backend (`Ctrl+C` แล้ว `python app.py`) — ค่าใน `.env` ถูกอ่านตอนเปิดเท่านั้น
ตอนเปิดครั้งแรก Backend จะสร้างตาราง `users` และ `image_tasks` ให้เอง

---

## 6. ตรวจว่าใช้ได้

1. Backend เปิดขึ้นโดยไม่มี error เรื่องฐานข้อมูลใน terminal
2. เช็คว่ามีตาราง (เครื่อง DB):
   ```powershell
   & $psql -U app_user -d image_processing_2026 -h 127.0.0.1 -c "\dt"
   ```
   ต้องเห็น `users` และ `image_tasks`
3. เปิดหน้าเว็บ → สมัครสมาชิก → login → สร้างภาพ 1 รูป
4. เช็คว่ามีข้อมูลเข้า:
   ```powershell
   & $psql -U app_user -d image_processing_2026 -h 127.0.0.1 -c "SELECT id, username, role, status FROM users;"
   & $psql -U app_user -d image_processing_2026 -h 127.0.0.1 -c "SELECT id, user_id, status, length(image_url) FROM image_tasks ORDER BY id DESC LIMIT 5;"
   ```
   ต้องเห็นชื่อที่สมัคร และงานที่ `status = completed` ซึ่ง `length(image_url)` เป็นตัวเลขหลักแสนขึ้นไป (รูปเก็บเป็น base64)

---

## 7. ตาราง

Backend สร้างตามไฟล์ model — **ถ้าจะเปลี่ยนตาราง ต้องแก้ไฟล์ model ด้วยและแจ้งคนทำ Backend**

**`users`** — [Backend/app/models/user.py](../Backend/app/models/user.py)

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | |
| `username` | VARCHAR(80) UNIQUE NOT NULL | |
| `password_hash` | VARCHAR(255) NOT NULL | เก็บ hash ไม่ใช่รหัสผ่านจริง |
| `role` | VARCHAR(20) NOT NULL | `user` หรือ `admin` |
| `status` | VARCHAR(20) NOT NULL | `active` หรือ `suspended` |
| `created_at` | TIMESTAMP NOT NULL | |
| `updated_at` | TIMESTAMP NOT NULL | |
| `last_login` | TIMESTAMP | ว่างได้ |

**`image_tasks`** — [Backend/app/models/image_task.py](../Backend/app/models/image_task.py)

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | ส่งไปให้ AI Service เป็น `task_id` |
| `user_id` | INTEGER NOT NULL → `users.id` | เจ้าของงาน |
| `prompt` | TEXT NOT NULL | |
| `status` | VARCHAR(20) NOT NULL | `processing`, `completed` หรือ `failed` |
| `image_url` | TEXT | เก็บรูปเป็น **base64** (รูปละประมาณ 0.5–2 MB) ไม่ใช่ URL |
| `created_at` | TIMESTAMP NOT NULL | |

### `001_add_user_columns.sql`

ใช้เฉพาะเมื่อตาราง `users` ถูกสร้างไว้ก่อนมีฟีเจอร์ admin (ไม่มีคอลัมน์ `role`, `status`, `updated_at`, `last_login`) — **database ใหม่ไม่ต้องรัน**

```powershell
& $psql -U app_user -d image_processing_2026 -h 127.0.0.1 -f Database\001_add_user_columns.sql
```

(รันจากโฟลเดอร์โปรเจค)

---

## 8. ปัญหาที่เจอบ่อย

| อาการ (ใน terminal ของ Backend) | สาเหตุ / วิธีแก้ |
|---|---|
| `Connection refused` หรือค้างจน `timeout expired` | PostgreSQL ไม่ได้รัน, IP/port ผิด, firewall ไม่เปิด 5432 หรือไม่ได้ตั้ง `listen_addresses` — ทดสอบด้วยข้อ 4.4 |
| `password authentication failed for user "app_user"` | รหัสผ่านใน `DATABASE_URL` ผิด หรือมีอักขระพิเศษที่ไม่ได้แปลง (ข้อ 5.1) |
| `no pg_hba.conf entry for host "..."` | ยังไม่ได้เพิ่ม IP เครื่อง Backend ใน `pg_hba.conf` หรือ IP เปลี่ยน — แก้แล้ว restart PostgreSQL |
| `database "image_processing_2026" does not exist` | ยังไม่ได้ทำข้อ 3 หรือพิมพ์ชื่อผิด |
| `permission denied for schema public` | database ไม่ได้สร้างด้วย `OWNER app_user` — รันใน psql (user postgres): `ALTER DATABASE image_processing_2026 OWNER TO app_user;` |
| `UnicodeDecodeError: 'utf-8' codec can't decode ...` | PostgreSQL ส่งข้อความ error เป็นภาษาของ Windows ที่ psycopg2 อ่านไม่ได้ — สาเหตุจริงมักเป็นรหัสผ่านผิดหรือชื่อ database ผิด ให้ลองต่อด้วย `psql` ตามข้อ 3 เพื่อดูข้อความจริง |
| `ModuleNotFoundError: No module named 'psycopg2'` | ยังไม่ได้ `pip install -r requirements.txt` ใน venv ของ Backend |
| `ModuleNotFoundError: No module named 'psycopg'` | `DATABASE_URL` ขึ้นต้นด้วย `postgresql://` หรือ `postgresql+psycopg://` — เปลี่ยนเป็น `postgresql+psycopg2://` |
| `column users.role does not exist` | ตาราง `users` เป็นของเก่า — รัน `001_add_user_columns.sql` |

---

## ใช้ SQLite แทน (ค่าที่ใช้อยู่ตอนนี้)

ใช้เมื่อยังต่อ PostgreSQL ที่เครื่องเพื่อนไม่ได้ เช่น เพื่อนไม่ได้เปิดเครื่อง หรือ IP เปลี่ยน — ไฟล์ `Backend\instance\app.db` สร้างให้เอง ตั้งใน `Backend\.env`:

```
DATABASE_URL=sqlite:///app.db
```

ข้อมูลใน SQLite แยกจาก PostgreSQL ถ้าสลับกลับไป PostgreSQL ต้องสมัครสมาชิกใหม่
