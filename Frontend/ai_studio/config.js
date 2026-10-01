// ตั้งค่าที่ใช้ร่วมกันระหว่าง login.html และ index.html — แก้ IP Backend ที่นี่ที่เดียว
// - ทดสอบเครื่องเดียว: http://127.0.0.1:5000
// - Backend อยู่เครื่องอื่น: ใส่ IP เครื่อง Backend (IP วง LAN หรือ Tailscale) เช่น http://172.20.x.x:5000
// - ถ้าใช้ nginx เสิร์ฟหน้าเว็บและส่งต่อ /api/ ไป Backend: ใช้ '' (ค่าว่าง)
// ไฟล์นี้อยู่ใน Git — แต่ละเครื่องที่เปิดหน้าเว็บต้องมีค่าที่ชี้ไป Backend ตัวเดียวกัน
const BACKEND_URL = 'http://127.0.0.1:5000';
const SESSION_KEY = 'aistudio_session';
