import requests
from flask import current_app

def call_ai_service(prompt, task_id, negative_prompt='', steps=20, width=512, height=512, seed=-1):
    # ส่งคำขอเจนรูปไปที่ POST {AI_SERVICE_URL}/generate (FastAPI ใน ai-service/main.py)
    # คืนค่า (dict, status_code): สำเร็จ = ({success, image_base64, elapsed_seconds}, 200)
    # ไม่สำเร็จ = ({'error': ข้อความ}, รหัส) โดย 504 = หมดเวลารอ, 500 = ต่อ AI Service ไม่ได้
    # task_id ส่งไปเพื่อให้ log ฝั่ง AI Service โยงกลับมาหา ImageTask ได้เท่านั้น
    ai_base_url = current_app.config['AI_SERVICE_URL']
    target_url = f"{ai_base_url}/generate"

    payload = {
        'task_id': task_id,
        'prompt': prompt,
        'negative_prompt': negative_prompt,
        'steps': steps,
        'width': width,
        'height': height,
        'seed': seed
    }

    try:
        current_app.logger.info(f"Sending Task ID {task_id} to AI Service at {target_url}")
        response = requests.post(target_url, json=payload, timeout=current_app.config['AI_SERVICE_TIMEOUT'])

        if response.status_code == 200:
            return response.json(), 200
        else:
            current_app.logger.warning(f"AI Service returned status code {response.status_code}: {response.text}")
            # FastAPI ส่ง error กลับเป็น {"detail": "..."} — ดึงข้อความออกมาให้ Frontend แสดงได้ตรงๆ
            try:
                message = response.json().get('detail', response.text)
            except ValueError:
                message = response.text
            return {'error': str(message)}, response.status_code

    except requests.exceptions.Timeout:
        current_app.logger.error(f"AI Service timed out for Task ID {task_id}")
        return {'error': 'AI Service ใช้เวลานานเกินกำหนด (คิวอาจยาว) กรุณาลองใหม่ภายหลัง'}, 504

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to connect to AI Service at {target_url}: {str(e)}")
        return {'error': str(e)}, 500
