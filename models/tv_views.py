"""
TV Management Views
Handles LG webOS TV control and management
"""
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .mongodb import db, to_object_id, doc_to_dict
from .tv_api_service import get_tv_service, LGTVService


@login_required
def tv_list(request):
    """Display list of TVs"""
    user_id = str(request.user.id)
    tvs = list(db.tvs.find({'user_id': user_id}))
    tvs = [doc_to_dict(tv) for tv in tvs]
    
    # Get current state for each TV
    for tv in tvs:
        try:
            service = get_tv_service(
                tv.get('ip_address'),
                tv.get('mac_address'),
                tv.get('client_key')
            )
            state = service.get_state()
            tv['state'] = state
        except:
            tv['state'] = {'power': 'unknown'}
    
    return render(request, 'tvs.html', {'tvs': tvs})


@login_required
def tv_add(request):
    """Add a new TV"""
    if request.method == 'POST':
        user_id = str(request.user.id)
        
        tv_data = {
            'user_id': user_id,
            'name': request.POST.get('name', 'LG TV'),
            'model': request.POST.get('model', ''),
            'ip_address': request.POST.get('ip_address'),
            'mac_address': request.POST.get('mac_address', ''),
            'client_key': '',  # Will be set after pairing
            'location': request.POST.get('location', ''),
            'linked_lights': [],  # Light IDs to sync with TV
            'auto_sync_enabled': request.POST.get('auto_sync_enabled') == 'on'
        }
        
        result = db.tvs.insert_one(tv_data)
        tv_id = str(result.inserted_id)
        
        # Redirect to pairing page
        return redirect('models:tv_pair', tv_id=tv_id)
    
    return render(request, 'tv_form.html', {'tv': None, 'action': 'add'})


@login_required
def tv_edit(request, tv_id):
    """Edit an existing TV"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return redirect('models:tv_list')
    
    if request.method == 'POST':
        update_data = {
            'name': request.POST.get('name', tv.get('name')),
            'model': request.POST.get('model', tv.get('model')),
            'ip_address': request.POST.get('ip_address', tv.get('ip_address')),
            'mac_address': request.POST.get('mac_address', tv.get('mac_address')),
            'location': request.POST.get('location', tv.get('location')),
            'auto_sync_enabled': request.POST.get('auto_sync_enabled') == 'on'
        }
        
        db.tvs.update_one(
            {'_id': to_object_id(tv_id)},
            {'$set': update_data}
        )
        
        return redirect('models:tv_list')
    
    tv = doc_to_dict(tv)
    return render(request, 'tv_form.html', {'tv': tv, 'action': 'edit'})


@login_required
def tv_delete(request, tv_id):
    """Delete a TV"""
    user_id = str(request.user.id)
    db.tvs.delete_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    return redirect('models:tv_list')


@login_required
def tv_pair(request, tv_id):
    """Pair with a TV (shows prompt on TV)"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return redirect('models:tv_list')
    
    tv = doc_to_dict(tv)
    return render(request, 'tv_pair.html', {'tv': tv})


