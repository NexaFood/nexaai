"""
LG webOS TV API Service
Provides control and state monitoring for LG Smart TVs
Uses aiowebostv library for reliable async communication
"""
import socket
import asyncio
import threading
from typing import Optional, Dict, Any, Callable

# Try to import aiowebostv - more stable than pywebostv
WEBOS_AVAILABLE = False
WEBOS_IMPORT_ERROR = None
try:
    from aiowebostv import WebOsClient
    WEBOS_AVAILABLE = True
    print("aiowebostv imported successfully")
except ImportError as e:
    WEBOS_IMPORT_ERROR = str(e)
    print(f"Warning: aiowebostv import failed: {e}")
except Exception as e:
    WEBOS_IMPORT_ERROR = str(e)
    print(f"Warning: aiowebostv import error: {e}")


def run_async(coro):
    """Helper to run async code from sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop, create a new one in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(coro)


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
        self._connected = False
        self._state_callbacks = []
        self._polling_thread = None
        self._stop_polling = False
        
    async def _connect_async(self, timeout: int = 10) -> Dict[str, Any]:
        """Async connect to the TV"""
        print(f"DEBUG _connect_async: WEBOS_AVAILABLE={WEBOS_AVAILABLE}, WEBOS_IMPORT_ERROR={WEBOS_IMPORT_ERROR}")
        if not WEBOS_AVAILABLE:
            return {
                'success': False,
                'error': f'aiowebostv library not available: {WEBOS_IMPORT_ERROR}. Run: pip install aiowebostv'
            }
            
        try:
            print(f"DEBUG _connect_async: Creating WebOsClient for {self.ip_address}")
            client = WebOsClient(self.ip_address, client_key=self.client_key)
            
            print(f"DEBUG _connect_async: Calling client.connect() with timeout={timeout}")
            await asyncio.wait_for(client.connect(), timeout=timeout)
            
            # Get the client key after connection
            new_client_key = client.client_key
            print(f"DEBUG _connect_async: Got client_key={new_client_key[:20] if new_client_key else None}...")
            
            await client.disconnect()
            
            self._connected = True
            return {
                'success': True,
                'client_key': new_client_key,
                'message': 'Connected successfully'
            }
            
        except asyncio.TimeoutError:
            print("DEBUG _connect_async: TimeoutError")
            return {
                'success': False,
                'error': 'Connection timed out. Make sure TV is on and accepts the connection prompt.'
            }
        except Exception as e:
            print(f"DEBUG _connect_async: Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def connect(self, timeout: int = 10) -> Dict[str, Any]:
        """Connect to the TV (sync wrapper)"""
        return run_async(self._connect_async(timeout))
            
    def is_on(self) -> bool:
        """
        Check if TV is on by attempting a connection
        
        Returns:
            True if TV is on and responding, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.ip_address, 3000))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get current TV state"""
        state = {
            'power': 'off',
            'volume': None,
            'muted': None,
            'current_app': None,
            'current_app_id': None
        }
        
        if not self.is_on():
            return state
            
        state['power'] = 'on'
        
        # Try to get more details if we have a client key
        if self.client_key:
            try:
                details = run_async(self._get_details_async())
                state.update(details)
            except Exception as e:
                state['error'] = str(e)
                
        return state
    
    async def _get_details_async(self) -> Dict[str, Any]:
        """Get detailed TV state asynchronously"""
        details = {}
        try:
            client = WebOsClient(self.ip_address, client_key=self.client_key)
            await asyncio.wait_for(client.connect(), timeout=5)
            
            # Get volume
            try:
                vol_info = await client.get_volume()
                details['volume'] = vol_info.get('volume')
                details['muted'] = vol_info.get('muted')
            except:
                pass
                
            # Get current app
            try:
                current = await client.get_current_app()
                if current:
                    details['current_app_id'] = current
            except:
                pass
                
            await client.disconnect()
        except:
            pass
            
        return details
    
    def power_on(self) -> Dict[str, Any]:
        """Turn on the TV using Wake-on-LAN"""
        if not self.mac_address:
            return {
                'success': False,
                'error': 'MAC address not configured'
            }
            
        try:
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
    
    async def _power_off_async(self) -> Dict[str, Any]:
        """Turn off the TV asynchronously"""
        if not WEBOS_AVAILABLE:
            return {'success': False, 'error': 'aiowebostv library not installed'}
            
        if not self.client_key:
            return {'success': False, 'error': 'TV not paired. Please pair the TV first.'}
            
        try:
            print(f"DEBUG: Connecting to TV at {self.ip_address} with client_key...")
            client = WebOsClient(self.ip_address, client_key=self.client_key)
            await asyncio.wait_for(client.connect(), timeout=10)
            
            print("DEBUG: Connected, sending power_off command...")
            await client.power_off()
            
            print("DEBUG: Power off sent, disconnecting...")
            await client.disconnect()
            
            self._connected = False
            return {'success': True}
            
        except asyncio.TimeoutError:
            return {'success': False, 'error': 'Connection timed out'}
        except Exception as e:
            print(f"DEBUG: power_off error: {e}")
            return {'success': False, 'error': str(e)}
    
    def power_off(self) -> Dict[str, Any]:
        """Turn off the TV (sync wrapper)"""
        print(f"DEBUG power_off: client_key={'set' if self.client_key else 'None'}")
        return run_async(self._power_off_async())
    
    async def _set_volume_async(self, volume: int) -> Dict[str, Any]:
        """Set volume asynchronously"""
        if not self.client_key:
            return {'success': False, 'error': 'TV not paired'}
            
        try:
            client = WebOsClient(self.ip_address, client_key=self.client_key)
            await asyncio.wait_for(client.connect(), timeout=5)
            await client.set_volume(max(0, min(100, volume)))
            await client.disconnect()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def set_volume(self, volume: int) -> Dict[str, Any]:
        """Set TV volume (0-100)"""
        return run_async(self._set_volume_async(volume))
    
    async def _mute_async(self, muted: bool) -> Dict[str, Any]:
        """Mute/unmute asynchronously"""
        if not self.client_key:
            return {'success': False, 'error': 'TV not paired'}
            
        try:
            client = WebOsClient(self.ip_address, client_key=self.client_key)
            await asyncio.wait_for(client.connect(), timeout=5)
            await client.set_mute(muted)
            await client.disconnect()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def mute(self, muted: bool = True) -> Dict[str, Any]:
        """Mute or unmute TV"""
        return run_async(self._mute_async(muted))
    
    async def _get_apps_async(self) -> list:
        """Get apps asynchronously"""
        if not self.client_key:
            return []
            
        try:
            client = WebOsClient(self.ip_address, client_key=self.client_key)
            await asyncio.wait_for(client.connect(), timeout=5)
            apps = await client.get_apps()
            await client.disconnect()
            return apps or []
        except:
            return []
    
    def get_apps(self) -> list:
        """Get list of installed apps"""
        return run_async(self._get_apps_async())
    
    async def _launch_app_async(self, app_id: str) -> Dict[str, Any]:
        """Launch app asynchronously"""
        if not self.client_key:
            return {'success': False, 'error': 'TV not paired'}
            
        try:
            client = WebOsClient(self.ip_address, client_key=self.client_key)
            await asyncio.wait_for(client.connect(), timeout=5)
            await client.launch_app(app_id)
            await client.disconnect()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def launch_app(self, app_id: str) -> Dict[str, Any]:
        """Launch an app on the TV"""
        return run_async(self._launch_app_async(app_id))
    
    def _send_wol(self, mac_address: str, broadcast: str = '255.255.255.255'):
        """Send Wake-on-LAN magic packet"""
        mac = mac_address.replace(':', '').replace('-', '').upper()
        
        if len(mac) != 12:
            raise ValueError('Invalid MAC address format')
            
        mac_bytes = bytes.fromhex(mac)
        magic_packet = b'\xff' * 6 + mac_bytes * 16
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast, 9))
        sock.close()
    
    def start_state_polling(self, callback: Callable[[Dict[str, Any]], None], interval: int = 5):
        """Start polling TV state at regular intervals"""
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
        import time
        last_state = None
        
        while not self._stop_polling:
            try:
                current_state = self.get_state()
                
                if current_state != last_state:
                    for callback in self._state_callbacks:
                        try:
                            callback(current_state)
                        except:
                            pass
                    last_state = current_state
            except:
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
