"""
Data Logger Service
Centralizes logging of model generation events, feedback, and errors for training data collection.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

class DataLogger:
    """
    Logs generation events, errors, and user feedback to JSONL files
    for use in future model training and evaluation.
    """
    
    @staticmethod
    def _get_log_file() -> Path:
        """Get the current month's log file path."""
        log_dir = Path(settings.BASE_DIR) / 'training' / 'data' / 'production_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / f"production_{datetime.now().strftime('%Y%m')}.jsonl"

    @classmethod
    def log_entry(cls, 
                  project_id: str, 
                  user_id: str, 
                  model_type: str, 
                  prompt: str, 
                  generated_code: str = None, 
                  rating: str = None, 
                  error_message: str = None,
                  corrected_code: str = None,
                  correction_type: str = None,
                  feedback_text: str = None,
                  success: bool = True,
                  validated: bool = False,
                  metadata: dict = None):
        """
        Log a single entry to the production logs.
        
        Args:
            project_id: ID of the project
            user_id: ID of the user
            model_type: 'overall_model' or 'part'
            prompt: The text prompt used for generation
            generated_code: The AI generated code (optional if failure)
            rating: 'good', 'bad', 'ok', 'corrected', or 'failure' (automatic)
            error_message: Exception message or error description if failed
            corrected_code: User corrected code
            correction_type: 'code_fix' or 'model_improvement'
            feedback_text: User explanation for why the model is good/bad
            success: Whether the ORIGINAL generation was considered successful
            validated: Whether the corrected code was validated
            metadata: Any additional context
        """
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'project_id': str(project_id),
                'user_id': str(user_id),
                'model_type': model_type,
                'prompt': prompt,
                'generated_code': generated_code,
                'rating': rating,
                'error_message': error_message,
                'corrected_code': corrected_code,
                'correction_type': correction_type,
                'feedback_text': feedback_text,
                'model_version': 'final_model', # TODO: Get actual version if possible
                'success': success,
                'validated': validated,
            }
            
            if metadata:
                entry['metadata'] = metadata

            log_file = cls._get_log_file()
            
            # Use append mode - atomic enough for low volume logging
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
                
            logger.info(f"Logged data entry: {rating} (Error: {bool(error_message)})")
            
        except Exception as e:
            # Never fail the main request because logging failed
            logger.error(f"Failed to log data entry: {e}")
