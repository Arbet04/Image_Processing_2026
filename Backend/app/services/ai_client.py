import requests  # ← ตัวส่ง HTTP ไปหา server อื่น (รอจนได้คำตอบ)
from flask import current_app  # ← ใช้อ่านค่าตั้งค่าและเขียน log

def call_ai_service(prompt, task_id, negative_prompt='', steps=20, width=512, height=512, seed=-1):  # ← ส่งคำขอเจนรูปไป AI Service คืน (ข้อมูล, รหัสสถานะ)
    # ส่งคำขอเจนรูปไปที่ POST {AI_SERVICE_URL}/generate (FastAPI ใน ai-service/main.py)
    # คืนค่า (dict, status_code): สำเร็จ = ({success, image_base64, elapsed_seconds}, 200)
    # ไม่สำเร็จ = ({'error': ข้อความ}, รหัส) โดย 504 = หมดเวลารอ, 500 = ต่อ AI Service ไม่ได้
    # task_id ส่งไปเพื่อให้ log ฝั่ง AI Service โยงกลับมาหา ImageTask ได้เท่านั้น
    ai_base_url = current_app.config['AI_SERVICE_URL']  # ← ที่อยู่ของ AI Service จาก .env
    target_url = f"{ai_base_url}/generate"  # ← endpoint ที่จะเรียก: /generate

    payload = {  # ← ข้อมูลที่ส่งให้ AI Service (ตรงกับ GenerateRequest ใน ai-service/models.py)
        'task_id': task_id,  # ← เลขงาน ใช้ใน log ของ AI Service
        'prompt': prompt,  # ← คำอธิบายรูป
        'negative_prompt': negative_prompt,  # ← สิ่งที่ไม่อยากให้มีในรูป
        'steps': steps,  # ← จำนวนรอบ
        'width': width,  # ← ความกว้าง
        'height': height,  # ← ความสูง
        'seed': seed  # ← เลขสุ่ม
    }

    try:  # ← ลองส่งคำขอ
        current_app.logger.info(f"Sending Task ID {task_id} to AI Service at {target_url}")  # ← เขียน log ว่ากำลังส่งงานไปที่ไหน
        response = requests.post(target_url, json=payload, timeout=current_app.config['AI_SERVICE_TIMEOUT'])  # ← ส่งไป AI Service แล้วรอ นานสุด AI_SERVICE_TIMEOUT วินาที

        if response.status_code == 200:  # ← AI Service ตอบสำเร็จ
            return response.json(), 200  # ← คืน {success, image_base64, elapsed_seconds}
        else:  # ← AI Service ตอบ error เช่น 503 หรือ 502
            current_app.logger.warning(f"AI Service returned status code {response.status_code}: {response.text}")  # ← เขียน log รหัสและข้อความ
            # FastAPI ส่ง error กลับเป็น {"detail": "..."} — ดึงข้อความออกมาให้ Frontend แสดงได้ตรงๆ
            try:  # ← ลองอ่านข้อความ error
                message = response.json().get('detail', response.text)  # ← หยิบข้อความจากช่อง 'detail' ของ FastAPI
            except ValueError:  # ← คำตอบไม่ใช่ JSON
                message = response.text  # ← ใช้ข้อความดิบแทน
            return {'error': str(message)}, response.status_code  # ← คืนสาเหตุและรหัสเดิมจาก AI Service

    except requests.exceptions.Timeout:  # ← รอเกินเวลาที่กำหนด
        current_app.logger.error(f"AI Service timed out for Task ID {task_id}")  # ← เขียน log ว่าหมดเวลา
        return {'error': 'AI Service ใช้เวลานานเกินกำหนด (คิวอาจยาว) กรุณาลองใหม่ภายหลัง'}, 504  # ← คืนข้อความหมดเวลา รหัส 504

    except requests.exceptions.RequestException as e:  # ← ต่อ AI Service ไม่ได้ เช่น ปิดอยู่ หรือ IP/port ผิด
        current_app.logger.error(f"Failed to connect to AI Service at {target_url}: {str(e)}")  # ← เขียน log สาเหตุ
        return {'error': str(e)}, 500  # ← คืนสาเหตุ รหัส 500
