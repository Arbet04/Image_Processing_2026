import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True เปิด Werkzeug debugger ที่รันโค้ดได้จากหน้าเว็บ ห้ามเปิดตอน host='0.0.0.0'
    # ถ้าจำเป็นต้อง debug ให้ตั้ง FLASK_DEBUG=1 ใน .env เฉพาะตอนรันบนเครื่องตัวเอง
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug, threaded=True)
