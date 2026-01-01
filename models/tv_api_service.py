"""
LG webOS TV API Service
Provides control and state monitoring for LG Smart TVs
"""
import socket
import struct
import time
import threading
from typing import Optional, Dict, Any, Callable

# Try to import pywebostv - will need to be installed
try:
    from pywebostv.connection import WebOSClient
    from pywebostv.controls import SystemControl, MediaControl, ApplicationControl, InputControl
    WEBOS_AVAILABLE = True
except ImportError:
    WEBOS_AVAILABLE = False
    print("Warning: pywebostv not installed. Install with: pip install pywebostv")


class LGTVService:
    """Service for controlling LG webOS TVs"""
    
    def __init__(self, ip_address: str, mac_address: str = None, client_key: str = None):
        """
        Initialize LG TV service
        
        Args:
            ip_address: IP address of the TV
            mac_address: MAC address for Wake-on-LAN (optional)
            client_key: Stored client key from previous pairing (optional)
        """
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.client_key = client_key
        self.client = None
        self.system = None
        self.media = None
        self.app = None
        self._connected = False
        self._state_callbacks = []
        self._polling_thread = None
        self._stop_polling = False
        
    def connect(self, timeout: int = 5) -> Dict[str, Any]:
        """
        Connect to the TV
        
        Returns:
            Dict with connection status and client_key if newly paired
        """
        if not WEBOS_AVAILABLE:
            return {
                'success': False,
                'error': 'pywebostv library not installed'
            }
            
        try:
            # Create client with secure connection for newer models
            self.client = WebOSClient(self.ip_address, secure=True)
            self.client.connect()
            
            # Prepare store for registration
            store = {}
            if self.client_key:
                store['client_key'] = self.client_key
            
            # Register with TV
            result = {'success': False, 'needs_pairing': False}
            
            for status in self.client.register(store):
                if status == WebOSClient.PROMPTED:
                    result['needs_pairing'] = True
                    result['message'] = 'Please accept the connection on your TV'
                elif status == WebOSClient.REGISTERED:
                    result['success'] = True
                    result['client_key'] = store.get('client_key')
                    self._connected = True
                    
                    # Initialize controls
                    self.system = SystemControl(self.client)
                    self.media = MediaControl(self.client)
                    self.app = ApplicationControl(self.client)
                    
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def disconnect(self):
        """Disconnect from the TV"""
        self._connected = False
        self.stop_state_polling()
        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None
            
    def is_on(self) -> bool:
        """
        Check if TV is on by attempting a connection
        
        Returns:
            True if TV is on and responding, False otherwise
        """
        try:
            # Try to create a socket connection to check if TV is responding
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.ip_address, 3000))  # webOS uses port 3000
            sock.close()
            return result == 0
        except:
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current TV state
        
        Returns:
            Dict with power state, volume, current app, etc.
        """
        state = {
            'power': 'off',
            'volume': None,
            'muted': None,
            'current_app': None,
            'current_app_id': None
        }
        
        # First check if TV is on
        if not self.is_on():
            return state
            
        state['power'] = 'on'
        
        # If we're connected, get more details
        if self._connected and self.client:
            try:
                # Get volume
                if self.media:
                    vol_info = self.media.get_volume()
                    state['volume'] = vol_info.get('volume')
                    state['muted'] = vol_info.get('muted')
                    
                # Get current app
                if self.app:
                    current = self.app.get_current()
                    if current:
                        state['current_app'] = current.get('title', current.get('appId'))
                        state['current_app_id'] = current.get('appId')
            except Exception as e:
                # Connection might have been lost
                state['error'] = str(e)
                
        return state
    
    def power_on(self) -> Dict[str, Any]:
        """
        Turn on the TV using Wake-on-LAN
        
        Returns:
            Dict with success status
        """
        if not self.mac_address:
            return {
                'success': False,
                'error': 'MAC address not configured'
            }
            
        try:
            # Send Wake-on-LAN magic packet
            self._send_wol(self.mac_address)
            return {
                'success': True,
                'message': 'Wake-on-LAN packet sent'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def power_off(self) -> Dict[str, Any]:
        """
        Turn off the TV
        
        Returns:
            Dict with success status
        """
        print(f"DEBUG power_off: _connected={self._connected}, client_key={self.client_key[:20] if self.client_key else None}...")
        
        if not self._connected or not self.system:
            # Try to connect first
            print("DEBUG power_off: Not connected, attempting to connect...")
            connect_result = self.connect()
            print(f"DEBUG power_off: connect result = {connect_result}")
            if not connect_result.get('success'):
                return {
                    'success': False,
                    'error': f"Not connected to TV: {connect_result.get('error', 'unknown')}"
                }
                
        try:
            print("DEBUG power_off: Sending power_off command...")
            self.system.power_off()
            self._connected = False
            print("DEBUG power_off: Success!")
            return {'success': True}
        except Exception as e:
            print(f"DEBUG power_off: Exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_volume(self, volume: int) -> Dict[str, Any]:
        """Set TV volume (0-100)"""
        if not self._connected or not self.media:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            self.media.set_volume(max(0, min(100, volume)))
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def mute(self, muted: bool = True) -> Dict[str, Any]:
        """Mute or unmute TV"""
        if not self._connected or not self.media:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            self.media.mute(muted)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_apps(self) -> list:
        """Get list of installed apps"""
        if not self._connected or not self.app:
            return []
            
        try:
            return self.app.list_apps()
        except:
            return []
    
    def launch_app(self, app_id: str) -> Dict[str, Any]:
        """Launch an app by ID"""
        if not self._connected or not self.app:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            apps = self.app.list_apps()
            for app in apps:
                if app.get('id') == app_id or app.get('title') == app_id:
                    self.app.launch(app)
                    return {'success': True}
            return {'success': False, 'error': 'App not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_info(self) -> Dict[str, Any]:
        """Get TV information"""
        if not self._connected or not self.system:
            return {}
            
        try:
            return self.system.info()
        except:
            return {}
    
    def _send_wol(self, mac_address: str, broadcast: str = '255.255.255.255'):
        """
        Send Wake-on-LAN magic packet
        
        Args:
            mac_address: MAC address in format 'AA:BB:CC:DD:EE:FF' or 'AA-BB-CC-DD-EE-FF'
            broadcast: Broadcast address (default: 255.255.255.255)
        """
        # Clean MAC address
        mac = mac_address.replace(':', '').replace('-', '').upper()
        
        if len(mac) != 12:
            raise ValueError('Invalid MAC address format')
            
        # Create magic packet
        # 6 bytes of 0xFF followed by MAC address repeated 16 times
        mac_bytes = bytes.fromhex(mac)
        magic_packet = b'\xff' * 6 + mac_bytes * 16
        
        # Send packet
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast, 9))  # Port 9 is standard for WOL
        sock.close()
    
    def start_state_polling(self, callback: Callable[[Dict[str, Any]], None], interval: int = 5):
        """
        Start polling TV state at regular intervals
        
        Args:
            callback: Function to call with state updates
            interval: Polling interval in seconds
        """
        self._state_callbacks.append(callback)
        
        if self._polling_thread is None or not self._polling_thread.is_alive():
            self._stop_polling = False
            self._polling_thread = threading.Thread(target=self._poll_state, args=(interval,))
            self._polling_thread.daemon = True
            self._polling_thread.start()
    
    def stop_state_polling(self):
        """Stop state polling"""
        self._stop_polling = True
        self._state_callbacks = []
    
    def _poll_state(self, interval: int):
        """Internal polling loop"""
        last_state = None
        
        while not self._stop_polling:
            try:
                current_state = self.get_state()
                
                # Only notify if state changed
                if current_state != last_state:
                    for callback in self._state_callbacks:
                        try:
                            callback(current_state)
                        except:
                            pass
                    last_state = current_state
                    
            except Exception as e:
                pass
                
            time.sleep(interval)


# Singleton instance cache
_tv_instances: Dict[str, LGTVService] = {}


def get_tv_service(ip_address: str, mac_address: str = None, client_key: str = None) -> LGTVService:
    """
    Get or create a TV service instance
    
    Args:
        ip_address: IP address of the TV
        mac_address: MAC address for Wake-on-LAN
        client_key: Stored client key from previous pairing
        
    Returns:
        LGTVService instance
    """
    if ip_address not in _tv_instances:
        _tv_instances[ip_address] = LGTVService(ip_address, mac_address, client_key)
    else:
        # Update credentials if provided
        tv = _tv_instances[ip_address]
        if mac_address:
            tv.mac_address = mac_address
        if client_key:
            tv.client_key = client_key
            
    return _tv_instances[ip_address]
