import requests
from flask import current_app

def call_ai_service(prompt, task_id):
    ai_base_url = current_app.config['AI_SERVICE_URL']
    target_url = f"{ai_base_url}/generate"

    payload = {
        'task_id': task_id,
        'prompt': prompt
    }

    try:
        current_app.logger.info(f"Sending request to AI Service at {target_url}")
        response = requests.post(target_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            return response.json(), 200
        else:
            current_app.logger.warning(f"AI Service returned status code {response.status_code}: {response.text}")
            return {'error': response.text}, response.status_code

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to connect to AI Service at {target_url}: {str(e)}")
        return {'error': str(e)}, 500
