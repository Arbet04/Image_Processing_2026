from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.image_task import ImageTask
from app.services.ai_client import call_ai_service
from flask_jwt_extended import jwt_required, get_jwt_identity

image_bp = Blueprint('image', __name__)


def _int_or_default(value, default):
    # ค่าที่ไม่ได้ส่งมา หรือส่งมาเป็น null/"" ให้ใช้ค่า default แทน
    if value is None or value == '':
        return default
    return int(value)


@image_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_image():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        options = {
            'negative_prompt': data.get('negative_prompt') or '',
            'steps': _int_or_default(data.get('steps'), 20),
            'width': _int_or_default(data.get('width'), 512),
            'height': _int_or_default(data.get('height'), 512),
            'seed': _int_or_default(data.get('seed'), -1),
        }
    except (TypeError, ValueError):
        return jsonify({'error': 'steps/width/height/seed ต้องเป็นตัวเลขจำนวนเต็ม'}), 400

    task = ImageTask(user_id=user_id, prompt=prompt, status='processing')
    db.session.add(task)
    db.session.commit()

    try:
        ai_response, status_code = call_ai_service(prompt, task.id, **options)
    except Exception:
        # กันไม่ให้ task ค้างสถานะ processing ถ้ามี error ที่ไม่คาดคิด
        task.status = 'failed'
        db.session.commit()
        raise

    # AI Service ตอบกลับเป็น {success, image_base64, elapsed_seconds, error} — ไม่มี field image_url
    image_base64 = ai_response.get('image_base64', '') if ai_response else ''

    if status_code == 200 and image_base64:
        task.status = 'completed'
        # คอลัมน์ image_url เก็บ base64 string ของรูป (ไม่ใช่ URL จริง) เพื่อไม่ต้อง migrate ชื่อคอลัมน์
        task.image_url = image_base64
        db.session.commit()
        current_app.logger.info(f"Image generated successfully for Task ID {task.id}")
        return jsonify(task.to_dict()), 200
    else:
        task.status = 'failed'
        db.session.commit()
        current_app.logger.error(f"Image generation failed for Task ID {task.id}")
        details = (ai_response or {}).get('error') or 'AI Service ไม่ได้ส่งรูปกลับมา'
        return jsonify({
            'error': 'Failed to communicate with AI Service',
            'details': details
        }), 502

@image_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    # ไม่ส่ง base64 ของรูปมาด้วย (รูปละหลาย MB) — ถ้าต้องการรูป ให้เรียก GET /api/image/<id>
    # หรือส่ง ?include_images=1 ถ้าต้องการทั้งหมดจริงๆ
    user_id = int(get_jwt_identity())
    include_images = request.args.get('include_images') == '1'
    tasks = ImageTask.query.filter_by(user_id=user_id).order_by(ImageTask.created_at.desc()).all()
    return jsonify([t.to_dict(include_image=include_images) for t in tasks]), 200

@image_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user_id = int(get_jwt_identity())
    task = ImageTask.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task.to_dict()), 200
