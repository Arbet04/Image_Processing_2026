from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.image_task import ImageTask
from app.services.ai_client import call_ai_service
from flask_jwt_extended import jwt_required, get_jwt_identity

image_bp = Blueprint('image', __name__)

@image_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_image():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    task = ImageTask(user_id=user_id, prompt=prompt, status='processing')
    db.session.add(task)
    db.session.commit()

    ai_response, status_code = call_ai_service(prompt, task.id)

    if status_code == 200 and ai_response:
        task.status = 'completed'
        task.image_url = ai_response.get('image_url', '')
        db.session.commit()
        current_app.logger.info(f"Image generated successfully for Task ID {task.id}")
        return jsonify(task.to_dict()), 200
    else:
        task.status = 'failed'
        db.session.commit()
        current_app.logger.error(f"Image generation failed for Task ID {task.id}")
        return jsonify({
            'error': 'Failed to communicate with AI Service',
            'details': ai_response
        }), 502

@image_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    tasks = ImageTask.query.filter_by(user_id=user_id).order_by(ImageTask.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200
