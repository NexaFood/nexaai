"""
Django management command to check Meshy.ai generation status.
Run this periodically to update model statuses.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from models.mongodb import db, to_object_id
from services.meshy_client import MeshyClient
from services.notifications import notify_owner
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check status of pending 3D model generation jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Run continuously in a loop',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Interval in seconds between checks (default: 10)',
        )

    def handle(self, *args, **options):
        import time
        
        meshy_client = MeshyClient()
        
        while True:
            self.stdout.write(self.style.SUCCESS(f'Checking generation status at {datetime.utcnow()}'))
            
            # Get all processing models from MongoDB
            processing_models = list(db.models.find({'status': 'processing'}))
            
            if not processing_models:
                self.stdout.write('No models currently processing')
            
            for model in processing_models:
                try:
                    model_id = str(model['_id'])
                    self.stdout.write(f'Checking model {model_id}: {model["prompt"][:50]}...')
                    
                    # Get generation job
                    job = db.generation_jobs.find_one({'model_id': model['_id']})
                    
                    if not job:
                        self.stdout.write(self.style.WARNING(f'  No generation job found for model {model_id}'))
                        continue
                    
                    # Check status with Meshy
                    task_status = meshy_client.get_task_status(job['meshy_task_id'])
                    
                    # Update job
                    db.generation_jobs.update_one(
                        {'_id': job['_id']},
                        {'$set': {
                            'meshy_status': task_status['status'],
                            'meshy_response': task_status,
                            'progress': task_status.get('progress', 0),
                            'last_checked_at': datetime.utcnow()
                        }}
                    )
                    
                    self.stdout.write(f'  Status: {task_status["status"]}, Progress: {task_status.get("progress", 0)}%')
                    
                    # Update model if completed
                    if task_status['status'] == 'SUCCEEDED':
                        model_urls = task_status.get('model_urls', {})
                        
                        db.models.update_one(
                            {'_id': model['_id']},
                            {'$set': {
                                'status': 'completed',
                                'completed_at': datetime.utcnow(),
                                'glb_url': model_urls.get('glb'),
                                'obj_url': model_urls.get('obj'),
                                'fbx_url': model_urls.get('fbx'),
                                'usdz_url': model_urls.get('usdz'),
                                'thumbnail_url': task_status.get('thumbnail_url')
                            }}
                        )
                        
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Model {model_id} completed!'))
                        
                        # Notify owner
                        try:
                            notify_owner(
                                title="3D Model Generation Completed",
                                content=f"Model '{model['prompt'][:100]}' completed successfully"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send owner notification: {e}")
                    
                    elif task_status['status'] == 'FAILED':
                        error_message = task_status.get('error', 'Unknown error')
                        
                        db.models.update_one(
                            {'_id': model['_id']},
                            {'$set': {
                                'status': 'failed',
                                'error_message': error_message
                            }}
                        )
                        
                        self.stdout.write(self.style.ERROR(f'  ✗ Model {model_id} failed: {error_message}'))
                        
                        # Notify owner
                        try:
                            notify_owner(
                                title="3D Model Generation Failed",
                                content=f"Model '{model['prompt'][:100]}' failed: {error_message}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send owner notification: {e}")
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Error checking model {model_id}: {str(e)}'))
                    logger.error(f"Error checking generation status for model {model_id}: {e}")
            
            if not options['loop']:
                break
            
            # Wait before next check
            time.sleep(options['interval'])
