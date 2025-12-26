"""
3D Printer Dashboard API Views
Mock data for Prusa and Snapmaker printers
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta

# Mock data for printers
MOCK_PRINTERS = {
    'prusa_mk3s': {
        'id': 'prusa_mk3s',
        'name': 'Prusa i3 MK3S',
        'type': 'prusa',
        'status': 'ready',
        'state': 'operational',
        'nozzle_temp': 25,
        'nozzle_target': 0,
        'bed_temp': 23,
        'bed_target': 0,
        'progress': 0,
        'printing_time': 0,
        'printing_time_left': 0,
        'current_file': None,
        'last_updated': datetime.now().isoformat()
    },
    'snapmaker_2': {
        'id': 'snapmaker_2',
        'name': 'Snapmaker 2.0 A350',
        'type': 'snapmaker',
        'status': 'ready',
        'state': 'operational',
        'nozzle_temp': 24,
        'nozzle_target': 0,
        'bed_temp': 22,
        'bed_target': 0,
        'progress': 0,
        'printing_time': 0,
        'printing_time_left': 0,
        'current_file': None,
        'last_updated': datetime.now().isoformat()
    }
}

# Mock print job
MOCK_PRINT_JOB = {
    'printer_id': 'prusa_mk3s',
    'file_name': 'gear_housing.gcode',
    'progress': 47,
    'time_elapsed': 8100,  # seconds (2h 15m)
    'time_remaining': 8100,  # seconds (2h 15m)
    'started_at': (datetime.now() - timedelta(hours=2, minutes=15)).isoformat(),
    'estimated_completion': (datetime.now() + timedelta(hours=2, minutes=15)).isoformat()
}


@login_required
@require_http_methods(["GET"])
def api_get_printers(request):
    """Get all printers status"""
    return JsonResponse({
        'success': True,
        'printers': list(MOCK_PRINTERS.values())
    })


@login_required
@require_http_methods(["GET"])
def api_get_printer_status(request, printer_id):
    """Get specific printer status"""
    if printer_id in MOCK_PRINTERS:
        return JsonResponse({
            'success': True,
            'printer': MOCK_PRINTERS[printer_id]
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Printer not found'
        }, status=404)


@login_required
@require_http_methods(["GET"])
def api_get_print_job(request):
    """Get current print job status"""
    return JsonResponse({
        'success': True,
        'print_job': MOCK_PRINT_JOB
    })


@login_required
@require_http_methods(["POST"])
def api_start_print(request, printer_id):
    """Start a print job"""
    try:
        data = json.loads(request.body)
        file_name = data.get('file_name')
        
        if printer_id not in MOCK_PRINTERS:
            return JsonResponse({
                'success': False,
                'error': 'Printer not found'
            }, status=404)
        
        # Update printer status
        MOCK_PRINTERS[printer_id]['status'] = 'printing'
        MOCK_PRINTERS[printer_id]['state'] = 'printing'
        MOCK_PRINTERS[printer_id]['current_file'] = file_name
        MOCK_PRINTERS[printer_id]['nozzle_target'] = 210
        MOCK_PRINTERS[printer_id]['bed_target'] = 60
        
        # Update print job
        MOCK_PRINT_JOB['printer_id'] = printer_id
        MOCK_PRINT_JOB['file_name'] = file_name
        MOCK_PRINT_JOB['progress'] = 0
        MOCK_PRINT_JOB['started_at'] = datetime.now().isoformat()
        
        return JsonResponse({
            'success': True,
            'printer': MOCK_PRINTERS[printer_id],
            'print_job': MOCK_PRINT_JOB
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def api_pause_print(request, printer_id):
    """Pause current print job"""
    if printer_id not in MOCK_PRINTERS:
        return JsonResponse({
            'success': False,
            'error': 'Printer not found'
        }, status=404)
    
    MOCK_PRINTERS[printer_id]['status'] = 'paused'
    MOCK_PRINTERS[printer_id]['state'] = 'paused'
    
    return JsonResponse({
        'success': True,
        'printer': MOCK_PRINTERS[printer_id]
    })


@login_required
@require_http_methods(["POST"])
def api_resume_print(request, printer_id):
    """Resume paused print job"""
    if printer_id not in MOCK_PRINTERS:
        return JsonResponse({
            'success': False,
            'error': 'Printer not found'
        }, status=404)
    
    MOCK_PRINTERS[printer_id]['status'] = 'printing'
    MOCK_PRINTERS[printer_id]['state'] = 'printing'
    
    return JsonResponse({
        'success': True,
        'printer': MOCK_PRINTERS[printer_id]
    })


@login_required
@require_http_methods(["POST"])
def api_cancel_print(request, printer_id):
    """Cancel current print job"""
    if printer_id not in MOCK_PRINTERS:
        return JsonResponse({
            'success': False,
            'error': 'Printer not found'
        }, status=404)
    
    MOCK_PRINTERS[printer_id]['status'] = 'ready'
    MOCK_PRINTERS[printer_id]['state'] = 'operational'
    MOCK_PRINTERS[printer_id]['current_file'] = None
    MOCK_PRINTERS[printer_id]['nozzle_target'] = 0
    MOCK_PRINTERS[printer_id]['bed_target'] = 0
    MOCK_PRINTERS[printer_id]['progress'] = 0
    
    return JsonResponse({
        'success': True,
        'printer': MOCK_PRINTERS[printer_id]
    })


@login_required
@require_http_methods(["POST"])
def api_set_temperature(request, printer_id):
    """Set printer temperatures"""
    try:
        data = json.loads(request.body)
        
        if printer_id not in MOCK_PRINTERS:
            return JsonResponse({
                'success': False,
                'error': 'Printer not found'
            }, status=404)
        
        if 'nozzle_target' in data:
            MOCK_PRINTERS[printer_id]['nozzle_target'] = data['nozzle_target']
        if 'bed_target' in data:
            MOCK_PRINTERS[printer_id]['bed_target'] = data['bed_target']
        
        return JsonResponse({
            'success': True,
            'printer': MOCK_PRINTERS[printer_id]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def api_get_printer_files(request, printer_id):
    """Get files available on printer"""
    if printer_id not in MOCK_PRINTERS:
        return JsonResponse({
            'success': False,
            'error': 'Printer not found'
        }, status=404)
    
    # Mock file list
    files = [
        {'name': 'gear_housing.gcode', 'size': 2456789, 'date': '2024-01-15'},
        {'name': 'bracket_v2.gcode', 'size': 1234567, 'date': '2024-01-14'},
        {'name': 'enclosure_top.gcode', 'size': 3456789, 'date': '2024-01-13'},
    ]
    
    return JsonResponse({
        'success': True,
        'files': files
    })
