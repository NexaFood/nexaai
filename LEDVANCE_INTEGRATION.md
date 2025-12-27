# Ledvance Smart+ WiFi Integration

Complete integration for controlling Ledvance Smart+ WiFi bulbs locally using the Tuya protocol 3.5.

## Overview

This integration allows you to control Ledvance Smart+ WiFi bulbs directly on your local network without cloud dependency. It supports individual light control, grouping, and all color/brightness features.

## Features

### Individual Light Control
- **Power:** On/Off/Toggle
- **Brightness:** 1-100%
- **Color Temperature:** 2300K-9000K (warm to cool white)
- **RGB Color:** Full RGB spectrum with saturation control
- **Status Monitoring:** Real-time status updates

### Group Control
- Create groups of multiple lights
- Control all lights in a group simultaneously
- Same features as individual control
- Per-room organization

## Prerequisites

### 1. Get Device Credentials

For each Ledvance bulb, you need three pieces of information:

1. **Device ID** (Virtual ID)
2. **Local IP Address**
3. **Local Key** (Encryption key)

#### How to Get Credentials:

**Option A: From Ledvance App**
1. Install the Ledvance Smart+ app
2. Add your bulbs to the app
3. The device ID and local key are stored in the app's database
4. You can find the IP address in your router's DHCP client list

**Option B: Using TinyTuya Scanner**
```bash
# Activate virtual environment
cd /home/ubuntu/nexaai
source venv_cadquery/bin/activate

# Scan network for Tuya devices
python -m tinytuya scan
```

This will discover devices but you'll still need the local key from the Ledvance app or Tuya IoT platform.

**Option C: Tuya IoT Platform**
1. Go to https://iot.tuya.com/
2. Create a developer account
3. Link your Ledvance app account
4. Access device credentials through the platform

### 2. Assign Static IP Addresses

It's recommended to assign static IP addresses to your bulbs in your router's DHCP settings to prevent connection issues when IPs change.

## API Endpoints

### Light Management

#### List All Lights
```
GET /api/ledvance/lights/
```

**Response:**
```json
{
  "success": true,
  "lights": [
    {
      "id": "light_id",
      "dev_id": "device_id",
      "name": "Living Room Ceiling",
      "ip": "192.168.1.100",
      "room": "Living Room",
      "online": true,
      "power": true,
      "mode": "white",
      "brightness": 80,
      "color_temp_kelvin": 4000,
      "color_hsv": ""
    }
  ]
}
```

#### Add New Light
```
POST /api/ledvance/lights/add/
```

**Parameters:**
- `name` (required): Friendly name
- `dev_id` (required): Device ID
- `ip` (required): Local IP address
- `local_key` (required): Encryption key
- `room` (optional): Room name

**Response:**
```json
{
  "success": true,
  "light": {
    "id": "light_id",
    "name": "Living Room Ceiling",
    "dev_id": "device_id",
    "ip": "192.168.1.100",
    "room": "Living Room"
  }
}
```

#### Remove Light
```
POST /api/ledvance/lights/<light_id>/remove/
```

#### Toggle Light
```
POST /api/ledvance/lights/<light_id>/toggle/
```

**Response:**
```json
{
  "success": true,
  "power": true
}
```

#### Set Brightness
```
POST /api/ledvance/lights/<light_id>/brightness/
```

**Parameters:**
- `brightness`: 1-100 (percentage)

#### Set RGB Color
```
POST /api/ledvance/lights/<light_id>/color/
```

**Parameters:**
- `r`: 0-255 (red)
- `g`: 0-255 (green)
- `b`: 0-255 (blue)
- `saturation`: 1-100 (optional, default 100)

#### Set Color Temperature
```
POST /api/ledvance/lights/<light_id>/temperature/
```

**Parameters:**
- `kelvin`: 2300-9000 (color temperature in Kelvin)

### Group Management

#### List All Groups
```
GET /api/ledvance/groups/
```

