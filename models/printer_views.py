"""
Printer Views
Handles printer management, status, and print job control
Uses MongoDB for printer storage and real API integration
"""

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
import json
import logging
from datetime import datetime

from .mongodb import db, to_object_id, doc_to_dict
from .printer_api_service import PrinterAPIFactory, PrusaLinkAPI, SnapmakerAPI, format_time

logger = logging.getLogger(__name__)


def get_printers_collection():
    """Get the printers collection from MongoDB"""
    return db.printers


def serialize_printer(printer: dict) -> dict:
    """Serialize a printer document for JSON response"""
    printer['id'] = str(printer['_id'])
    del printer['_id']
    
    # Add display values
    printer['printer_type_display'] = {
        'prusa': 'Prusa (3D Print)',
        'snapmaker': 'Snapmaker (Multi-Mode)'
    }.get(printer.get('printer_type', ''), printer.get('printer_type', ''))
    
    printer['status_display'] = {
        'idle': 'Idle',
        'printing': 'Printing',
        'paused': 'Paused',
        'offline': 'Offline',
        'error': 'Error'
    }.get(printer.get('status', 'offline'), 'Unknown')
    
    # Format time displays
    if printer.get('time_remaining'):
        printer['time_remaining_display'] = format_time(printer['time_remaining'])
    if printer.get('time_elapsed'):
        printer['time_elapsed_display'] = format_time(printer['time_elapsed'])
    
    return printer


# ==================== Page Views ====================

@login_required
def printers_page(request):
    """Render the printers management page"""
    return render(request, 'printers.html')


@login_required
def add_printer_page(request):
    """Render the add printer form"""
    if request.method == 'POST':
        return save_printer(request)
    return render(request, 'printer_form.html', {'printer': None})


@login_required
def edit_printer_page(request, printer_id):
    """Render the edit printer form"""
    collection = get_printers_collection()
    printer = collection.find_one({
        '_id': ObjectId(printer_id),
        'user_id': str(request.user.id)
    })
    
    if not printer:
        return redirect('/printers')
    
    if request.method == 'POST':
        return save_printer(request, printer_id)
    
    printer = serialize_printer(printer)
    return render(request, 'printer_form.html', {'printer': printer})


def save_printer(request, printer_id=None):
    """Save a new or existing printer"""
    collection = get_printers_collection()
    
    printer_data = {
        'user_id': str(request.user.id),
        'name': request.POST.get('name'),
        'printer_type': request.POST.get('printer_type'),
        'model': request.POST.get('model'),
        'serial_number': request.POST.get('serial_number', ''),
        'ip_address': request.POST.get('ip_address', ''),
        'api_key': request.POST.get('api_key', ''),
        'build_volume_x': int(request.POST.get('build_volume_x', 0)),
        'build_volume_y': int(request.POST.get('build_volume_y', 0)),
        'build_volume_z': int(request.POST.get('build_volume_z', 0)),
        'status': request.POST.get('status', 'offline'),
        'current_mode': request.POST.get('current_mode', '3d_print'),
        'updated_at': datetime.utcnow()
    }
    
    if printer_id:
        # Update existing
        collection.update_one(
            {'_id': ObjectId(printer_id), 'user_id': str(request.user.id)},
            {'$set': printer_data}
        )
    else:
        # Create new
        printer_data['created_at'] = datetime.utcnow()
        collection.insert_one(printer_data)
    
    return redirect('/printers')


# ==================== API Views ====================

