"""
Snapmaker API Client

Connects to Snapmaker 2.0 machines via HTTP API.
Supports 3D printing, CNC milling, and laser engraving modes.

API Documentation: https://snapmaker.github.io/Documentation/gcode/G-code%20Reference.html
"""

import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


class SnapmakerClient:
    """Client for Snapmaker 2.0 API (A150/A250/A350)."""
    
    def __init__(self, ip_address: str, token: Optional[str] = None):
        """
        Initialize Snapmaker client.
        
        Args:
            ip_address: Printer IP address (e.g., "192.168.1.100")
            token: Optional API token (Snapmaker 2.0 uses token authentication)
        """
        self.base_url = f"http://{ip_address}:8080/api/v1"
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                "token": token
            })
        
        logger.info(f"Snapmaker client initialized for {ip_address}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get printer status.
        
        Returns:
            Dict with:
                - state: Machine state (idle, running, paused)
                - mode: Current mode (3d_print, cnc, laser)
                - progress: Job progress (0-100)
                - temp_nozzle: Nozzle temperature (3D print mode)
                - temp_bed: Bed temperature (3D print mode)
        """
        try:
            response = self.session.get(f"{self.base_url}/status")
            response.raise_for_status()
            
            data = response.json()
            
            # Parse state
            state_text = data.get('state', 'IDLE').upper()
            
            state_map = {
                'IDLE': 'idle',
                'RUNNING': 'printing',
                'PAUSED': 'paused',
                'STOPPED': 'idle',
                'UNKNOWN': 'offline'
            }
            
            # Determine current mode
            mode = data.get('headType', '3dp')
            mode_map = {
                '3dp': '3d_print',
                'cnc': 'cnc',
                'laser': 'laser'
            }
            
            status = {
                'state': state_map.get(state_text, 'offline'),
                'mode': mode_map.get(mode, '3d_print'),
                'progress': data.get('progress', 0),
                'temp_nozzle': data.get('nozzleTemperature', 0),
                'temp_bed': data.get('heatedBedTemperature', 0)
            }
            
            logger.info(f"Snapmaker status: {status['state']} ({status['mode']} mode)")
            return status
            
        except Exception as e:
            logger.error(f"Failed to get Snapmaker status: {e}")
            return {
                'state': 'offline',
                'error': str(e)
            }
    
    def upload_file(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to Snapmaker.
        
        Args:
            file_path: Path to file (STL/GCODE for 3D print, NC for CNC, etc.)
            filename: Optional custom filename
            
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
                files = {'file': (filename, f)}
                response = self.session.post(
                    f"{self.base_url}/upload",
                    files=files
                )
                response.raise_for_status()
            
            logger.info(f"✓ Uploaded file to Snapmaker: {filename}")
            
            return {
                'success': True,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to upload file to Snapmaker: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_print(self, filename: str) -> Dict[str, Any]:
        """
        Start a job (print/CNC/laser).
        
        Args:
            filename: Name of file to run
            
        Returns:
            Dict with success status
        """
        try:
            response = self.session.post(
                f"{self.base_url}/start_print",
                json={'filename': filename}
            )
            response.raise_for_status()
            
            logger.info(f"✓ Started job on Snapmaker: {filename}")
            
            return {
                'success': True
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to start job on Snapmaker: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_and_print(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file and immediately start the job.
        
        Args:
            file_path: Path to file
            filename: Optional custom filename
            
        Returns:
            Dict with success status
        """
        # Upload file
        upload_result = self.upload_file(file_path, filename)
        
        if not upload_result['success']:
            return upload_result
        
        # Start job
        print_result = self.start_print(upload_result['filename'])
        
        if not print_result['success']:
            return print_result
        
        return {
            'success': True,
            'filename': upload_result['filename']
        }
    
    def pause_job(self) -> Dict[str, Any]:
        """Pause current job."""
        try:
            response = self.session.post(f"{self.base_url}/pause")
            response.raise_for_status()
            
            logger.info("✓ Snapmaker job paused")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"✗ Failed to pause Snapmaker job: {e}")
            return {'success': False, 'error': str(e)}
    
    def resume_job(self) -> Dict[str, Any]:
        """Resume paused job."""
        try:
            response = self.session.post(f"{self.base_url}/resume")
            response.raise_for_status()
            
            logger.info("✓ Snapmaker job resumed")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"✗ Failed to resume Snapmaker job: {e}")
            return {'success': False, 'error': str(e)}
    
    def stop_job(self) -> Dict[str, Any]:
        """Stop current job."""
        try:
            response = self.session.post(f"{self.base_url}/stop")
            response.raise_for_status()
            
            logger.info("✓ Snapmaker job stopped")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"✗ Failed to stop Snapmaker job: {e}")
            return {'success': False, 'error': str(e)}
    
    def change_mode(self, mode: str) -> Dict[str, Any]:
        """
        Change Snapmaker mode (3D Print / CNC / Laser).
        
        Args:
            mode: '3d_print', 'cnc', or 'laser'
            
        Returns:
            Dict with success status
        """
        mode_map = {
            '3d_print': '3dp',
            'cnc': 'cnc',
            'laser': 'laser'
        }
        
        if mode not in mode_map:
            return {
                'success': False,
                'error': f'Invalid mode: {mode}'
            }
        
        try:
            response = self.session.post(
                f"{self.base_url}/change_tool",
                json={'headType': mode_map[mode]}
            )
            response.raise_for_status()
            
            logger.info(f"✓ Changed Snapmaker mode to: {mode}")
            
            return {
                'success': True,
                'mode': mode
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to change Snapmaker mode: {e}")
            return {
                'success': False,
                'error': str(e)
            }
