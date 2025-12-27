"""
Ledvance Smart+ WiFi Light Controller
Uses TinyTuya protocol 3.5 for local network control
"""

import tinytuya
import colorsys
import time
from typing import Dict, List, Optional, Tuple


class LedvanceLight:
    """Controller for a single Ledvance Smart+ WiFi bulb"""
    
    def __init__(self, dev_id: str, ip: str, local_key: str, name: str = None):
        """
        Initialize Ledvance light controller
        
        Args:
            dev_id: Device ID (Virtual ID from Ledvance app)
            ip: Local IP address
            local_key: Local encryption key from Ledvance app
            name: Friendly name for the light
        """
        self.dev_id = dev_id
        self.ip = ip
        self.local_key = local_key
        self.name = name or dev_id
        self.bulb = None
        self._connect()
    
    def _connect(self):
        """Establish connection to the bulb"""
        try:
            self.bulb = tinytuya.BulbDevice(self.dev_id, self.ip, self.local_key)
            self.bulb.set_version(3.5)
            self.bulb.set_socketPersistent(True)
        except Exception as e:
            print(f"Failed to connect to {self.name} ({self.ip}): {e}")
            raise
    
    def get_status(self) -> Dict:
        """
        Get current status of the bulb
        
        Returns:
            Dict with DPS values and parsed state
        """
        try:
            status = self.bulb.status()
            dps = status.get('dps', {})
            
            # Parse DPS into human-readable format
            parsed = {
                'online': status.get('online', False),
                'power': dps.get('20', False),
                'mode': dps.get('21', 'unknown'),
                'brightness': dps.get('22', 0) // 10 if dps.get('22') else 0,
                'color_temp_raw': dps.get('23', 0),
                'color_temp_kelvin': self._dps23_to_kelvin(dps.get('23', 0)),
                'color_hsv': dps.get('24', ''),
                'raw_dps': dps
            }
            
            return parsed
        except Exception as e:
            print(f"Failed to get status for {self.name}: {e}")
            return {'online': False, 'error': str(e)}
    
    def turn_on(self) -> bool:
        """Turn the light on"""
        try:
            self.bulb.set_value('20', True)
            return True
        except Exception as e:
            print(f"Failed to turn on {self.name}: {e}")
            return False
    
    def turn_off(self) -> bool:
        """Turn the light off"""
        try:
            self.bulb.set_value('20', False)
            return True
        except Exception as e:
            print(f"Failed to turn off {self.name}: {e}")
            return False
    
    def toggle(self) -> bool:
        """Toggle the light on/off"""
        status = self.get_status()
        if status.get('power'):
            return self.turn_off()
        else:
            return self.turn_on()
    
    def set_brightness(self, brightness: int) -> bool:
        """
        Set brightness in white mode
        
        Args:
            brightness: 1-100 percentage
        """
        try:
            brightness = max(1, min(100, brightness))
            payload = {
                '21': 'white',
                '22': brightness * 10
            }
            self.bulb.set_multiple_values(payload)
            return True
        except Exception as e:
            print(f"Failed to set brightness for {self.name}: {e}")
            return False
    
    def set_color_temperature(self, kelvin: int) -> bool:
        """
        Set color temperature in white mode
        
        Args:
            kelvin: 2300-9000 Kelvin
        """
        try:
            kelvin = max(2300, min(9000, kelvin))
            dps23 = self._kelvin_to_dps23(kelvin)
            payload = {
                '21': 'white',
                '23': dps23
            }
            self.bulb.set_multiple_values(payload)
            return True
        except Exception as e:
            print(f"Failed to set color temperature for {self.name}: {e}")
            return False
    
    def set_white(self, brightness: int, kelvin: int) -> bool:
        """
        Set white mode with brightness and color temperature
        
        Args:
            brightness: 1-100 percentage
            kelvin: 2300-9000 Kelvin
        """
        try:
            brightness = max(1, min(100, brightness))
            kelvin = max(2300, min(9000, kelvin))
            dps23 = self._kelvin_to_dps23(kelvin)
            
            payload = {
                '21': 'white',
                '22': brightness * 10,
                '23': dps23
            }
            self.bulb.set_multiple_values(payload)
            return True
        except Exception as e:
            print(f"Failed to set white mode for {self.name}: {e}")
            return False
    
    def set_rgb(self, r: int, g: int, b: int, saturation: int = 100) -> bool:
        """
        Set RGB color
        
        Args:
            r: Red 0-255
            g: Green 0-255
            b: Blue 0-255
            saturation: 1-100 percentage
        """
        try:
            # Switch to colour mode
            self.bulb.set_multiple_values({'21': 'colour'})
            time.sleep(0.3)  # Wait for mode switch
            
            # Convert RGB to HSV
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            saturation = max(1, min(100, saturation))
            
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hue = h * 360
            sat = saturation / 100
            
            # Format as hex HSV
            hsv_hex = self._hsv_to_hex(hue, sat, 1.0)
            self.bulb.set_value('24', hsv_hex)
            return True
        except Exception as e:
            print(f"Failed to set RGB for {self.name}: {e}")
            return False
    
    def set_hsv(self, hue: float, saturation: float, value: float) -> bool:
        """
        Set HSV color directly
        
        Args:
            hue: 0-360 degrees
            saturation: 0-1 (0-100%)
            value: 0-1 (0-100%)
        """
        try:
            # Switch to colour mode
            self.bulb.set_multiple_values({'21': 'colour'})
            time.sleep(0.3)
            
            hsv_hex = self._hsv_to_hex(hue, saturation, value)
            self.bulb.set_value('24', hsv_hex)
            return True
        except Exception as e:
            print(f"Failed to set HSV for {self.name}: {e}")
            return False
    
    # Helper methods
    
    @staticmethod
    def _kelvin_to_dps23(kelvin: int) -> int:
        """Convert Kelvin to DPS 23 value (100-900)"""
        k = max(2300, min(9000, kelvin))
        return int(round((k - 2300) / (9000 - 2300) * 800 + 100))
    
    @staticmethod
    def _dps23_to_kelvin(dps23: int) -> int:
        """Convert DPS 23 value to Kelvin"""
        if dps23 < 100 or dps23 > 900:
            return 0
        return int(round((dps23 - 100) / 800 * (9000 - 2300) + 2300))
    
    @staticmethod
    def _hsv_to_hex(hue: float, saturation: float, value: float) -> str:
        """Convert HSV to 12-digit hex string for DPS 24"""
        h = int(hue % 360)
        s = int(saturation * 1000)
        v = int(value * 1000)
        return f"{h:04x}{s:04x}{v:04x}"
    
    @staticmethod
    def _hex_to_hsv(hsv_hex: str) -> Tuple[float, float, float]:
        """Convert 12-digit hex string to HSV values"""
        if len(hsv_hex) != 12:
            return (0, 0, 0)
        try:
            h = int(hsv_hex[0:4], 16)
            s = int(hsv_hex[4:8], 16) / 1000
            v = int(hsv_hex[8:12], 16) / 1000
            return (h, s, v)
        except ValueError:
            return (0, 0, 0)