@login_required
@require_http_methods(["GET"])
def api_get_printers(request):
    """Get all printers for the current user with live status"""
    collection = get_printers_collection()
    printers = list(collection.find({'user_id': str(request.user.id)}))
    
    # Update status from real printers
    for printer in printers:
        printer = serialize_printer(printer)
        
        # Try to get live status if IP is configured
        if printer.get('ip_address') and printer.get('api_key'):
            try:
                api = PrinterAPIFactory.create(
                    printer['printer_type'],
                    printer['ip_address'],
                    printer['api_key']
                )
                status = api.get_status()
                
                if status.online:
                    printer['status'] = status.status
                    printer['nozzle_temp'] = status.nozzle_temp
                    printer['nozzle_target'] = status.nozzle_target
                    printer['bed_temp'] = status.bed_temp
                    printer['bed_target'] = status.bed_target
                    printer['progress'] = status.progress
                    printer['time_remaining'] = status.time_remaining
                    printer['time_elapsed'] = status.time_elapsed
                    printer['current_file'] = status.current_file
                    printer['job_id'] = status.job_id
                    
                    # Update display values
                    printer['status_display'] = {
                        'idle': 'Idle',
                        'printing': 'Printing',
                        'paused': 'Paused',
                        'offline': 'Offline',
                        'error': 'Error'
                    }.get(status.status, 'Unknown')
                    
                    if status.time_remaining:
                        printer['time_remaining_display'] = format_time(status.time_remaining)
                    if status.time_elapsed:
                        printer['time_elapsed_display'] = format_time(status.time_elapsed)
            except Exception as e:
                logger.error(f"Error getting printer status: {e}")
    
    # Return HTML partial for HTMX or JSON for API
    if 'HX-Request' in request.headers:
        if not printers:
            return render(request, 'partials/empty_printers.html')
        return render(request, 'partials/printers_grid.html', {'printers': printers})
    
    return JsonResponse({
        'success': True,
        'printers': printers
    })


@login_required
@require_http_methods(["GET", "DELETE"])
def api_printer_detail(request, printer_id):
    """Get or delete a specific printer"""
    collection = get_printers_collection()
    
    if request.method == 'DELETE':
        result = collection.delete_one({
            '_id': ObjectId(printer_id),
            'user_id': str(request.user.id)
        })
        
        if result.deleted_count:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Printer not found'}, status=404)
    
    # GET request
    printer = collection.find_one({
        '_id': ObjectId(printer_id),
        'user_id': str(request.user.id)
    })
    
    if not printer:
        return JsonResponse({'success': False, 'error': 'Printer not found'}, status=404)
    
    printer = serialize_printer(printer)
    
    # Get live status
    if printer.get('ip_address') and printer.get('api_key'):
        try:
            api = PrinterAPIFactory.create(
                printer['printer_type'],
                printer['ip_address'],
                printer['api_key']
            )
            status = api.get_status()
            
            if status.online:
                printer['status'] = status.status
                printer['nozzle_temp'] = status.nozzle_temp
                printer['nozzle_target'] = status.nozzle_target
                printer['bed_temp'] = status.bed_temp
                printer['bed_target'] = status.bed_target
                printer['progress'] = status.progress
                printer['time_remaining'] = status.time_remaining
                printer['time_elapsed'] = status.time_elapsed
                printer['current_file'] = status.current_file
                printer['job_id'] = status.job_id
        except Exception as e:
            logger.error(f"Error getting printer status: {e}")
    
    return JsonResponse({
        'success': True,
        'printer': printer
    })