**Response:**
```json
{
  "success": true,
  "groups": [
    {
      "id": "group_id",
      "name": "Living Room",
      "room": "Living Room",
      "total_lights": 3,
      "online_lights": 3,
      "lights_on": 2,
      "all_on": false,
      "any_on": true
    }
  ]
}
```

#### Create Group
```
POST /api/ledvance/groups/create/
```

**Parameters:**
- `name` (required): Group name
- `room` (optional): Room name
- `light_ids` (required): JSON array or comma-separated list of light IDs

**Example:**
```javascript
{
  "name": "Living Room",
  "room": "Living Room",
  "light_ids": ["light1", "light2", "light3"]
}
```

#### Toggle Group
```
POST /api/ledvance/groups/<group_id>/toggle/
```

#### Set Group Brightness
```
POST /api/ledvance/groups/<group_id>/brightness/
```

**Parameters:**
- `brightness`: 1-100

#### Set Group Color
```
POST /api/ledvance/groups/<group_id>/color/
```

**Parameters:**
- `r`: 0-255
- `g`: 0-255
- `b`: 0-255
- `saturation`: 1-100 (optional)

## Database Schema

### Lights Collection (`ledvance_lights`)
```javascript
{
  "_id": ObjectId,
  "user_id": "user123",
  "name": "Living Room Ceiling",
  "dev_id": "a1b2c3d4e5f6g7h8ijklmn",
  "ip": "192.168.1.100",
  "local_key": "WQ!zYx8#kLp3vBn@",
  "room": "Living Room",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Groups Collection (`ledvance_groups`)
```javascript
{
  "_id": ObjectId,
  "user_id": "user123",
  "name": "Living Room",
  "room": "Living Room",
  "light_ids": ["dev_id1", "dev_id2", "dev_id3"],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

## Python Usage Examples

### Control a Single Light

```python
from models.ledvance_controller import LedvanceLight

# Initialize light
light = LedvanceLight(
    dev_id="a1b2c3d4e5f6g7h8ijklmn",
    ip="192.168.1.100",
    local_key="WQ!zYx8#kLp3vBn@",
    name="Living Room Ceiling"
)

# Get status
status = light.get_status()
print(f"Power: {status['power']}, Brightness: {status['brightness']}%")

# Turn on
light.turn_on()

# Set brightness to 80%
light.set_brightness(80)

# Set warm white (2700K)
light.set_color_temperature(2700)

# Set RGB color (red)
light.set_rgb(255, 0, 0, saturation=100)

# Toggle
light.toggle()
```

### Control a Group

```python
from models.ledvance_controller import LedvanceLight, LightGroup

# Create lights
light1 = LedvanceLight("dev_id1", "192.168.1.100", "key1", "Light 1")
light2 = LedvanceLight("dev_id2", "192.168.1.101", "key2", "Light 2")
light3 = LedvanceLight("dev_id3", "192.168.1.102", "key3", "Light 3")

# Create group
group = LightGroup(
    group_id="living_room",
    name="Living Room",
    lights=[light1, light2, light3]
)

# Control all lights
group.turn_on()
group.set_brightness(75)
group.set_rgb(255, 200, 100)  # Warm orange
```

### Using the Light Manager

```python
from models.ledvance_controller import LightManager

# Initialize manager
manager = LightManager()

# Add lights
manager.add_light(light1)
manager.add_light(light2)
manager.add_light(light3)

# Create group from light IDs
group = manager.create_group(
    group_id="living_room",
    name="Living Room",
    light_ids=["dev_id1", "dev_id2", "dev_id3"]
)

# Get all lights
all_lights = manager.get_all_lights()

# Get specific light
light = manager.get_light("dev_id1")
```

## Technical Details

### Tuya Protocol 3.5

Ledvance bulbs use Tuya's protocol version 3.5 for local communication. The protocol uses:
- **Encryption:** AES encryption with local key
- **Transport:** TCP/IP over WiFi
- **Port:** Default Tuya port (6668)

### DPS (Data Point System)

The bulbs expose the following data points:

| DPS | Function | Values | Notes |
|-----|----------|--------|-------|
| 20 | Power | true/false | On/Off state |
| 21 | Mode | "white"/"colour" | Must set before other commands |
| 22 | Brightness | 10-1000 | Multiply percentage by 10 |
| 23 | Color Temp | 100-900 | Calculated from Kelvin |
| 24 | RGB Color | 12-hex HSV | Format: HHHHSSSSVVVV |

### Color Temperature Conversion

```python
def kelvin_to_dps23(kelvin):
    k = max(2300, min(9000, kelvin))
    return int(round((k - 2300) / (9000 - 2300) * 800 + 100))

def dps23_to_kelvin(dps23):
    return int(round((dps23 - 100) / 800 * (9000 - 2300) + 2300))
```

### HSV Color Format

The RGB color is stored as HSV in hexadecimal:
- **Hue:** 0-360 degrees (4 hex digits: 0000-0168)
- **Saturation:** 0-1000 (4 hex digits: 0000-03e8)
- **Value:** 0-1000 (4 hex digits: 0000-03e8)

Example: `00b403e803e8` = Hue 180°, Saturation 100%, Value 100% (Cyan)

## Troubleshooting

### Connection Issues

**Problem:** Can't connect to bulb
**Solutions:**
1. Verify the bulb is on the same network
2. Check IP address is correct (use router DHCP list)
3. Verify local key is correct
4. Ensure firewall isn't blocking connections
5. Try pinging the bulb's IP address

### Bulb Not Responding

**Problem:** Commands don't work
**Solutions:**
1. Check bulb is powered on
2. Verify WiFi connection is stable
3. Try power cycling the bulb
4. Check if bulb firmware needs update
5. Verify protocol version is 3.5

### Wrong Colors

**Problem:** Colors don't match expected
**Solutions:**
1. Ensure you're using RGB values 0-255
2. Check saturation is set correctly (1-100)
3. Try setting mode to "colour" explicitly first
4. Wait 0.3 seconds after mode switch

### Group Control Issues

**Problem:** Not all lights in group respond
**Solutions:**
1. Check all lights are online
2. Verify light IDs in group are correct
3. Check network connectivity for each light
4. Try controlling lights individually first

## Performance Considerations

### Connection Persistence

The integration uses persistent socket connections to reduce latency. Connections are maintained until explicitly closed or network issues occur.

### Command Timing

When switching between white and color modes, a 0.3-second delay is required for the bulb to process the mode change before accepting color/temperature commands.

### Network Load

Each command sends a small TCP packet (~100 bytes). For groups, commands are sent sequentially to each light, so larger groups may take slightly longer to respond.

## Security

### Local Key Protection

The local key is an encryption key that should be kept secure:
- Stored in MongoDB with user authentication
- Never exposed in API responses
- Required for all communication with bulbs

### Network Security

- All communication is on local network only
- No cloud dependency after initial setup
- AES encryption for all commands
- Consider using VLANs to isolate IoT devices

## Future Enhancements

Potential improvements for future versions:

1. **Auto-discovery:** Automatic bulb discovery on network
2. **Scenes:** Predefined color/brightness scenes
3. **Schedules:** Time-based automation
4. **Transitions:** Smooth color/brightness transitions
5. **Sync:** Synchronize multiple lights for effects
6. **Backup:** Export/import light configurations

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your bulb model is compatible (Ledvance Smart+ WiFi)
3. Ensure TinyTuya library is up to date
4. Check GitHub issues for similar problems

## References

- **TinyTuya Library:** https://github.com/jasonacox/tinytuya
- **Tuya Protocol:** https://github.com/tuya/tuya-iotos-embeded-sdk-wifi-ble-bk7231n
- **Ledvance Products:** https://www.ledvance.com/smart-home
- **Original Script:** https://github.com/adm1nsys/Ledvence-Smart-WiFi-E27-A60-Local-Control