class LightGroup:
    """Controller for a group of lights"""
    
    def __init__(self, group_id: str, name: str, lights: List[LedvanceLight]):
        """
        Initialize light group
        
        Args:
            group_id: Unique group identifier
            name: Group name
            lights: List of LedvanceLight objects
        """
        self.group_id = group_id
        self.name = name
        self.lights = lights
    
    def get_status(self) -> Dict:
        """Get status of all lights in group"""
        statuses = []
        for light in self.lights:
            status = light.get_status()
            status['light_name'] = light.name
            status['light_id'] = light.dev_id
            statuses.append(status)
        
        # Calculate group state
        online_count = sum(1 for s in statuses if s.get('online'))
        on_count = sum(1 for s in statuses if s.get('power'))
        
        return {
            'group_id': self.group_id,
            'name': self.name,
            'total_lights': len(self.lights),
            'online_lights': online_count,
            'lights_on': on_count,
            'all_on': on_count == len(self.lights),
            'any_on': on_count > 0,
            'lights': statuses
        }
    
    def turn_on(self) -> Dict[str, bool]:
        """Turn on all lights in group"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.turn_on()
        return results
    
    def turn_off(self) -> Dict[str, bool]:
        """Turn off all lights in group"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.turn_off()
        return results
    
    def toggle(self) -> Dict[str, bool]:
        """Toggle all lights in group"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.toggle()
        return results
    
    def set_brightness(self, brightness: int) -> Dict[str, bool]:
        """Set brightness for all lights"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.set_brightness(brightness)
        return results
    
    def set_color_temperature(self, kelvin: int) -> Dict[str, bool]:
        """Set color temperature for all lights"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.set_color_temperature(kelvin)
        return results
    
    def set_white(self, brightness: int, kelvin: int) -> Dict[str, bool]:
        """Set white mode for all lights"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.set_white(brightness, kelvin)
        return results
    
    def set_rgb(self, r: int, g: int, b: int, saturation: int = 100) -> Dict[str, bool]:
        """Set RGB color for all lights"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.set_rgb(r, g, b, saturation)
        return results
    
    def set_hsv(self, hue: float, saturation: float, value: float) -> Dict[str, bool]:
        """Set HSV color for all lights"""
        results = {}
        for light in self.lights:
            results[light.dev_id] = light.set_hsv(hue, saturation, value)
        return results


class LightManager:
    """Manager for all lights and groups"""
    
    def __init__(self):
        self.lights: Dict[str, LedvanceLight] = {}
        self.groups: Dict[str, LightGroup] = {}
    
    def add_light(self, light: LedvanceLight):
        """Add a light to the manager"""
        self.lights[light.dev_id] = light
    
    def remove_light(self, dev_id: str):
        """Remove a light from the manager"""
        if dev_id in self.lights:
            del self.lights[dev_id]
    
    def get_light(self, dev_id: str) -> Optional[LedvanceLight]:
        """Get a light by device ID"""
        return self.lights.get(dev_id)
    
    def get_all_lights(self) -> List[LedvanceLight]:
        """Get all lights"""
        return list(self.lights.values())
    
    def add_group(self, group: LightGroup):
        """Add a group to the manager"""
        self.groups[group.group_id] = group
    
    def remove_group(self, group_id: str):
        """Remove a group from the manager"""
        if group_id in self.groups:
            del self.groups[group_id]
    
    def get_group(self, group_id: str) -> Optional[LightGroup]:
        """Get a group by ID"""
        return self.groups.get(group_id)
    
    def get_all_groups(self) -> List[LightGroup]:
        """Get all groups"""
        return list(self.groups.values())
    
    def create_group(self, group_id: str, name: str, light_ids: List[str]) -> Optional[LightGroup]:
        """Create a new group from light IDs"""
        lights = [self.get_light(lid) for lid in light_ids if self.get_light(lid)]
        if not lights:
            return None
        
        group = LightGroup(group_id, name, lights)
        self.add_group(group)
        return group
