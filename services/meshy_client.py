"""
Meshy.ai API client for 3D model generation.
Python implementation of the Meshy.ai text-to-3D API.
"""
import requests
import time
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MeshyClient:
    """
    Client for interacting with Meshy.ai API.
    Handles text-to-3D model generation requests.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize Meshy client.
        
        Args:
            api_key: Meshy API key (defaults to settings.MESHY_API_KEY)
        """
        self.api_key = api_key or settings.MESHY_API_KEY
        if not self.api_key:
            raise ValueError("MESHY_API_KEY is required")
        
        self.base_url = settings.MESHY_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_text_to_3d_task(self, prompt, art_style='realistic', target_polycount=30000):
        """
        Create a new text-to-3D generation task.
        
        Args:
            prompt: Text description of the 3D model
            art_style: Art style (realistic, cartoon, low-poly, etc.)
            target_polycount: Target polygon count
        
        Returns:
            dict: Task creation response with task ID
        """
        url = f"{self.base_url}/v2/text-to-3d"
        
        payload = {
            'mode': 'preview',
            'prompt': prompt,
            'art_style': art_style,
            'target_polycount': target_polycount,
            'enable_pbr': True
        }
        
        logger.info(f"Creating Meshy task for prompt: {prompt[:100]}")
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Meshy task created: {result.get('result')}")
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Meshy task: {e}")
            raise Exception(f"Meshy API error: {str(e)}")
    
    def get_task_status(self, task_id):
        """
        Get the status of a generation task.
        
        Args:
            task_id: Meshy task ID
        
        Returns:
            dict: Task status and details
        """
        url = f"{self.base_url}/v2/text-to-3d/{task_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            logger.debug(f"Meshy task {task_id} status: {result.get('status')}")
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Meshy task status: {e}")
            raise Exception(f"Meshy API error: {str(e)}")
    
    def refine_task(self, task_id):
        """
        Refine a preview task to get higher quality model.
        
        Args:
            task_id: Preview task ID
        
        Returns:
            dict: Refine task response
        """
        url = f"{self.base_url}/v2/text-to-3d/{task_id}/refine"
        
        try:
            response = requests.post(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Meshy refine task created: {result.get('result')}")
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refine Meshy task: {e}")
            raise Exception(f"Meshy API error: {str(e)}")
    
    def wait_for_completion(self, task_id, max_wait_time=600, poll_interval=10):
        """
        Wait for a task to complete.
        
        Args:
            task_id: Meshy task ID
            max_wait_time: Maximum time to wait in seconds (default: 10 minutes)
            poll_interval: Time between status checks in seconds
        
        Returns:
            dict: Final task status
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_task_status(task_id)
            
            if status['status'] == 'SUCCEEDED':
                logger.info(f"Meshy task {task_id} completed successfully")
                return status
            
            elif status['status'] == 'FAILED':
                error_msg = status.get('error', 'Unknown error')
                logger.error(f"Meshy task {task_id} failed: {error_msg}")
                raise Exception(f"Generation failed: {error_msg}")
            
            elif status['status'] in ['PENDING', 'IN_PROGRESS']:
                logger.debug(f"Meshy task {task_id} still processing...")
                time.sleep(poll_interval)
            
            else:
                logger.warning(f"Unknown Meshy task status: {status['status']}")
                time.sleep(poll_interval)
        
        raise Exception(f"Task {task_id} timed out after {max_wait_time} seconds")
    
    def download_model(self, url, output_path):
        """
        Download a generated model file.
        
        Args:
            url: Model file URL
            output_path: Local path to save the file
        
        Returns:
            str: Path to downloaded file
        """
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded model to {output_path}")
            return output_path
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download model: {e}")
            raise Exception(f"Download error: {str(e)}")
