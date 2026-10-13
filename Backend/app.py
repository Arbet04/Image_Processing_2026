import os  # ← ใช้อ่านค่า environment variable
from app import create_app  # ← ฟังก์ชันสร้างแอป อยู่ใน app/__init__.py

app = create_app()  # ← สร้างแอป Flask พร้อมตั้งค่าทั้งหมด

if __name__ == '__main__':  # ← ทำเฉพาะเมื่อรันไฟล์นี้ตรงๆ ด้วย python app.py
    # debug=True เปิด Werkzeug debugger ที่รันโค้ดได้จากหน้าเว็บ ห้ามเปิดตอน host='0.0.0.0'
    # ถ้าจำเป็นต้อง debug ให้ตั้ง FLASK_DEBUG=1 ใน .env เฉพาะตอนรันบนเครื่องตัวเอง
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'  # ← เปิดโหมด debug เฉพาะเมื่อตั้ง FLASK_DEBUG=1 ใน .env
    app.run(host='0.0.0.0', port=5000, debug=debug, threaded=True)  # ← เปิด server ที่ port 5000 โดย 0.0.0.0 = รับจากทุกเครื่อง, threaded = รับหลายคำขอพร้อมกัน
