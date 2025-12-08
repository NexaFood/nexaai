"""
Django views for NexaAI using PyMongo for MongoDB operations.
Server-side rendering with HTMX for dynamic updates.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from bson import ObjectId
from datetime import datetime
import logging
import requests

from models.mongodb import db, to_object_id, doc_to_dict, docs_to_list
from models.schemas import (
    Model3DSchema, PrinterSchema, PrintJobSchema, GenerationJobSchema,
    get_display_name, PRINTER_TYPE_DISPLAY, PRINTER_STATUS_DISPLAY,
    SNAPMAKER_MODE_DISPLAY, MODEL_STATUS_DISPLAY
)
from services.meshy_client import MeshyClient
from services.prompt_refinement import refine_prompt_with_llm
from services.notifications import notify_owner

logger = logging.getLogger(__name__)


# ============================================================================
# BASIC VIEWS
# ============================================================================

def home(request):
    """Landing page."""
    return render(request, 'home.html')


# ============================================================================
# 3D MODEL GENERATION VIEWS
# ============================================================================

@login_required
def generate(request):
    """Model generation page."""
    return render(request, 'generate.html')


@login_required
def history(request):
    """Model history page."""
    return render(request, 'history.html')


@login_required
def viewer(request, model_id):
    """3D model viewer page."""
    model = db.models.find_one({'_id': to_object_id(model_id), 'user_id': str(request.user.id)})
    
    if not model:
        return HttpResponse('Model not found', status=404)
    
    model = doc_to_dict(model)
    return render(request, 'viewer.html', {'model': model})


# ============================================================================
# 3D MODEL HTMX API ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_generate(request):
    """
    HTMX endpoint to generate 3D model.
    Creates model and starts Meshy.ai generation job.
    """
    try:
        prompt = request.POST.get('prompt', '').strip()
        quality = request.POST.get('quality', 'preview')
        
        if not prompt:
            return HttpResponse('Prompt is required', status=400)
        
        # Map quality to polygon count
        quality_map = {
            'preview': 10000,
            'standard': 30000,
            'high': 60000,
            'ultra': 100000,
        }
        polygon_count = quality_map.get(quality, 30000)
        
        # Create model document
        model_doc = Model3DSchema.create(
            user_id=str(request.user.id),
            prompt=prompt,
            quality=quality,
            polygon_count=polygon_count,
            status='processing'
        )
        
        # Insert into MongoDB
        result = db.models.insert_one(model_doc)
        model_id = result.inserted_id
        
        # Start Meshy.ai generation
        try:
            meshy_client = MeshyClient()
            task_id = meshy_client.create_text_to_3d(prompt, polygon_count)
            
            # Create generation job
            job_doc = GenerationJobSchema.create(
                model_id=model_id,
                meshy_task_id=task_id,
                meshy_status='PENDING'
            )
            db.generation_jobs.insert_one(job_doc)
            
            logger.info(f"Started generation for model {model_id}, task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to start Meshy generation: {e}")
            db.models.update_one(
                {'_id': model_id},
                Model3DSchema.update({'status': 'failed', 'error_message': str(e)})
            )
            return HttpResponse(f'Failed to start generation: {e}', status=500)
        
        # Notify owner
        try:
            notify_owner(
                title="New 3D Model Generation Started",
                content=f"Prompt: {prompt}\nQuality: {quality}"
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
        
        return HttpResponse('Generation started! Check the History page to see progress.')
    
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return HttpResponse(f'Error: {e}', status=500)


@login_required
@require_http_methods(["POST"])
def api_refine_prompt(request):
    """
    HTMX endpoint to refine prompt using LLM.
    """
    try:
        prompt = request.POST.get('prompt', '').strip()
        
        if not prompt:
            return HttpResponse('Prompt is required', status=400)
        
        refined = refine_prompt_with_llm(prompt)
        return HttpResponse(refined)
    
    except Exception as e:
        logger.error(f"Prompt refinement failed: {e}")
        return HttpResponse(prompt, status=200)  # Return original on error


@login_required
@require_http_methods(["GET"])
def api_models_list(request):
    """
    HTMX endpoint to list user's 3D models.
    Returns HTML grid of model cards.
    """
    filter_status = request.GET.get('status', 'all')
    
    # Build query
    query = {'user_id': str(request.user.id)}
    if filter_status != 'all':
        query['status'] = filter_status
    
    # Fetch models
    models = list(db.models.find(query).sort('created_at', -1))
    
    if not models:
        return HttpResponse('''
            <div class="text-center py-12">
                <svg class="w-24 h-24 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                </svg>
                <h3 class="text-xl font-bold text-gray-700 mb-2">No Models Yet</h3>
                <p class="text-gray-500 mb-6">Generate your first 3D model to get started</p>
                <a href="/generate/" class="inline-block bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 transition">
                    Generate Your First Model
                </a>
            </div>
        ''')
    
    # Render model cards
    html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
    for model in models:
        model = doc_to_dict(model)
        # Add display names
        model['status_display'] = get_display_name(model['status'], MODEL_STATUS_DISPLAY)
        html += render_to_string('partials/model_card.html', {'model': model})
    html += '</div>'
    
    return HttpResponse(html)


@login_required
@require_http_methods(["GET"])
def api_model_status(request, model_id):
    """
    HTMX endpoint to check model generation status.
    Returns updated model card HTML.
    """
    model = db.models.find_one({'_id': to_object_id(model_id), 'user_id': str(request.user.id)})
    
    if not model:
        return HttpResponse('Model not found', status=404)
    
    # Check if still processing
    if model['status'] == 'processing':
        # Check Meshy.ai status
        job = db.generation_jobs.find_one({'model_id': model['_id']})
        if job:
            try:
                meshy_client = MeshyClient()
                status_data = meshy_client.get_task_status(job['meshy_task_id'])
                
                # Update job
                db.generation_jobs.update_one(
                    {'_id': job['_id']},
                    GenerationJobSchema.update({
                        'meshy_status': status_data.get('status'),
                        'meshy_response': status_data,
                        'progress': status_data.get('progress', 0),
                        'last_checked_at': datetime.utcnow()
                    })
                )
                
                # Update model if completed
                if status_data.get('status') == 'SUCCEEDED':
                    db.models.update_one(
                        {'_id': model['_id']},
                        Model3DSchema.update({
                            'status': 'completed',
                            'glb_url': status_data.get('model_urls', {}).get('glb'),
                            'obj_url': status_data.get('model_urls', {}).get('obj'),
                            'fbx_url': status_data.get('model_urls', {}).get('fbx'),
                            'usdz_url': status_data.get('model_urls', {}).get('usdz'),
                            'thumbnail_url': status_data.get('thumbnail_url'),
                            'completed_at': datetime.utcnow()
                        })
                    )
                    model = db.models.find_one({'_id': model['_id']})
                
                elif status_data.get('status') == 'FAILED':
                    db.models.update_one(
                        {'_id': model['_id']},
                        Model3DSchema.update({
                            'status': 'failed',
                            'error_message': status_data.get('error', 'Generation failed')
                        })
                    )
                    model = db.models.find_one({'_id': model['_id']})
            
            except Exception as e:
                logger.error(f"Failed to check status: {e}")
    
    # Return updated card
    model = doc_to_dict(model)
    model['status_display'] = get_display_name(model['status'], MODEL_STATUS_DISPLAY)
    return HttpResponse(render_to_string('partials/model_card.html', {'model': model}))


@login_required
@require_http_methods(["DELETE", "POST"])
def api_model_delete(request, model_id):
    """
    HTMX endpoint to delete model.
    """
    result = db.models.delete_one({'_id': to_object_id(model_id), 'user_id': str(request.user.id)})
    
    if result.deleted_count == 0:
        return HttpResponse('Model not found', status=404)
    
    # Also delete generation job
    db.generation_jobs.delete_one({'model_id': to_object_id(model_id)})
    
    return HttpResponse('Model deleted successfully')


@login_required
@require_http_methods(["GET"])
def proxy_glb(request, model_id):
    """
    Proxy endpoint to serve GLB files from Meshy.ai.
    Bypasses CORS restrictions.
    """
    model = db.models.find_one({'_id': to_object_id(model_id), 'user_id': str(request.user.id)})
    
    if not model or not model.get('glb_url'):
        return HttpResponse('GLB file not found', status=404)
    
    try:
        # Download from Meshy.ai
        response = requests.get(model['glb_url'], stream=True)
        response.raise_for_status()
        
        # Stream to client
        def file_iterator():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk
        
        streaming_response = StreamingHttpResponse(file_iterator(), content_type='model/gltf-binary')
        streaming_response['Access-Control-Allow-Origin'] = '*'
        streaming_response['Content-Disposition'] = f'inline; filename="model_{model_id}.glb"'
        
        return streaming_response
    
    except Exception as e:
        logger.error(f"Failed to proxy GLB: {e}")
        return HttpResponse(f'Failed to load model: {e}', status=500)



# ============================================================================
# PRINTER MANAGEMENT VIEWS
# ============================================================================

@login_required
def printers(request):
    """Printer management page."""
    return render(request, 'printers.html')


@login_required
def printer_add(request):
    """Add new printer page."""
    if request.method == 'POST':
        try:
            # Create printer document
            printer_doc = PrinterSchema.create(
                user_id=str(request.user.id),
                name=request.POST.get('name'),
                printer_type=request.POST.get('printer_type'),
                model=request.POST.get('model'),
                build_volume_x=int(request.POST.get('build_volume_x')),
                build_volume_y=int(request.POST.get('build_volume_y')),
                build_volume_z=int(request.POST.get('build_volume_z')),
                serial_number=request.POST.get('serial_number') or None,
                ip_address=request.POST.get('ip_address') or None,
                status=request.POST.get('status', 'idle'),
                current_mode=request.POST.get('current_mode') if request.POST.get('printer_type') == 'snapmaker' else None,
            )
            
            # Insert into MongoDB
            db.printers.insert_one(printer_doc)
            
            return redirect('/printers')
        
        except Exception as e:
            logger.error(f"Failed to create printer: {e}")
            return render(request, 'printer_form.html', {
                'error': str(e)
            })
    
    return render(request, 'printer_form.html')


@login_required
def printer_edit(request, printer_id):
    """Edit printer page."""
    printer = db.printers.find_one({'_id': to_object_id(printer_id), 'user_id': str(request.user.id)})
    
    if not printer:
        return HttpResponse('Printer not found', status=404)
    
    if request.method == 'POST':
        try:
            # Prepare updates
            updates = {
                'name': request.POST.get('name'),
                'printer_type': request.POST.get('printer_type'),
                'model': request.POST.get('model'),
                'serial_number': request.POST.get('serial_number') or None,
                'ip_address': request.POST.get('ip_address') or None,
                'build_volume_x': int(request.POST.get('build_volume_x')),
                'build_volume_y': int(request.POST.get('build_volume_y')),
                'build_volume_z': int(request.POST.get('build_volume_z')),
                'status': request.POST.get('status'),
                'current_mode': request.POST.get('current_mode') if request.POST.get('printer_type') == 'snapmaker' else None,
            }
            
            # Update in MongoDB
            db.printers.update_one(
                {'_id': printer['_id']},
                PrinterSchema.update(updates)
            )
            
            return redirect('/printers')
        
        except Exception as e:
            logger.error(f"Failed to update printer: {e}")
            printer = doc_to_dict(printer)
            return render(request, 'printer_form.html', {
                'printer': printer,
                'error': str(e)
            })
    
    printer = doc_to_dict(printer)
    return render(request, 'printer_form.html', {'printer': printer})


# ============================================================================
# PRINTER HTMX API ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_printers_list(request):
    """
    HTMX endpoint to list printers.
    Returns HTML grid of printer cards.
    """
    printers = list(db.printers.find({'user_id': str(request.user.id)}).sort('name', 1))
    
    if not printers:
        return HttpResponse('''
            <div class="text-center py-12">
                <svg class="w-24 h-24 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
                </svg>
                <h3 class="text-xl font-bold text-gray-700 mb-2">No Printers Yet</h3>
                <p class="text-gray-500 mb-6">Add your first 3D printer or CNC machine to get started</p>
                <a href="/printers/add" class="inline-block bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 transition">
                    Add Your First Printer
                </a>
            </div>
        ''')
    
    # Render printer cards
    html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
    for printer in printers:
        printer = doc_to_dict(printer)
        # Add display names
        printer['printer_type_display'] = get_display_name(printer['printer_type'], PRINTER_TYPE_DISPLAY)
        printer['status_display'] = get_display_name(printer['status'], PRINTER_STATUS_DISPLAY)
        if printer.get('current_mode'):
            printer['current_mode_display'] = get_display_name(printer['current_mode'], SNAPMAKER_MODE_DISPLAY)
        html += render_to_string('partials/printer_card.html', {'printer': printer})
    html += '</div>'
    
    return HttpResponse(html)


@login_required
@require_http_methods(["POST"])
def api_printer_change_mode(request, printer_id):
    """
    HTMX endpoint to change Snapmaker mode.
    """
    printer = db.printers.find_one({'_id': to_object_id(printer_id), 'user_id': str(request.user.id)})
    
    if not printer:
        return HttpResponse('Printer not found', status=404)
    
    if printer['printer_type'] != 'snapmaker':
        return HttpResponse('Only Snapmaker printers support mode changing', status=400)
    
    new_mode = request.POST.get('mode')
    if new_mode not in ['3d_print', 'cnc', 'laser']:
        return HttpResponse('Invalid mode', status=400)
    
    # Update mode
    db.printers.update_one(
        {'_id': printer['_id']},
        PrinterSchema.update({'current_mode': new_mode})
    )
    
    mode_display = get_display_name(new_mode, SNAPMAKER_MODE_DISPLAY)
    return HttpResponse(f'Mode changed to {mode_display}')


@login_required
@require_http_methods(["DELETE", "POST"])
def api_printer_delete(request, printer_id):
    """
    HTMX endpoint to delete printer.
    """
    result = db.printers.delete_one({'_id': to_object_id(printer_id), 'user_id': str(request.user.id)})
    
    if result.deleted_count == 0:
        return HttpResponse('Printer not found', status=404)
    
    return HttpResponse('Printer deleted successfully')


# Authentication Views

def signup(request):
    """User signup page."""
    if request.method == 'GET':
        return render(request, 'registration/signup.html')
    
    # POST - Handle signup
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    password2 = request.POST.get('password2', '')
    
    # Validation
    errors = []
    
    if not username:
        errors.append('Username is required')
    elif len(username) < 3:
        errors.append('Username must be at least 3 characters')
    elif db.users.find_one({'username': username}):
        errors.append('Username already exists')
    
    if not password:
        errors.append('Password is required')
    elif len(password) < 8:
        errors.append('Password must be at least 8 characters')
    elif password != password2:
        errors.append('Passwords do not match')
    
    if errors:
        error_html = '<div class="rounded-md bg-red-50 p-4 mb-4"><div class="flex"><div class="flex-shrink-0"><svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg></div><div class="ml-3"><h3 class="text-sm font-medium text-red-800">Errors:</h3><ul class="mt-2 text-sm text-red-700 list-disc list-inside">'
        for error in errors:
            error_html += f'<li>{error}</li>'
        error_html += '</ul></div></div></div>'
        
        return HttpResponse(error_html + render_to_string('registration/signup.html', request=request))
    
    # Create user
    try:
        from models.auth_backend import create_user
        user = create_user(
            username=username,
            email=email,
            password=password,
            is_superuser=False,
            is_staff=False
        )
        
        # Auto-login after signup
        from django.contrib.auth import login
        from models.auth_backend import MongoDBAuthBackend
        
        backend = MongoDBAuthBackend()
        authenticated_user = backend.authenticate(request, username=username, password=password)
        
        if authenticated_user:
            login(request, authenticated_user, backend='models.auth_backend.MongoDBAuthBackend')
            return HttpResponse('<script>window.location.href="/";</script>')
        else:
            return HttpResponse('<div class="rounded-md bg-green-50 p-4 mb-4"><p class="text-sm text-green-800">Account created! <a href="/login/" class="font-medium underline">Click here to login</a></p></div>')
    
    except Exception as e:
        return HttpResponse(f'<div class="rounded-md bg-red-50 p-4 mb-4"><p class="text-sm text-red-800">Failed to create account: {str(e)}</p></div>')
