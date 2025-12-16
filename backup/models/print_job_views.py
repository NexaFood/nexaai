"""
Print Job Views

Handles sending CAD models to physical printers via PrusaLink and Snapmaker APIs.
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from models.views import session_login_required
from models.mongodb import db, to_object_id, doc_to_dict
from models.schemas import PrintJobSchema, PrinterSchema
from services.prusalink_client import PrusaLinkClient
from services.snapmaker_client import SnapmakerClient
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def get_printer_client(printer):
    """
    Get the appropriate API client for a printer.
    
    Args:
        printer: Printer document from MongoDB
        
    Returns:
        PrusaLinkClient or SnapmakerClient instance
    """
    if not printer.get('ip_address'):
        raise ValueError("Printer has no IP address configured")
    
    if not printer.get('api_key'):
        raise ValueError("Printer has no API key configured")
    
    if printer['printer_type'] == 'prusa':
        return PrusaLinkClient(
            ip_address=printer['ip_address'],
            api_key=printer['api_key']
        )
    elif printer['printer_type'] == 'snapmaker':
        return SnapmakerClient(
            ip_address=printer['ip_address'],
            token=printer['api_key']
        )
    else:
        raise ValueError(f"Unknown printer type: {printer['printer_type']}")


@session_login_required
@require_http_methods(["POST"])
def api_send_to_printer(request, project_id, part_number):
    """
    Send a generated CAD part to a printer.
    
    POST /api/design/send-to-printer/<project_id>/<part_number>/
    Body: printer_id=<printer_id>
    
    Returns:
        HTML with success/error message
    """
    try:
        # Get the design project
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return HttpResponse('Project not found', status=404)
        
        # Get the part
        part_number = int(part_number)
        parts = project.get('parts', [])
        
        if part_number < 1 or part_number > len(parts):
            return HttpResponse('Part not found', status=404)
        
        part = parts[part_number - 1]
        
        # Check if part has STL file
        if not part.get('stl_file_path'):
            return HttpResponse('''
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    ❌ This part has no STL file. Generate the CAD model first.
                </div>
            ''')
        
        # Get printer
        printer_id = request.POST.get('printer_id')
        if not printer_id:
            return HttpResponse('No printer selected', status=400)
        
        printer = db.printers.find_one({
            '_id': to_object_id(printer_id),
            'user_id': str(request.user.id)
        })
        
        if not printer:
            return HttpResponse('Printer not found', status=404)
        
        # Check if printer can print 3D
        if not PrinterSchema.can_print_3d(printer):
            return HttpResponse('''
                <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
                    ⚠️ This printer is not in 3D printing mode.
                </div>
            ''')
        
        # Get printer client
        try:
            client = get_printer_client(printer)
        except ValueError as e:
            return HttpResponse(f'''
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    ❌ Printer configuration error: {str(e)}
                </div>
            ''')
        
        # Send file to printer
        stl_file_path = part['stl_file_path']
        filename = f"{part['name']}.stl"
        
        logger.info(f"Sending {filename} to printer {printer['name']}...")
        
        result = client.upload_and_print(stl_file_path, filename)
        
        if result['success']:
            # Create print job record
            job_doc = PrintJobSchema.create(
                user_id=str(request.user.id),
                model_id=None,  # Not from old 3D model system
                printer_id=printer['_id'],
                status='printing',
                notes=f"Part {part_number}: {part['name']} from project {project['name']}"
            )
            db.print_jobs.insert_one(job_doc)
            
            # Update printer status
            db.printers.update_one(
                {'_id': printer['_id']},
                {'$set': {'status': 'printing'}}
            )
            
            return HttpResponse(f'''
                <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
                    ✅ Successfully sent to {printer['name']}!
                    <br><small>File: {filename}</small>
                </div>
            ''')
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Failed to send to printer: {error_msg}")
            
            return HttpResponse(f'''
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    ❌ Failed to send to printer: {error_msg}
                </div>
            ''')
    
    except Exception as e:
        logger.error(f"Error sending to printer: {e}", exc_info=True)
        return HttpResponse(f'''
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                ❌ Error: {str(e)}
            </div>
        ''', status=500)


@session_login_required
@require_http_methods(["GET"])
def api_get_printer_status(request, printer_id):
    """
    Get real-time status from a printer.
    
    GET /api/printers/<printer_id>/status
    
    Returns:
        JSON with printer status
    """
    try:
        printer = db.printers.find_one({
            '_id': to_object_id(printer_id),
            'user_id': str(request.user.id)
        })
        
        if not printer:
            return JsonResponse({'error': 'Printer not found'}, status=404)
        
        # Get printer client
        try:
            client = get_printer_client(printer)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get status from printer
        status = client.get_status()
        
        # Update printer status in database
        if status.get('state') != 'offline':
            db.printers.update_one(
                {'_id': printer['_id']},
                {'$set': {
                    'status': status['state'],
                    'last_online': datetime.utcnow()
                }}
            )
        
        return JsonResponse(status)
    
    except Exception as e:
        logger.error(f"Error getting printer status: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