@login_required
@require_http_methods(['POST'])
def tv_pair_connect(request, tv_id):
    """API endpoint to initiate pairing"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        service = get_tv_service(
            tv.get('ip_address'),
            tv.get('mac_address'),
            tv.get('client_key')
        )
        
        result = service.connect(timeout=10)
        
        if result.get('success') and result.get('client_key'):
            # Save the client key
            db.tvs.update_one(
                {'_id': to_object_id(tv_id)},
                {'$set': {'client_key': result['client_key']}}
            )
            
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def tv_api_state(request, tv_id):
    """Get current TV state"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        service = get_tv_service(
            tv.get('ip_address'),
            tv.get('mac_address'),
            tv.get('client_key')
        )
        
        state = service.get_state()
        return JsonResponse({'success': True, 'state': state})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def tv_api_power(request, tv_id):
    """Control TV power"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        data = json.loads(request.body) if request.body else {}
        action = data.get('action', 'toggle')
        
        service = get_tv_service(
            tv.get('ip_address'),
            tv.get('mac_address'),
            tv.get('client_key')
        )
        
        new_power_state = None
        
        if action == 'on':
            result = service.power_on()
            new_power_state = 'on'
        elif action == 'off':
            result = service.power_off()
            new_power_state = 'off'
        else:
            # Toggle
            state = service.get_state()
            if state.get('power') == 'on':
                result = service.power_off()
                new_power_state = 'off'
            else:
                result = service.power_on()
                new_power_state = 'on'
        
        # Trigger light sync if enabled
        if result.get('success') and tv.get('auto_sync_enabled') and new_power_state:
            print(f"TV power changed to {new_power_state}, syncing lights...")
            _sync_lights_with_tv(tv, new_power_state)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def tv_api_volume(request, tv_id):
    """Control TV volume"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        data = json.loads(request.body) if request.body else {}
        
        service = get_tv_service(
            tv.get('ip_address'),
            tv.get('mac_address'),
            tv.get('client_key')
        )
        
        # Connect if needed
        if not service._connected:
            service.connect()
        
        if 'volume' in data:
            result = service.set_volume(int(data['volume']))
        elif 'mute' in data:
            result = service.mute(data['mute'])
        else:
            return JsonResponse({'success': False, 'error': 'No volume or mute parameter'})
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def tv_api_apps(request, tv_id):
    """Get list of TV apps"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        service = get_tv_service(
            tv.get('ip_address'),
            tv.get('mac_address'),
            tv.get('client_key')
        )
        
        # Connect if needed
        if not service._connected:
            service.connect()
        
        apps = service.get_apps()
        # Convert to serializable format
        app_list = []
        for app in apps:
            app_list.append({
                'id': app.get('id'),
                'title': app.get('title'),
                'icon': app.get('icon')
            })
        
        return JsonResponse({'success': True, 'apps': app_list})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def tv_api_launch_app(request, tv_id):
    """Launch an app on the TV"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        data = json.loads(request.body) if request.body else {}
        app_id = data.get('app_id')
        
        if not app_id:
            return JsonResponse({'success': False, 'error': 'No app_id provided'})
        
        service = get_tv_service(
            tv.get('ip_address'),
            tv.get('mac_address'),
            tv.get('client_key')
        )
        
        # Connect if needed
        if not service._connected:
            service.connect()
        
        result = service.launch_app(app_id)
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def tv_toggle_sync(request, tv_id):
    """Toggle auto-sync setting for a TV"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        data = json.loads(request.body) if request.body else {}
        enabled = data.get('enabled', False)
        
        db.tvs.update_one(
            {'_id': to_object_id(tv_id)},
            {'$set': {'auto_sync_enabled': enabled}}
        )
        
        return JsonResponse({'success': True, 'auto_sync_enabled': enabled})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def tv_link_lights(request, tv_id):
    """Link lights to sync with TV state"""
    user_id = str(request.user.id)
    tv = db.tvs.find_one({'_id': to_object_id(tv_id), 'user_id': user_id})
    
    if not tv:
        return JsonResponse({'success': False, 'error': 'TV not found'})
    
    try:
        data = json.loads(request.body) if request.body else {}
        light_ids = data.get('light_ids', [])
        
        db.tvs.update_one(
            {'_id': to_object_id(tv_id)},
            {'$set': {'linked_lights': light_ids}}
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def _sync_lights_with_tv(tv: dict, power_state: str):
    """
    Sync linked lights with TV power state
    
    Args:
        tv: TV document from database
        power_state: 'on' or 'off'
    """
    from .ledvance_controller import LedvanceLight
    
    linked_lights = tv.get('linked_lights', [])
    print(f"Syncing {len(linked_lights)} lights with TV state: {power_state}")
    
    for light_id in linked_lights:
        try:
            # Get light from database - try ledvance_lights collection
            light = db.ledvance_lights.find_one({'_id': to_object_id(light_id)})
            if not light:
                # Also try by dev_id
                light = db.ledvance_lights.find_one({'dev_id': light_id})
            
            if light:
                print(f"Found light: {light.get('name')} at {light.get('ip')}")
                # Create controller and turn on/off
                controller = LedvanceLight(
                    dev_id=light['dev_id'],
                    ip=light['ip'],
                    local_key=light['local_key'],
                    name=light.get('name', light['dev_id']),
                    version=light.get('version', 3.3)
                )
                
                if power_state == 'on':
                    result = controller.turn_on()
                    print(f"Turn on {light.get('name')}: {result}")
                else:
                    result = controller.turn_off()
                    print(f"Turn off {light.get('name')}: {result}")
            else:
                print(f"Light not found: {light_id}")
        except Exception as e:
            print(f"Error syncing light {light_id}: {e}")


# Background task to poll TV state and sync lights
_polling_tasks = {}

def start_tv_polling(tv_id: str, interval: int = 10):
    """Start polling a TV's state"""
    if tv_id in _polling_tasks:
        return  # Already polling
    
    tv = db.tvs.find_one({'_id': to_object_id(tv_id)})
    if not tv:
        return
    
    service = get_tv_service(
        tv.get('ip_address'),
        tv.get('mac_address'),
        tv.get('client_key')
    )
    
    last_power_state = [None]  # Use list to allow modification in closure
    
    def on_state_change(state):
        power = state.get('power')
        if power != last_power_state[0] and last_power_state[0] is not None:
            # Power state changed, sync lights
            if tv.get('auto_sync_enabled'):
                _sync_lights_with_tv(tv, power)
        last_power_state[0] = power
    
    service.start_state_polling(on_state_change, interval)
    _polling_tasks[tv_id] = service


def stop_tv_polling(tv_id: str):
    """Stop polling a TV's state"""
    if tv_id in _polling_tasks:
        _polling_tasks[tv_id].stop_state_polling()
        del _polling_tasks[tv_id]
