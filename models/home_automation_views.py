"""
Home Automation API Views
Mock data for lights, climate, and devices
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json

# Mock data storage (in production, this would be from your backend)
MOCK_LIGHTS = {
    'living_room': {'name': 'Living Room', 'state': True, 'brightness': 80},
    'kitchen': {'name': 'Kitchen', 'state': True, 'brightness': 100},
    'bedroom': {'name': 'Bedroom', 'state': False, 'brightness': 0},
    'office': {'name': 'Office', 'state': True, 'brightness': 60},
    'bathroom': {'name': 'Bathroom', 'state': False, 'brightness': 0},
}

MOCK_CLIMATE = {
    'temperature': 22,
    'humidity': 45,
    'target_temperature': 21,
    'mode': 'auto',
    'fan_speed': 'medium',
    'status': 'cooling'
}

MOCK_DEVICES = {
    'router': {'name': 'Router', 'status': 'online', 'type': 'network'},
    'nas': {'name': 'NAS', 'status': 'online', 'type': 'storage'},
    'camera': {'name': 'Camera', 'status': 'offline', 'type': 'security'},
    'speaker': {'name': 'Smart Speaker', 'status': 'online', 'type': 'audio'},
    'tv': {'name': 'Smart TV', 'status': 'online', 'type': 'entertainment'},
}


@login_required
@require_http_methods(["GET"])
def api_get_lights(request):
    """Get all lights status"""
    return JsonResponse({
        'success': True,
        'lights': MOCK_LIGHTS
    })


@login_required
@require_http_methods(["POST"])
def api_toggle_light(request, light_id):
    """Toggle a specific light"""
    try:
        data = json.loads(request.body)
        state = data.get('state')
        brightness = data.get('brightness')
        
        if light_id in MOCK_LIGHTS:
            if state is not None:
                MOCK_LIGHTS[light_id]['state'] = state
            if brightness is not None:
                MOCK_LIGHTS[light_id]['brightness'] = brightness
            
            return JsonResponse({
                'success': True,
                'light': MOCK_LIGHTS[light_id]
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Light not found'
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def api_get_climate(request):
    """Get climate status"""
    return JsonResponse({
        'success': True,
        'climate': MOCK_CLIMATE
    })


@login_required
@require_http_methods(["POST"])
def api_set_climate(request):
    """Set climate parameters"""
    try:
        data = json.loads(request.body)
        
        if 'target_temperature' in data:
            MOCK_CLIMATE['target_temperature'] = data['target_temperature']
        if 'mode' in data:
            MOCK_CLIMATE['mode'] = data['mode']
        if 'fan_speed' in data:
            MOCK_CLIMATE['fan_speed'] = data['fan_speed']
        
        return JsonResponse({
            'success': True,
            'climate': MOCK_CLIMATE
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def api_get_devices(request):
    """Get all devices status"""
    return JsonResponse({
        'success': True,
        'devices': MOCK_DEVICES
    })


@login_required
@require_http_methods(["POST"])
def api_toggle_device(request, device_id):
    """Toggle a specific device"""
    try:
        data = json.loads(request.body)
        status = data.get('status')
        
        if device_id in MOCK_DEVICES:
            if status:
                MOCK_DEVICES[device_id]['status'] = status
            
            return JsonResponse({
                'success': True,
                'device': MOCK_DEVICES[device_id]
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Device not found'
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
