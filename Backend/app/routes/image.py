from flask import Blueprint, request, jsonify, current_app  # ← Blueprint, คำขอที่เข้ามา, ตอบ JSON และตัวแอปปัจจุบัน
from app.extensions import db  # ← ตัวจัดการฐานข้อมูล
from app.models.image_task import ImageTask  # ← ตารางงานเจนรูป
from app.services.ai_client import call_ai_service  # ← ฟังก์ชันที่ส่งคำขอไป AI Service
from flask_jwt_extended import jwt_required, get_jwt_identity  # ← บังคับ login และอ่านเลขผู้ใช้จาก token

image_bp = Blueprint('image', __name__)  # ← กลุ่ม endpoint ของรูป (ต่อจาก /api/image)


def _int_or_default(value, default):  # ← แปลงค่าเป็นตัวเลข ถ้าไม่ได้ส่งมาใช้ค่าเริ่มต้น
    # ค่าที่ไม่ได้ส่งมา หรือส่งมาเป็น null/"" ให้ใช้ค่า default แทน
    if value is None or value == '':  # ← ไม่ได้ส่งมา หรือส่งค่าว่าง
        return default  # ← ใช้ค่าเริ่มต้น
    return int(value)  # ← แปลงเป็นจำนวนเต็ม (แปลงไม่ได้จะ error ไปที่ except ด้านล่าง)


@image_bp.route('/generate', methods=['POST'])  # ← ผูกฟังก์ชันด้านล่างกับ POST /api/image/generate
@jwt_required()  # ← ต้อง login (บัญชีที่ถูกระงับถูกปฏิเสธตรงนี้)
def generate_image():  # ← ทำงานเมื่อผู้ใช้กดปุ่มสร้างภาพ
    # รับ {prompt, negative_prompt, steps, width, height, seed} จาก Frontend
    # request นี้รอจน AI Service เจนรูปเสร็จ (รวมเวลารอคิว) แล้วตอบ ImageTask.to_dict() กลับไป
    user_id = int(get_jwt_identity())  # ← เลข id ของผู้ใช้ อ่านจาก token
    data = request.get_json() or {}  # ← อ่าน JSON ที่หน้าเว็บส่งมา
    prompt = data.get('prompt')  # ← คำอธิบายรูป

    if not prompt:  # ← ไม่ได้ใส่ prompt
        return jsonify({'error': 'Prompt is required'}), 400  # ← ตอบ 400

    try:  # ← ลองแปลงค่าตัวเลข
        options = {  # ← ค่าตั้งค่าที่จะส่งต่อให้ AI Service
            'negative_prompt': data.get('negative_prompt') or '',  # ← สิ่งที่ไม่อยากให้มีในรูป ไม่ส่งมา = ข้อความว่าง
            'steps': _int_or_default(data.get('steps'), 20),  # ← จำนวนรอบ ค่าเริ่มต้น 20
            'width': _int_or_default(data.get('width'), 512),  # ← ความกว้าง ค่าเริ่มต้น 512
            'height': _int_or_default(data.get('height'), 512),  # ← ความสูง ค่าเริ่มต้น 512
            'seed': _int_or_default(data.get('seed'), -1),  # ← เลขสุ่ม ค่าเริ่มต้น -1 = สุ่มใหม่
        }
    except (TypeError, ValueError):  # ← มีค่าที่แปลงเป็นตัวเลขไม่ได้
        return jsonify({'error': 'steps/width/height/seed ต้องเป็นตัวเลขจำนวนเต็ม'}), 400  # ← ตอบ 400

    task = ImageTask(user_id=user_id, prompt=prompt, status='processing')  # ← สร้างรายการงาน สถานะเริ่มต้น 'processing'
    db.session.add(task)  # ← เตรียมเพิ่มลงฐานข้อมูล
    db.session.commit()  # ← บันทึกก่อนเรียก AI เพื่อให้ได้เลขงาน task.id

    try:  # ← ลองเรียก AI Service
        ai_response, status_code = call_ai_service(prompt, task.id, **options)  # ← ส่งต่อไป AI Service แล้วรอจนเสร็จ (จุดที่ใช้เวลานานที่สุด)
    except Exception:  # ← เกิดปัญหาที่ไม่คาดคิด
        # กันไม่ให้ task ค้างสถานะ processing ถ้ามี error ที่ไม่คาดคิด
        task.status = 'failed'  # ← บันทึกว่างานล้มเหลว
        db.session.commit()  # ← บันทึกลงฐานข้อมูล
        raise  # ← โยนปัญหาต่อ (Flask ตอบ 500)

    # AI Service ตอบกลับเป็น {success, image_base64, elapsed_seconds, error} — ไม่มี field image_url
    image_base64 = ai_response.get('image_base64', '') if ai_response else ''  # ← หยิบรูปจากคำตอบ ถ้าไม่มีได้ข้อความว่าง

    if status_code == 200 and image_base64:  # ← สำเร็จและมีรูปกลับมา
        task.status = 'completed'  # ← งานเสร็จ
        # คอลัมน์ image_url เก็บ base64 string ของรูป (ไม่ใช่ URL จริง) เพื่อไม่ต้อง migrate ชื่อคอลัมน์
        task.image_url = image_base64  # ← เก็บรูป (base64) ลงในงาน
        db.session.commit()  # ← บันทึกลงฐานข้อมูล
        current_app.logger.info(f"Image generated successfully for Task ID {task.id}")  # ← เขียน log ว่าสำเร็จ
        return jsonify(task.to_dict()), 200  # ← ตอบ 200 พร้อมรูป หน้าเว็บนำไปแสดง
    else:  # ← AI Service ไม่สำเร็จ หรือไม่มีรูป
        task.status = 'failed'  # ← บันทึกว่างานล้มเหลว
        db.session.commit()  # ← บันทึกลงฐานข้อมูล
        current_app.logger.error(f"Image generation failed for Task ID {task.id}")  # ← เขียน log ว่าล้มเหลว
        details = (ai_response or {}).get('error') or 'AI Service ไม่ได้ส่งรูปกลับมา'  # ← สาเหตุจาก AI Service เช่น คิวเต็ม หรือต่อ Forge Neo ไม่ได้
        return jsonify({  # ← ตอบ 502 พร้อมสาเหตุ
            'error': 'Failed to communicate with AI Service',  # ← ข้อความทั่วไป
            'details': details  # ← สาเหตุจริงที่หน้าเว็บนำไปแสดง
        }), 502

