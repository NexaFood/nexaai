"""
Printer API Service
Handles communication with Prusa (PrusaLink) and Snapmaker printers
"""

import requests
from requests.auth import HTTPDigestAuth
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PrinterStatus:
    """Unified printer status response"""
    online: bool = False
    status: str = 'offline'  # idle, printing, paused, error, offline
    nozzle_temp: float = 0
    nozzle_target: float = 0
    bed_temp: float = 0
    bed_target: float = 0
    progress: float = 0
    time_remaining: int = 0  # seconds
    time_elapsed: int = 0  # seconds
    current_file: str = ''
    job_id: Optional[int] = None
    error_message: str = ''


class PrusaLinkAPI:
    """
    PrusaLink API Client
    Communicates with Prusa printers via PrusaLink HTTP API
    """
    
    def __init__(self, ip_address: str, api_key: str):
        self.base_url = f"http://{ip_address}"
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Api-Key': api_key,
            'Accept': 'application/json'
        })
        self.timeout = 10
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make an API request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            kwargs.setdefault('timeout', self.timeout)
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 204:
                return {'success': True}
            elif response.status_code == 401:
                logger.error(f"PrusaLink authentication failed for {self.base_url}")
                return None
            elif response.ok:
                return response.json()
            else:
                logger.error(f"PrusaLink request failed: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"PrusaLink request timeout for {self.base_url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"PrusaLink connection error for {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"PrusaLink request error: {str(e)}")
            return None
    
    def get_version(self) -> Optional[Dict]:
        """Get API version information"""
        return self._request('GET', '/api/version')
    
    def get_info(self) -> Optional[Dict]:
        """Get printer information"""
        return self._request('GET', '/api/v1/info')
    
    def get_status(self) -> PrinterStatus:
        """Get current printer status"""
        status = PrinterStatus()
        
        data = self._request('GET', '/api/v1/status')
        if not data:
            return status
        
        status.online = True
        
        # Parse printer state
        printer = data.get('printer', {})
        state = printer.get('state', 'IDLE').upper()
        
        state_map = {
            'IDLE': 'idle',
            'READY': 'idle',
            'BUSY': 'printing',
            'PRINTING': 'printing',
            'PAUSED': 'paused',
            'FINISHED': 'idle',
            'STOPPED': 'idle',
            'ERROR': 'error',
            'ATTENTION': 'error'
        }
        status.status = state_map.get(state, 'idle')
        
        # Parse temperatures
        status.nozzle_temp = printer.get('temp_nozzle', 0)
        status.nozzle_target = printer.get('target_nozzle', 0)
        status.bed_temp = printer.get('temp_bed', 0)
        status.bed_target = printer.get('target_bed', 0)
        
        # Parse job info
        job = data.get('job', {})
        if job:
            status.progress = job.get('progress', 0)
            status.time_remaining = job.get('time_remaining', 0)
            status.time_elapsed = job.get('time_printing', 0)
            status.job_id = job.get('id')
        
        return status
    
    def get_job(self) -> Optional[Dict]:
        """Get current job information"""
        return self._request('GET', '/api/v1/job')
    
    def pause_job(self, job_id: int) -> bool:
        """Pause the current print job"""
        result = self._request('PUT', f'/api/v1/job/{job_id}/pause')
        return result is not None
    
    def resume_job(self, job_id: int) -> bool:
        """Resume a paused print job"""
        result = self._request('PUT', f'/api/v1/job/{job_id}/resume')
        return result is not None
    
    def cancel_job(self, job_id: int) -> bool:
        """Cancel/stop the current print job"""
        result = self._request('DELETE', f'/api/v1/job/{job_id}')
        return result is not None
    
    def get_storage(self) -> Optional[Dict]:
        """Get storage information"""
        return self._request('GET', '/api/v1/storage')
    
    def get_files(self, storage: str = 'local', path: str = '/') -> Optional[Dict]:
        """Get files in storage"""
        return self._request('GET', f'/api/v1/files/{storage}{path}')
    
    def upload_file(self, file_path: str, file_data: bytes, 
                    storage: str = 'local', print_after_upload: bool = False,
                    overwrite: bool = True) -> bool:
        """
        Upload a file to the printer
        
        Args:
            file_path: Path where the file should be stored (e.g., '/my_print.gcode')
            file_data: The file content as bytes
            storage: Storage location ('local' or 'sdcard')
            print_after_upload: Whether to start printing immediately
            overwrite: Whether to overwrite existing file
        """
        headers = {
            'Content-Type': 'application/octet-stream',
            'Print-After-Upload': '?1' if print_after_upload else '?0',
            'Overwrite': '?1' if overwrite else '?0'
        }
        
        result = self._request(
            'PUT', 
            f'/api/v1/files/{storage}{file_path}',
            data=file_data,
            headers=headers
        )
        return result is not None
    
    def start_print(self, storage: str, file_path: str) -> bool:
        """Start printing a file"""
        result = self._request('POST', f'/api/v1/files/{storage}{file_path}')
        return result is not None
    
    def delete_file(self, storage: str, file_path: str) -> bool:
        """Delete a file from storage"""
        result = self._request('DELETE', f'/api/v1/files/{storage}{file_path}')
        return result is not None


class SnapmakerAPI:
    """
    Snapmaker API Client
    Communicates with Snapmaker 2.0 printers via HTTP API
    """
    
    def __init__(self, ip_address: str, api_token: str = None):
        self.base_url = f"http://{ip_address}:8080"
        self.api_token = api_token
        self.session = requests.Session()
        self.timeout = 10
        self._connected = False
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make an API request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            kwargs.setdefault('timeout', self.timeout)
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 204:
                # Not yet connected/authorized
                return None
            elif response.ok:
                try:
                    return response.json()
                except:
                    return {'success': True, 'text': response.text}
            else:
                logger.error(f"Snapmaker request failed: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"Snapmaker request timeout for {self.base_url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Snapmaker connection error for {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Snapmaker request error: {str(e)}")
            return None
    
    def connect(self) -> bool:
        """
        Establish connection with the Snapmaker
        If no token is provided, a new one will be generated (requires confirmation on device)
        """
        data = {}
        if self.api_token:
            data['token'] = self.api_token
        
        result = self._request(
            'POST', 
            '/api/v1/connect',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if result:
            # If we got a new token, save it
            if 'token' in result:
                self.api_token = result['token']
            self._connected = True
            return True
        
        return False
    
    def get_status(self) -> PrinterStatus:
        """Get current printer status"""
        status = PrinterStatus()
        
        if not self.api_token:
            return status
        
        timestamp = int(time.time() * 1000)
        data = self._request('GET', f'/api/v1/status?token={self.api_token}&{timestamp}')
        
        if not data:
            return status
        
        status.online = True
        
        # Parse status
        state = data.get('status', 'IDLE').upper()
        state_map = {
            'IDLE': 'idle',
            'RUNNING': 'printing',
            'PAUSED': 'paused',
            'STOPPED': 'idle',
            'UNKNOWN': 'offline'
        }
        status.status = state_map.get(state, 'idle')
        
        # Parse temperatures (if available)
        status.nozzle_temp = data.get('nozzleTemperature', 0)
        status.nozzle_target = data.get('nozzleTargetTemperature', 0)
        status.bed_temp = data.get('heatedBedTemperature', 0)
        status.bed_target = data.get('heatedBedTargetTemperature', 0)
        
        # Parse progress
        status.progress = data.get('progress', 0)
        status.time_remaining = data.get('estimatedTime', 0)
        status.time_elapsed = data.get('elapsedTime', 0)
        status.current_file = data.get('fileName', '')
        
        return status
    
    def get_enclosure_status(self) -> Optional[Dict]:
        """Get enclosure status (if available)"""
        if not self.api_token:
            return None
        
        timestamp = int(time.time() * 1000)
        return self._request('GET', f'/api/v1/enclosure?token={self.api_token}&{timestamp}')
    
    def upload_file(self, filename: str, file_data: bytes) -> bool:
        """
        Upload a G-code file to the Snapmaker
        
        Args:
            filename: Name for the file on the printer
            file_data: The file content as bytes
        """
        if not self.api_token:
            logger.error("No API token - cannot upload")
            return False
        
        # Snapmaker requires multipart form with specific structure
        # Token part must NOT have Content-Type header
        
        # Build multipart manually to control headers
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="token"\r\n\r\n'
            f'{self.api_token}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f'Content-Type: application/octet-stream\r\n\r\n'
        ).encode('utf-8')
        
        body += file_data
        body += f'\r\n--{boundary}--\r\n'.encode('utf-8')
        
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        
        result = self._request(
            'POST',
            '/api/v1/upload',
            data=body,
            headers=headers
        )
        
        return result is not None
    
    def execute_gcode(self, gcode: str) -> bool:
        """
        Execute G-code command(s)
        
        Args:
            gcode: G-code command(s) to execute
        """
        if not self.api_token:
            return False
        
        data = {
            'token': self.api_token,
            'code': gcode
        }
        
        result = self._request(
            'POST',
            '/api/v1/execute_code',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        return result is not None
    
    def start_print(self, filename: str) -> bool:
        """Start printing a file that's already on the printer"""
        # Use G-code to start the print
        return self.execute_gcode(f'M23 {filename}\nM24')
    
    def pause_print(self) -> bool:
        """Pause the current print"""
        return self.execute_gcode('M25')
    
    def resume_print(self) -> bool:
        """Resume a paused print"""
        return self.execute_gcode('M24')
    
    def cancel_print(self) -> bool:
        """Cancel the current print"""
        return self.execute_gcode('M26 S0\nM104 S0\nM140 S0')


class PrinterAPIFactory:
    """Factory for creating printer API clients"""
    
    @staticmethod
    def create(printer_type: str, ip_address: str, api_key: str = None):
        """
        Create appropriate API client based on printer type
        
        Args:
            printer_type: 'prusa' or 'snapmaker'
            ip_address: Printer's IP address
            api_key: API key or token
        """
        if printer_type == 'prusa':
            return PrusaLinkAPI(ip_address, api_key)
        elif printer_type == 'snapmaker':
            return SnapmakerAPI(ip_address, api_key)
        else:
            raise ValueError(f"Unknown printer type: {printer_type}")


def format_time(seconds: int) -> str:
    """Format seconds into human-readable time string"""
    if seconds <= 0:
        return '--:--'
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f'{hours}h {minutes}m'
    else:
        return f'{minutes}m'