@login_required
@require_http_methods(["POST"])
def api_upload_file(request, printer_id):
    """Upload a file to a printer and optionally start printing"""
    collection = get_printers_collection()
    printer = collection.find_one({
        '_id': ObjectId(printer_id),
        'user_id': str(request.user.id)
    })
    
    if not printer:
        return JsonResponse({'success': False, 'error': 'Printer not found'}, status=404)
    
    if not printer.get('ip_address') or not printer.get('api_key'):
        return JsonResponse({'success': False, 'error': 'Printer not configured for remote access'}, status=400)
    
    # Get uploaded file
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
    
    print_after_upload = request.POST.get('print_after_upload') == 'true'
    
    try:
        api = PrinterAPIFactory.create(
            printer['printer_type'],
            printer['ip_address'],
            printer['api_key']
        )
        
        file_data = uploaded_file.read()
        filename = uploaded_file.name
        
        if isinstance(api, PrusaLinkAPI):
            # Upload to Prusa
            success = api.upload_file(
                f'/{filename}',
                file_data,
                storage='local',
                print_after_upload=print_after_upload
            )
        elif isinstance(api, SnapmakerAPI):
            # Connect first for Snapmaker
            if not api.connect():
                return JsonResponse({'success': False, 'error': 'Failed to connect to Snapmaker'}, status=500)
            
            success = api.upload_file(filename, file_data)
            
            if success and print_after_upload:
                api.start_print(filename)
        else:
            return JsonResponse({'success': False, 'error': 'Unknown printer type'}, status=400)
        
        if success:
            return JsonResponse({'success': True, 'message': 'File uploaded successfully'})
        else:
            return JsonResponse({'success': False, 'error': 'Upload failed'}, status=500)
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_pause_print(request, printer_id):
    """Pause the current print job"""
    return control_print(request, printer_id, 'pause')


@login_required
@require_http_methods(["POST"])
def api_resume_print(request, printer_id):
    """Resume a paused print job"""
    return control_print(request, printer_id, 'resume')


@login_required
@require_http_methods(["POST"])
def api_cancel_print(request, printer_id):
    """Cancel the current print job"""
    return control_print(request, printer_id, 'cancel')


def control_print(request, printer_id, action):
    """Generic print control function"""
    collection = get_printers_collection()
    printer = collection.find_one({
        '_id': ObjectId(printer_id),
        'user_id': str(request.user.id)
    })
    
    if not printer:
        return JsonResponse({'success': False, 'error': 'Printer not found'}, status=404)
    
    if not printer.get('ip_address') or not printer.get('api_key'):
        return JsonResponse({'success': False, 'error': 'Printer not configured for remote access'}, status=400)
    
    try:
        api = PrinterAPIFactory.create(
            printer['printer_type'],
            printer['ip_address'],
            printer['api_key']
        )
        
        if isinstance(api, PrusaLinkAPI):
            # Get current job ID for Prusa
            status = api.get_status()
            if not status.job_id:
                return JsonResponse({'success': False, 'error': 'No active print job'}, status=400)
            
            if action == 'pause':
                success = api.pause_job(status.job_id)
            elif action == 'resume':
                success = api.resume_job(status.job_id)
            elif action == 'cancel':
                success = api.cancel_job(status.job_id)
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        elif isinstance(api, SnapmakerAPI):
            if not api.connect():
                return JsonResponse({'success': False, 'error': 'Failed to connect to Snapmaker'}, status=500)
            
            if action == 'pause':
                success = api.pause_print()
            elif action == 'resume':
                success = api.resume_print()
            elif action == 'cancel':
                success = api.cancel_print()
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Unknown printer type'}, status=400)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': f'Failed to {action} print'}, status=500)
    
    except Exception as e:
        logger.error(f"Print control error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_set_mode(request, printer_id):
    """Set Snapmaker mode (3D print, CNC, laser)"""
    collection = get_printers_collection()
    printer = collection.find_one({
        '_id': ObjectId(printer_id),
        'user_id': str(request.user.id)
    })
    
    if not printer:
        return JsonResponse({'success': False, 'error': 'Printer not found'}, status=404)
    
    if printer.get('printer_type') != 'snapmaker':
        return JsonResponse({'success': False, 'error': 'Mode change only available for Snapmaker'}, status=400)
    
    try:
        data = json.loads(request.body)
        new_mode = data.get('mode')
        
        if new_mode not in ['3d_print', 'cnc', 'laser']:
            return JsonResponse({'success': False, 'error': 'Invalid mode'}, status=400)
        
        # Update in database
        collection.update_one(
            {'_id': ObjectId(printer_id)},
            {'$set': {'current_mode': new_mode, 'updated_at': datetime.utcnow()}}
        )
        
        return JsonResponse({'success': True, 'mode': new_mode})
    
    except Exception as e:
        logger.error(f"Mode change error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