@image_bp.route('/history', methods=['GET'])  # ← ผูกฟังก์ชันด้านล่างกับ GET /api/image/history
@jwt_required()  # ← ต้อง login
def get_history():  # ← ประวัติงานของผู้ใช้
    # ไม่ส่ง base64 ของรูปมาด้วย (รูปละหลาย MB) — ถ้าต้องการรูป ให้เรียก GET /api/image/<id>
    # หรือส่ง ?include_images=1 ถ้าต้องการทั้งหมดจริงๆ
    user_id = int(get_jwt_identity())  # ← เลข id ของผู้ใช้ อ่านจาก token
    include_images = request.args.get('include_images') == '1'  # ← ต้องการรูปด้วยหรือไม่ (?include_images=1)
    tasks = ImageTask.query.filter_by(user_id=user_id).order_by(ImageTask.created_at.desc()).all()  # ← เฉพาะงานของคนนี้ เรียงจากใหม่ไปเก่า
    return jsonify([t.to_dict(include_image=include_images) for t in tasks]), 200  # ← ตอบเป็นรายการงาน

@image_bp.route('/<int:task_id>', methods=['GET'])  # ← ผูกฟังก์ชันด้านล่างกับ GET /api/image/<เลขงาน>
@jwt_required()  # ← ต้อง login
def get_task(task_id):  # ← ดูงานเดียวพร้อมรูป
    user_id = int(get_jwt_identity())  # ← เลข id ของผู้ใช้ อ่านจาก token
    task = ImageTask.query.filter_by(id=task_id, user_id=user_id).first()  # ← ต้องตรงทั้งเลขงานและเจ้าของ จึงดูงานของคนอื่นไม่ได้
    if not task:  # ← ไม่มีงานนี้ หรือไม่ใช่ของตัวเอง
        return jsonify({'error': 'Task not found'}), 404  # ← ตอบ 404
    return jsonify(task.to_dict()), 200  # ← ตอบข้อมูลงานพร้อมรูป
