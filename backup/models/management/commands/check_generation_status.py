"""
Django management command to check Meshy.ai generation status.
Handles 2-step workflow: Preview → Refine → Download
Run this periodically to update model statuses.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from models.mongodb import db, to_object_id
from services.meshy_client import MeshyClient
from services.notifications import notify_owner
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check status of pending 3D model generation jobs and handle preview→refine workflow'

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
                    
                    # Determine current stage
                    current_stage = job.get('stage', 'preview')  # 'preview' or 'refine'
                    
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
                    
                    self.stdout.write(f'  Stage: {current_stage}, Status: {task_status["status"]}, Progress: {task_status.get("progress", 0)}%')
                    
                    # Handle task completion based on stage
                    if task_status['status'] == 'SUCCEEDED':
                        
                        if current_stage == 'preview':
                            # Preview completed - start refine task
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Preview completed, starting refine...'))
                            
                            try:
                                # Create refine task
                                refine_result = meshy_client.refine_task(job['meshy_task_id'])
                                refine_task_id = refine_result.get('result')
                                
                                # Update job with refine task ID
                                db.generation_jobs.update_one(
                                    {'_id': job['_id']},
                                    {'$set': {
                                        'stage': 'refine',
                                        'meshy_task_id': refine_task_id,
                                        'preview_task_id': job['meshy_task_id'],
                                        'meshy_status': 'PENDING',
                                        'refine_started_at': datetime.utcnow()
                                    }}
                                )
                                
                                self.stdout.write(self.style.SUCCESS(f'  ✓ Refine task started: {refine_task_id}'))
                                
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'  ✗ Failed to start refine: {e}'))
                                logger.error(f"Failed to start refine for model {model_id}: {e}")
                        
                        elif current_stage == 'refine':
                            # Refine completed - download GLB and mark as complete
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Refine completed, downloading GLB...'))
                            
                            try:
                                model_urls = task_status.get('model_urls', {})
                                glb_url = model_urls.get('glb')
                                
                                if glb_url:
                                    # Create download directory
                                    download_dir = os.path.join(settings.MEDIA_ROOT, 'models')
                                    os.makedirs(download_dir, exist_ok=True)
                                    
                                    # Download GLB file
                                    filename = f"{model_id}.glb"
                                    output_path = os.path.join(download_dir, filename)
                                    meshy_client.download_model(glb_url, output_path)
                                    
                                    # Update model as completed
                                    db.models.update_one(
                                        {'_id': model['_id']},
                                        {'$set': {
                                            'status': 'completed',
                                            'completed_at': datetime.utcnow(),
                                            'glb_url': glb_url,
                                            'glb_file_path': output_path,
                                            'fbx_url': model_urls.get('fbx'),
                                            'usdz_url': model_urls.get('usdz'),
                                            'thumbnail_url': task_status.get('thumbnail_url')
                                        }}
                                    )
                                    
                                    self.stdout.write(self.style.SUCCESS(f'  ✓ Model {model_id} completed and downloaded!'))
                                    
                                    # Notify owner
                                    try:
                                        notify_owner(
                                            title="3D Model Generation Completed",
                                            content=f"Model '{model['prompt'][:100]}' completed with textures and downloaded"
                                        )
                                    except Exception as e:
                                        logger.warning(f"Failed to send owner notification: {e}")
                                else:
                                    self.stdout.write(self.style.ERROR(f'  ✗ No GLB URL in response'))
                                    
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'  ✗ Failed to download GLB: {e}'))
                                logger.error(f"Failed to download GLB for model {model_id}: {e}")
                    
                    elif task_status['status'] == 'FAILED':
                        error_message = task_status.get('error', 'Unknown error')
                        
                        db.models.update_one(
                            {'_id': model['_id']},
                            {'$set': {
                                'status': 'failed',
                                'error_message': f'{current_stage} failed: {error_message}'
                            }}
                        )
                        
                        self.stdout.write(self.style.ERROR(f'  ✗ Model {model_id} failed at {current_stage}: {error_message}'))
                        
                        # Notify owner
                        try:
                            notify_owner(
                                title="3D Model Generation Failed",
                                content=f"Model '{model['prompt'][:100]}' failed at {current_stage}: {error_message}"
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
