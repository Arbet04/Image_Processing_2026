# AI Studio — Chat & Image Gen

## วิธีเปิดใช้งานใน VS Code

### วิธีที่ 1: Live Server (แนะนำ)
1. ติดตั้ง Extension **"Live Server"** (ritwickdey.LiveServer)
2. คลิกขวาที่ไฟล์ `index.html`
3. เลือก **"Open with Live Server"**
4. เบราว์เซอร์จะเปิดขึ้นมาอัตโนมัติ

### วิธีที่ 2: เปิดตรงจาก File Explorer
1. เปิด File Explorer ไปที่โฟลเดอร์นี้
2. ดับเบิลคลิกที่ `index.html`

### วิธีที่ 3: Debug ด้วย Chrome (ต้องติดตั้ง Debugger for Chrome)
1. กด `F5` หรือไปที่ Run → Start Debugging
2. เลือก "Open with Chrome"

---

## ฟีเจอร์

### 🔐 เข้าสู่ระบบ / สมัครสมาชิก
- เปิดแอปมาจะเจอหน้า Login/Signup ก่อนเสมอ
- สมัครสมาชิกด้วยชื่อ + อีเมล + รหัสผ่าน (อย่างน้อย 6 ตัวอักษร)
- ข้อมูลผู้ใช้และ session เก็บไว้ใน `localStorage` ของเบราว์เซอร์ (ไม่มี backend จริง)
- มีปุ่ม "ออกจากระบบ" ที่มุมขวาบนของหน้าแอปหลัก
- ⚠️ นี่คือ demo auth ฝั่ง client เท่านั้น รหัสผ่านเก็บเป็น plain text ใน localStorage
  เหมาะสำหรับทดสอบ/เดโมในเครื่องเท่านั้น หากจะใช้งานจริงต้องเปลี่ยนไปใช้ระบบ auth
  ฝั่ง server (เช่น Supabase Auth) แทน

### 💬 แชทกับ AI (อับดุล)
- พิมพ์ข้อความแล้วกด Enter
- AI จะตอบกลับเป็นภาษาไทย

### 🎨 เจนรูปภาพ
- **Text to Image**: พิมพ์ prompt แล้วกด Generate
- **Image to Image**: เลือกรูปต้นแบบ + prompt แล้วกด Generate

## ต้องการ
- SD WebUI เปิดด้วย `--api` flag: `webui.bat --api`
- SD WebUI URL ค่าเริ่มต้น: `http://127.0.0.1:7860`
