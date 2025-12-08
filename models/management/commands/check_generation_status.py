"""
Django management command to check Meshy.ai generation status.
Run this periodically to update model statuses.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from models.models import Model3D, GenerationJob
from services.meshy_client import MeshyClient
from services.notifications import notify_owner
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
            self.stdout.write(self.style.SUCCESS(f'Checking generation status at {timezone.now()}'))
            
            # Get all processing models
            processing_models = Model3D.objects.filter(status='processing')
            
            if not processing_models.exists():
                self.stdout.write('No models currently processing')
            
            for model in processing_models:
                try:
                    job = model.generation_job
                    self.stdout.write(f'Checking model {model.id}: {model.prompt[:50]}...')
                    
                    # Check status with Meshy
                    task_status = meshy_client.get_task_status(job.meshy_task_id)
                    
                    # Update job
                    job.meshy_status = task_status['status']
                    job.meshy_response = task_status
                    job.progress = task_status.get('progress', 0)
                    job.last_checked_at = timezone.now()
                    job.save()
                    
                    self.stdout.write(f'  Status: {job.meshy_status}, Progress: {job.progress}%')
                    
                    # Update model if completed
                    if task_status['status'] == 'SUCCEEDED':
                        model.status = 'completed'
                        model.completed_at = timezone.now()
                        
                        # Store file URLs
                        model_urls = task_status.get('model_urls', {})
                        model.glb_url = model_urls.get('glb')
                        model.obj_url = model_urls.get('obj')
                        model.fbx_url = model_urls.get('fbx')
                        model.usdz_url = model_urls.get('usdz')
                        model.thumbnail_url = task_status.get('thumbnail_url')
                        
                        model.save()
                        
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Model {model.id} completed!'))
                        
                        # Notify owner
                        try:
                            notify_owner(
                                title="3D Model Generation Completed",
                                content=f"Model '{model.prompt[:100]}' completed successfully"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send owner notification: {e}")
                    
                    elif task_status['status'] == 'FAILED':
                        model.status = 'failed'
                        model.error_message = task_status.get('error', 'Unknown error')
                        model.save()
                        
                        self.stdout.write(self.style.ERROR(f'  ✗ Model {model.id} failed: {model.error_message}'))
                        
                        # Notify owner
                        try:
                            notify_owner(
                                title="3D Model Generation Failed",
                                content=f"Model '{model.prompt[:100]}' failed: {model.error_message}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send owner notification: {e}")
                
                except GenerationJob.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  No generation job found for model {model.id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Error checking model {model.id}: {str(e)}'))
                    logger.error(f"Error checking generation status for model {model.id}: {e}")
            
            if not options['loop']:
                break
            
            # Wait before next check
            time.sleep(options['interval'])
