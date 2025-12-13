"""
Feedback API for continuous learning.
Collects user ratings and corrections for generated models.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from models.mongodb import db, to_object_id
from models.views import session_login_required
from pathlib import Path
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


@session_login_required
@require_http_methods(["POST"])
def submit_feedback(request, project_id):
    """
    Submit feedback for generated models to enable continuous learning.
    
    Logs feedback to production_logs for future model retraining.
    
    Request body:
        {
            "model_type": "overall_model" | "part",
            "rating": "good" | "ok" | "bad" | "corrected",
            "corrected_code": "..." (optional, for corrections)
        }
    """
    try:
        # Parse request
        data = json.loads(request.body)
        model_type = data.get('model_type')
        rating = data.get('rating')
        corrected_code = data.get('corrected_code')
        
        # Validate
        if not model_type or not rating:
            return JsonResponse({
                'success': False,
                'error': 'model_type and rating are required'
            }, status=400)
        
        # Get project
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return JsonResponse({
                'success': False,
                'error': 'Project not found'
            }, status=404)
        
        # Get the original generation data
        if model_type == 'overall_model':
            original_prompt = project.get('original_prompt', '')
            generated_code = project.get('overall_model_code', '')  # May be empty if generation failed
        else:
            # For parts, would need part_id
            return JsonResponse({
                'success': False,
                'error': 'Part feedback not yet implemented'
            }, status=400)
        
        # Allow feedback even without generated code (for failures)
        if not generated_code and rating != 'corrected':
            generated_code = '<generation_failed>'
        
        # Create feedback entry
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'project_id': project_id,
            'user_id': str(request.user.id),
            'model_type': model_type,
            'rating': rating,
            'prompt': original_prompt,
            'generated_code': generated_code,
            'corrected_code': corrected_code,
            'model_version': 'final_model',  # Track which model version generated this
            'success': rating in ['good', 'corrected'],  # For training data filtering
        }
        
        # Log to production logs directory
        log_dir = Path(settings.BASE_DIR) / 'training' / 'data' / 'production_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Append to monthly log file
        log_file = log_dir / f"production_{datetime.now().strftime('%Y%m')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(feedback_entry) + '\n')
        
        logger.info(f"Feedback logged: {rating} for {model_type} in project {project_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Feedback recorded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
