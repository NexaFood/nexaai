"""
PrusaLink API Client

Connects to Prusa printers (MK4, MINI+, XL) via PrusaLink API.
Supports file upload, print job management, and status monitoring.

API Documentation: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml
"""

import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)


class PrusaLinkClient:
    """Client for PrusaLink API (Prusa MK4, MINI+, XL)."""
    
    def __init__(self, ip_address: str, api_key: str):
        """
        Initialize PrusaLink client.
        
        Args:
            ip_address: Printer IP address (e.g., "192.168.1.100")
            api_key: PrusaLink API key (from printer settings)
        """
        self.base_url = f"http://{ip_address}/api"
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-Api-Key": api_key
        })
        
        logger.info(f"PrusaLink client initialized for {ip_address}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get printer status.
        
        Returns:
            Dict with:
                - state: Printer state (idle, printing, paused, error)
                - temp_nozzle: Current nozzle temperature
                - temp_bed: Current bed temperature
                - progress: Print progress (0-100)
                - job_name: Current job name (if printing)
        """
        try:
            response = self.session.get(f"{self.base_url}/printer")
            response.raise_for_status()
            
            data = response.json()
            
            # Parse printer state
            state = data.get('state', {}).get('text', 'unknown').lower()
            
            # Map PrusaLink states to our states
            state_map = {
                'idle': 'idle',
                'printing': 'printing',
                'paused': 'paused',
                'error': 'error',
                'busy': 'printing',
                'ready': 'idle'
            }
            
            status = {
                'state': state_map.get(state, 'offline'),
                'temp_nozzle': data.get('temperature', {}).get('tool0', {}).get('actual', 0),
                'temp_bed': data.get('temperature', {}).get('bed', {}).get('actual', 0),
                'progress': data.get('progress', {}).get('completion', 0),
                'job_name': data.get('job', {}).get('file', {}).get('name', '')
            }
            
            logger.info(f"Printer status: {status['state']}")
            return status
            
        except Exception as e:
            logger.error(f"Failed to get printer status: {e}")
            return {
                'state': 'offline',
                'error': str(e)
            }
    
    def upload_file(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to the printer.
        
        Args:
            file_path: Path to STL/GCODE file
            filename: Optional custom filename (default: use original)
            
        Returns:
            Dict with:
                - success: Boolean
                - filename: Uploaded filename
                - error: Error message if failed
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            if filename is None:
                filename = file_path.name
            
            # Upload file
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                response = self.session.post(
                    f"{self.base_url}/files/local",
                    files=files
                )
                response.raise_for_status()
            
            logger.info(f"✓ Uploaded file: {filename}")
            
            return {
                'success': True,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to upload file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_print(self, filename: str) -> Dict[str, Any]:
        """
        Start printing a file.
        
        Args:
            filename: Name of file to print (must be already uploaded)
            
        Returns:
            Dict with:
                - success: Boolean
                - error: Error message if failed
        """
        try:
            # Select and start the file
            response = self.session.post(
                f"{self.base_url}/files/local/{filename}",
                json={'command': 'select', 'print': True}
            )
            response.raise_for_status()
            
            logger.info(f"✓ Started print: {filename}")
            
            return {
                'success': True
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to start print: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_and_print(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file and immediately start printing.
        
        Args:
            file_path: Path to STL/GCODE file
            filename: Optional custom filename
            
        Returns:
            Dict with:
                - success: Boolean
                - filename: Uploaded filename
                - error: Error message if failed
        """
        # Upload file
        upload_result = self.upload_file(file_path, filename)
        
        if not upload_result['success']:
            return upload_result
        
        # Start printing
        print_result = self.start_print(upload_result['filename'])
        
        if not print_result['success']:
            return print_result
        
        return {
            'success': True,
            'filename': upload_result['filename']
        }
    
    def pause_print(self) -> Dict[str, Any]:
        """Pause current print job."""
        try:
            response = self.session.post(
                f"{self.base_url}/job",
                json={'command': 'pause', 'action': 'pause'}
            )
            response.raise_for_status()
            
            logger.info("✓ Print paused")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"✗ Failed to pause print: {e}")
            return {'success': False, 'error': str(e)}
    
    def resume_print(self) -> Dict[str, Any]:
        """Resume paused print job."""
        try:
            response = self.session.post(
                f"{self.base_url}/job",
                json={'command': 'pause', 'action': 'resume'}
            )
            response.raise_for_status()
            
            logger.info("✓ Print resumed")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"✗ Failed to resume print: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_print(self) -> Dict[str, Any]:
        """Cancel current print job."""
        try:
            response = self.session.post(
                f"{self.base_url}/job",
                json={'command': 'cancel'}
            )
            response.raise_for_status()
            
            logger.info("✓ Print cancelled")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"✗ Failed to cancel print: {e}")
            return {'success': False, 'error': str(e)}
