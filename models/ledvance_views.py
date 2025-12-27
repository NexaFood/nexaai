"""
Ledvance Smart Light API Views
Handles light control, groups, and device management
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from models.mongodb import db
from models.views import session_login_required
from models.ledvance_controller import LedvanceLight, LightGroup, LightManager
from datetime import datetime
from bson import ObjectId
import json


# Global light manager instance
light_manager = LightManager()


def _load_user_lights(user_id: str):
    """Load all lights for a user from database"""
    lights = list(db.ledvance_lights.find({'user_id': user_id}))
    
    # Clear existing lights for this user
    for light in light_manager.get_all_lights():
        if hasattr(light, 'user_id') and light.user_id == user_id:
            light_manager.remove_light(light.dev_id)
    
    # Add lights from database
    for light_data in lights:
        try:
            light = LedvanceLight(
                dev_id=light_data['dev_id'],
                ip=light_data['ip'],
                local_key=light_data['local_key'],
                name=light_data.get('name', light_data['dev_id']),
                version=light_data.get('version', 3.3)
            )
            light.user_id = user_id
            light.light_id = str(light_data['_id'])
            light.room = light_data.get('room', '')
            light_manager.add_light(light)
        except Exception as e:
            print(f"Failed to load light {light_data.get('name')}: {e}")


def _load_user_groups(user_id: str):
    """Load all groups for a user from database"""
    groups = list(db.ledvance_groups.find({'user_id': user_id}))
    
    # Clear existing groups for this user
    for group in light_manager.get_all_groups():
        if hasattr(group, 'user_id') and group.user_id == user_id:
            light_manager.remove_group(group.group_id)
    
    # Add groups from database
    for group_data in groups:
        try:
            light_ids = group_data.get('light_ids', [])
            lights = [light_manager.get_light(lid) for lid in light_ids]
            lights = [l for l in lights if l and hasattr(l, 'user_id') and l.user_id == user_id]
            
            if lights:
                group = LightGroup(
                    group_id=str(group_data['_id']),
                    name=group_data['name'],
                    lights=lights
                )
                group.user_id = user_id
                group.room = group_data.get('room', '')
                light_manager.add_group(group)
        except Exception as e:
            print(f"Failed to load group {group_data.get('name')}: {e}")


@session_login_required
@require_http_methods(["GET"])
def api_list_lights(request):
    """Get all lights for the current user"""
    try:
        user_id = str(request.user.id)
        
        # Load lights from database
        _load_user_lights(user_id)
        
        # Get all lights for this user
        user_lights = [l for l in light_manager.get_all_lights() if hasattr(l, 'user_id') and l.user_id == user_id]
        
        lights_data = []
        for light in user_lights:
            status = light.get_status()
            lights_data.append({
                'id': light.light_id,
                'dev_id': light.dev_id,
                'name': light.name,
                'ip': light.ip,
                'room': getattr(light, 'room', ''),
                'online': status.get('online', False),
                'power': status.get('power', False),
                'mode': status.get('mode', 'unknown'),
                'brightness': status.get('brightness', 0),
                'color_temp_kelvin': status.get('color_temp_kelvin', 0),
                'color_hsv': status.get('color_hsv', '')
            })
        
        return JsonResponse({
            'success': True,
            'lights': lights_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_add_light(request):
    """Add a new light"""
    try:
        user_id = str(request.user.id)
        
        # Get form data
        name = request.POST.get('name', '').strip()
        dev_id = request.POST.get('dev_id', '').strip()
        ip = request.POST.get('ip', '').strip()
        local_key = request.POST.get('local_key', '').strip()
        room = request.POST.get('room', '').strip()
        version = float(request.POST.get('version', '3.3'))
        skip_test = request.POST.get('skip_test', 'false').lower() == 'true'
        
        if not all([name, dev_id, ip, local_key]):
            return JsonResponse({
                'success': False,
                'error': 'Name, device ID, IP, and local key are required'
            }, status=400)
        
        # Test connection (unless skipped)
        if not skip_test:
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Testing connection to {dev_id} at {ip}")
                
                test_light = LedvanceLight(dev_id, ip, local_key, name, version)
                test_status = test_light.get_status()
                
                logger.info(f"Connection test result: {test_status}")
                
                if not test_status.get('online'):
                    error_msg = test_status.get('error', 'Device not responding')
                    logger.error(f"Connection test failed: {error_msg}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Could not connect to light: {error_msg}. Try enabling "Skip Connection Test" to add anyway.'
                    }, status=400)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Connection test exception: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': f'Connection test failed: {str(e)}. Try enabling "Skip Connection Test" to add anyway.'
                }, status=400)
        
        # Save to database
        light_data = {
            'user_id': user_id,
            'name': name,
            'dev_id': dev_id,
            'ip': ip,
            'local_key': local_key,
            'room': room,
            'version': version,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.ledvance_lights.insert_one(light_data)
        light_data['_id'] = result.inserted_id
        
        # Add to manager
        light = LedvanceLight(dev_id, ip, local_key, name, version)
        light.user_id = user_id
        light.light_id = str(result.inserted_id)
        light.room = room
        light_manager.add_light(light)
        
        return JsonResponse({
            'success': True,
            'light': {
                'id': str(result.inserted_id),
                'name': name,
                'dev_id': dev_id,
                'ip': ip,
                'room': room
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_remove_light(request, light_id):
    """Remove a light"""
    try:
        user_id = str(request.user.id)
        
        # Find light in database
        light_data = db.ledvance_lights.find_one({
            '_id': ObjectId(light_id),
            'user_id': user_id
        })
        
        if not light_data:
            return JsonResponse({
                'success': False,
                'error': 'Light not found'
            }, status=404)
        
        # Remove from database
        db.ledvance_lights.delete_one({'_id': ObjectId(light_id)})
        
        # Remove from manager
        light_manager.remove_light(light_data['dev_id'])
        
        # Remove from groups
        db.ledvance_groups.update_many(
            {'user_id': user_id},
            {'$pull': {'light_ids': light_data['dev_id']}}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Light removed successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_toggle_light(request, light_id):
    """Toggle a light on/off"""
    try:
        user_id = str(request.user.id)
        _load_user_lights(user_id)
        
        # Find light
        light = None
        for l in light_manager.get_all_lights():
            if hasattr(l, 'light_id') and l.light_id == light_id and l.user_id == user_id:
                light = l
                break
        
        if not light:
            return JsonResponse({
                'success': False,
                'error': 'Light not found'
            }, status=404)
        
        success = light.toggle()
        status = light.get_status()
        
        return JsonResponse({
            'success': success,
            'power': status.get('power', False)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_set_light_brightness(request, light_id):
    """Set light brightness"""
    try:
        user_id = str(request.user.id)
        _load_user_lights(user_id)
        
        brightness = int(request.POST.get('brightness', 50))
        
        # Find light
        light = None
        for l in light_manager.get_all_lights():
            if hasattr(l, 'light_id') and l.light_id == light_id and l.user_id == user_id:
                light = l
                break
        
        if not light:
            return JsonResponse({
                'success': False,
                'error': 'Light not found'
            }, status=404)
        
        success = light.set_brightness(brightness)
        
        return JsonResponse({
            'success': success,
            'brightness': brightness
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_set_light_color(request, light_id):
    """Set light RGB color"""
    try:
        user_id = str(request.user.id)
        _load_user_lights(user_id)
        
        r = int(request.POST.get('r', 255))
        g = int(request.POST.get('g', 255))
        b = int(request.POST.get('b', 255))
        saturation = int(request.POST.get('saturation', 100))
        
        # Find light
        light = None
        for l in light_manager.get_all_lights():
            if hasattr(l, 'light_id') and l.light_id == light_id and l.user_id == user_id:
                light = l
                break
        
        if not light:
            return JsonResponse({
                'success': False,
                'error': 'Light not found'
            }, status=404)
        
        success = light.set_rgb(r, g, b, saturation)
        
        return JsonResponse({
            'success': success,
            'color': {'r': r, 'g': g, 'b': b, 'saturation': saturation}
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_set_light_temperature(request, light_id):
    """Set light color temperature"""
    try:
        user_id = str(request.user.id)
        _load_user_lights(user_id)
        
        kelvin = int(request.POST.get('kelvin', 4000))
        
        # Find light
        light = None
        for l in light_manager.get_all_lights():
            if hasattr(l, 'light_id') and l.light_id == light_id and l.user_id == user_id:
                light = l
                break
        
        if not light:
            return JsonResponse({
                'success': False,
                'error': 'Light not found'
            }, status=404)
        
        success = light.set_color_temperature(kelvin)
        
        return JsonResponse({
            'success': success,
            'kelvin': kelvin
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Group endpoints

@session_login_required
@require_http_methods(["GET"])
def api_list_groups(request):
    """Get all light groups for the current user"""
    try:
        user_id = str(request.user.id)
        
        # Load lights and groups
        _load_user_lights(user_id)
        _load_user_groups(user_id)
        
        # Get all groups for this user
        user_groups = [g for g in light_manager.get_all_groups() if hasattr(g, 'user_id') and g.user_id == user_id]
        
        # Batch load all lights once to create dev_id -> MongoDB ID mapping
        all_lights = list(db.ledvance_lights.find({'user_id': user_id}))
        dev_id_to_mongo_id = {light['dev_id']: str(light['_id']) for light in all_lights}
        
        groups_data = []
        for group in user_groups:
            status = group.get_status()
            # Get light IDs (dev_ids) for this group
            light_dev_ids = [light.dev_id for light in group.lights]
            # Convert dev_ids to MongoDB IDs using the mapping (no DB queries!)
            light_mongo_ids = [dev_id_to_mongo_id.get(dev_id) for dev_id in light_dev_ids if dev_id in dev_id_to_mongo_id]
            
            groups_data.append({
                'id': group.group_id,
                'name': group.name,
                'room': getattr(group, 'room', ''),
                'light_count': status['total_lights'],  # Frontend expects light_count
                'light_ids': light_mongo_ids,  # MongoDB IDs for frontend checkboxes
                'total_lights': status['total_lights'],
                'online_lights': status['online_lights'],
                'lights_on': status['lights_on'],
                'all_on': status['all_on'],
                'any_on': status['any_on']
            })
        
        return JsonResponse({
            'success': True,
            'groups': groups_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_create_group(request):
    """Create a new light group"""
    try:
        user_id = str(request.user.id)
        
        name = request.POST.get('name', '').strip()
        room = request.POST.get('room', '').strip()
        light_ids = request.POST.get('light_ids', '').strip()
        
        if not name or not light_ids:
            return JsonResponse({
                'success': False,
                'error': 'Name and light IDs are required'
            }, status=400)
        
        # Parse light IDs (these are MongoDB document IDs from the form)
        try:
            light_ids = json.loads(light_ids) if isinstance(light_ids, str) else light_ids
        except:
            light_ids = light_ids.split(',') if isinstance(light_ids, str) else []
        
        # Convert MongoDB document IDs to device IDs (dev_id)
        dev_ids = []
        for light_id in light_ids:
            try:
                light_doc = db.ledvance_lights.find_one({
                    '_id': ObjectId(light_id),
                    'user_id': user_id
                })
                if light_doc:
                    dev_ids.append(light_doc['dev_id'])
            except Exception as e:
                print(f"Failed to convert light ID {light_id}: {e}")
        
        if not dev_ids:
            return JsonResponse({
                'success': False,
                'error': 'No valid lights found'
            }, status=400)
        
        # Save to database with device IDs
        group_data = {
            'user_id': user_id,
            'name': name,
            'room': room,
            'light_ids': dev_ids,  # Store device IDs, not MongoDB IDs
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.ledvance_groups.insert_one(group_data)
        
        # Load into manager
        _load_user_lights(user_id)
        _load_user_groups(user_id)
        
        return JsonResponse({
            'success': True,
            'group': {
                'id': str(result.inserted_id),
                'name': name,
                'room': room,
                'light_count': len(light_ids)
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_update_group(request, group_id):
    """Update an existing light group"""
    try:
        user_id = str(request.user.id)
        
        # Find group in database
        group_doc = db.ledvance_groups.find_one({
            '_id': ObjectId(group_id),
            'user_id': user_id
        })
        
        if not group_doc:
            return JsonResponse({
                'success': False,
                'error': 'Group not found'
            }, status=404)
        
        # Get updated data
        name = request.POST.get('name', '').strip()
        room = request.POST.get('room', '').strip()
        light_ids = request.POST.get('light_ids', '').strip()
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Name is required'
            }, status=400)
        
        # Parse and convert light IDs if provided
        if light_ids:
            try:
                light_ids = json.loads(light_ids) if isinstance(light_ids, str) else light_ids
            except:
                light_ids = light_ids.split(',') if isinstance(light_ids, str) else []
            
            # Convert MongoDB document IDs to device IDs
            dev_ids = []
            for light_id in light_ids:
                try:
                    light_doc = db.ledvance_lights.find_one({
                        '_id': ObjectId(light_id),
                        'user_id': user_id
                    })
                    if light_doc:
                        dev_ids.append(light_doc['dev_id'])
                except Exception as e:
                    print(f"Failed to convert light ID {light_id}: {e}")
            
            if not dev_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid lights selected'
                }, status=400)
        else:
            # Keep existing lights
            dev_ids = group_doc.get('light_ids', [])
        
        # Update in database
        db.ledvance_groups.update_one(
            {'_id': ObjectId(group_id)},
            {'$set': {
                'name': name,
                'room': room,
                'light_ids': dev_ids,
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Reload groups
        _load_user_lights(user_id)
        _load_user_groups(user_id)
        
        return JsonResponse({
            'success': True,
            'group': {
                'id': group_id,
                'name': name,
                'room': room,
                'light_count': len(dev_ids)
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_delete_group(request, group_id):
    """Delete a light group"""
    try:
        user_id = str(request.user.id)
        
        # Find and delete group from database
        result = db.ledvance_groups.delete_one({
            '_id': ObjectId(group_id),
            'user_id': user_id
        })
        
        if result.deleted_count == 0:
            return JsonResponse({
                'success': False,
                'error': 'Group not found'
            }, status=404)
        
        # Remove from manager
        light_manager.remove_group(group_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Group deleted successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_toggle_group(request, group_id):
    """Toggle all lights in a group"""
    try:
        user_id = str(request.user.id)
        _load_user_lights(user_id)
        _load_user_groups(user_id)
        
        # Find group
        group = None
        for g in light_manager.get_all_groups():
            if g.group_id == group_id and hasattr(g, 'user_id') and g.user_id == user_id:
                group = g
                break
        
        if not group:
            return JsonResponse({
                'success': False,
                'error': 'Group not found'
            }, status=404)
        
        results = group.toggle()
        status = group.get_status()
        
        return JsonResponse({
            'success': True,
            'results': results,
            'any_on': status['any_on']
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_set_group_brightness(request, group_id):
    """Set brightness for all lights in a group"""
    try:
        user_id = str(request.user.id)
        _load_user_lights(user_id)
        _load_user_groups(user_id)
        
        brightness = int(request.POST.get('brightness', 50))
        
        # Find group
        group = None
        for g in light_manager.get_all_groups():
            if g.group_id == group_id and hasattr(g, 'user_id') and g.user_id == user_id:
                group = g
                break
        
        if not group:
            return JsonResponse({
                'success': False,
                'error': 'Group not found'
            }, status=404)
        
        results = group.set_brightness(brightness)
        
        return JsonResponse({
            'success': True,
            'results': results,
            'brightness': brightness
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_set_group_color(request, group_id):
    """Set RGB color for all lights in a group"""
    try:
        user_id = str(request.user.id)
        _load_user_lights(user_id)
        _load_user_groups(user_id)
        
        r = int(request.POST.get('r', 255))
        g = int(request.POST.get('g', 255))
        b = int(request.POST.get('b', 255))
        saturation = int(request.POST.get('saturation', 100))
        
        # Find group
        group = None
        for grp in light_manager.get_all_groups():
            if grp.group_id == group_id and hasattr(grp, 'user_id') and grp.user_id == user_id:
                group = grp
                break
        
        if not group:
            return JsonResponse({
                'success': False,
                'error': 'Group not found'
            }, status=404)
        
        results = group.set_rgb(r, g, b, saturation)
        
        return JsonResponse({
            'success': True,
            'results': results,
            'color': {'r': r, 'g': g, 'b': b}
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



# Template view for lights management page

@session_login_required
def lights_management(request):
    """Render the lights management page"""
    from django.shortcuts import render
    return render(request, 'lights_management.html')



@session_login_required
@require_http_methods(["POST"])
def api_scan_network(request):
    """Scan local network for Tuya devices"""
    try:
        import tinytuya
        import socket
        
        # Get local network info
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Scan for devices (this may take 10-20 seconds)
        devices = tinytuya.deviceScan(False, 20)
        
        discovered = []
        for dev_id, device_info in devices.items():
            discovered.append({
                'dev_id': dev_id,
                'ip': device_info.get('ip', ''),
                'version': device_info.get('version', ''),
                'name': device_info.get('name', 'Unknown Device'),
                'product_key': device_info.get('product_key', '')
            })
        
        return JsonResponse({
            'success': True,
            'devices': discovered,
            'local_ip': local_ip,
            'count': len(discovered)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
