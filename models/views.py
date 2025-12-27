"""
Django views for NexaAI using PyMongo for MongoDB operations.
Server-side rendering with HTMX for dynamic updates.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from functools import wraps

# Custom decorator for session-based authentication
def session_login_required(view_func):
    """
    Decorator that checks if user is logged in via session.
    Redirects to login page if not authenticated.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user' not in request.session:
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper
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

@session_login_required
def generate(request):
    """Model generation page."""
    return render(request, 'generate.html')


@session_login_required
def history(request):
    """Model history page."""
    return render(request, 'history.html')


@session_login_required
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

@session_login_required
@require_http_methods(["POST"])
def api_generate(request):
    """
    HTMX endpoint to generate 3D model with AI-powered design analysis.
    Analyzes the design, splits into parts, and recommends manufacturing methods.
    """
    try:
        from services.design_analyzer import DesignAnalyzer
        
        prompt = request.POST.get('prompt', '').strip()
        quality = request.POST.get('quality', 'preview')
        use_analysis = request.POST.get('use_analysis', 'true').lower() == 'true'
        
        if not prompt:
            return HttpResponse('Prompt is required', status=400)
        
        # Map quality to polygon count
        # NOTE: Meshy API uses 'preview' mode for initial generation.
        # 'refine' mode requires a preview_task_id and is a separate 2-step process.
        # Quality is controlled by target_polycount parameter.
        quality_map = {
            'preview': 10000,
            'standard': 30000,
            'high': 60000,
            'ultra': 100000,
        }
        polygon_count = quality_map.get(quality, 30000)
        
        logger.info(f"Generation request: quality={quality}, polycount={polygon_count}")
        
        # Analyze design and get recommendations
        if use_analysis:
            analyzer = DesignAnalyzer()
            analysis = analyzer.analyze_and_refine(prompt)
            logger.info(f"Design analysis complete: {len(analysis.get('parts', []))} parts")
        else:
            # Simple mode - just refine the prompt
            analyzer = DesignAnalyzer()
            refined_prompt = analyzer.refine_prompt_simple(prompt)
            analysis = {
                "original_prompt": prompt,
                "analysis": "Simple refinement",
                "parts": [{
                    "name": "Main Component",
                    "description": "Primary design component",
                    "refined_prompt": refined_prompt,
                    "manufacturing_method": "3d_print",
                    "reasoning": "Default manufacturing method",
                    "material_suggestion": "PLA",
                    "estimated_dimensions": "TBD",
                    "complexity": "medium"
                }],
                "assembly_notes": "Single part design"
            }
        
        # Generate 3D models for each part
        generated_parts = []
        meshy_client = MeshyClient()
        
        for part in analysis.get('parts', []):
            try:
                # Create model document for this part
                model_doc = Model3DSchema.create(
                    user_id=str(request.user.id),
                    prompt=part['refined_prompt'],
                    quality=quality,
                    polygon_count=polygon_count,
                    status='processing'
                )
                
                # Add design analysis metadata
                model_doc['original_prompt'] = prompt
                model_doc['part_name'] = part['name']
                model_doc['part_description'] = part['description']
                model_doc['manufacturing_method'] = part['manufacturing_method']
                model_doc['manufacturing_reasoning'] = part['reasoning']
                model_doc['material_suggestion'] = part['material_suggestion']
                model_doc['estimated_dimensions'] = part['estimated_dimensions']
                model_doc['complexity'] = part['complexity']
                model_doc['design_analysis'] = analysis
                
                # Insert into MongoDB
                result = db.models.insert_one(model_doc)
                model_id = result.inserted_id
                
                # Start Meshy.ai generation with Meshy-6
                result = meshy_client.create_text_to_3d_task(
                    prompt=part['refined_prompt'],
                    art_style='realistic',
                    target_polycount=polygon_count,
                    ai_model='latest'  # Use Meshy-6 for best quality
                )
                task_id = result.get('result')
                
                # Create generation job
                job_doc = GenerationJobSchema.create(
                    model_id=model_id,
                    meshy_task_id=task_id,
                    meshy_status='PENDING'
                )
                db.generation_jobs.insert_one(job_doc)
                
                generated_parts.append({
                    'model_id': str(model_id),
                    'part_name': part['name'],
                    'manufacturing_method': part['manufacturing_method']
                })
                
                logger.info(f"Started generation for part '{part['name']}': model {model_id}, task {task_id}")
            
            except Exception as e:
                logger.error(f"Failed to generate part '{part['name']}': {e}")
                # Continue with other parts even if one fails
        
        if not generated_parts:
            return HttpResponse('Failed to start any generation tasks', status=500)
        
        # Notify owner
        try:
            notify_owner(
                title=f"Design Analysis Complete - {len(generated_parts)} Parts",
                content=f"Original: {prompt}\nParts: {', '.join([p['part_name'] for p in generated_parts])}"
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
        
        # Return success message with part details
        parts_summary = "<br>".join([
            f"• {p['part_name']} ({p['manufacturing_method'].replace('_', ' ').title()})"
            for p in generated_parts
        ])
        
        return HttpResponse(
            f"<div class='space-y-2'>" 
            f"<p class='font-bold'>Design analyzed and split into {len(generated_parts)} part(s):</p>"
            f"<div class='text-sm'>{parts_summary}</div>"
            f"<p class='text-sm text-gray-600 mt-2'>Check the History page to see generation progress.</p>"
            f"</div>"
        )
    
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return HttpResponse(f'Error: {e}', status=500)


@session_login_required
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


@session_login_required
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


@session_login_required
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


@session_login_required
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


@session_login_required
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

@session_login_required
def printers(request):
    """Printer management page."""
    return render(request, 'printers.html')


@session_login_required
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
                api_key=request.POST.get('api_key') or None,
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


@session_login_required
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
                'api_key': request.POST.get('api_key') or None,
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

@session_login_required
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


@session_login_required
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


@session_login_required
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
    username = request.POST.get('username', '').strip().lower()  # Convert to lowercase
    email = request.POST.get('email', '').strip().lower()  # Convert to lowercase
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
        
        # Show success message and redirect to login
        success_html = '''
        <div class="rounded-md bg-green-50 p-4 mb-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-green-800">Account created successfully!</h3>
                    <div class="mt-2 text-sm text-green-700">
                        <p>Your account has been created. <a href="/login/" class="font-medium underline hover:text-green-600">Click here to login</a></p>
                    </div>
                </div>
            </div>
        </div>
        <script>setTimeout(function() { window.location.href = "/login/"; }, 2000);</script>
        '''
        return HttpResponse(success_html)
    
    except Exception as e:
        return HttpResponse(f'<div class="rounded-md bg-red-50 p-4 mb-4"><p class="text-sm text-red-800">Failed to create account: {str(e)}</p></div>')


def login_view(request):
    """Session-based login view for MongoDB authentication."""
    if request.method == 'GET':
        # If already logged in, redirect to home
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'registration/login.html')
    
    # POST - Handle login
    from django.contrib.auth.hashers import check_password
    
    username = request.POST.get('username', '').strip().lower()  # Convert to lowercase
    password = request.POST.get('password', '')
    
    # Validation
    if not username or not password:
        context = {
            'error': 'Username and password are required',
            'username': username
        }
        return render(request, 'registration/login.html', context)
    
    # Find user in MongoDB
    user = db.users.find_one({'username': username})
    
    if user and check_password(password, user['password']):
        # Login successful - store user data in session
        user_session_data = {
            '_id': str(user['_id']),
            'username': user['username'],
            'email': user.get('email', ''),
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', ''),
            'is_active': user.get('is_active', True),
            'is_staff': user.get('is_staff', False),
            'is_superuser': user.get('is_superuser', False),
        }
        
        request.session['user'] = user_session_data
        
        # Update last_login
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Redirect to next page or home
        next_url = request.GET.get('next', '/')
        return redirect(next_url)
    else:
        # Login failed
        context = {
            'error': 'Invalid username or password',
            'username': username
        }
        return render(request, 'registration/login.html', context)



def logout_view(request):
    """Custom logout view that works with GET requests."""
    # Clear the session
    if 'user' in request.session:
        del request.session['user']
    
    # Also logout from Django auth system if used
    from django.contrib.auth import logout
    logout(request)
    
    # Redirect to home page
    return redirect('/')
