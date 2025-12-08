"""
Django template views for Manufacturing Orchestrator.
Replaces REST API with server-side rendering using HTMX.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string

from models.models import User, Model3D, GenerationJob
from services.meshy_client import MeshyClient
from services.prompt_refinement import refine_prompt_with_llm
from services.notifications import notify_owner

import logging

logger = logging.getLogger(__name__)


def home(request):
    """Landing page."""
    return render(request, 'home.html')


@login_required
def generate(request):
    """Model generation page."""
    # Pre-fill prompt from query parameter if provided
    initial_prompt = request.GET.get('prompt', '')
    return render(request, 'generate.html', {
        'initial_prompt': initial_prompt
    })


@login_required
def history(request):
    """Model history/gallery page."""
    return render(request, 'history.html')


@login_required
def viewer(request, model_id):
    """3D model viewer page."""
    model = get_object_or_404(Model3D, id=model_id, user=request.user)
    return render(request, 'viewer.html', {
        'model': model
    })


# HTMX API Endpoints

@login_required
@require_http_methods(["POST"])
def api_generate(request):
    """
    HTMX endpoint to start model generation.
    Returns HTML fragment with generation status.
    """
    prompt = request.POST.get('prompt', '').strip()
    art_style = request.POST.get('art_style', '')
    quality = request.POST.get('quality', 'preview')
    
    if not prompt:
        return HttpResponse(
            '<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Please enter a prompt</div>',
            status=400
        )
    
    try:
        # Create model instance
        model = Model3D.objects.create(
            user=request.user,
            prompt=prompt,
            art_style=art_style if art_style else None,
            quality=quality,
            status='pending'
        )
        
        # Initialize Meshy client
        meshy_client = MeshyClient()
        
        # Determine polygon count based on quality
        quality_map = {
            'preview': 10000,
            'standard': 30000,
            'high': 60000,
            'ultra': 100000
        }
        polygon_count = quality_map.get(quality, 10000)  # Default to preview
        
        # Start generation task
        task_response = meshy_client.create_text_to_3d_task(
            prompt=prompt,
            art_style=art_style if art_style else None,
            target_polycount=polygon_count
        )
        
        # Create generation job
        GenerationJob.objects.create(
            model=model,
            meshy_task_id=task_response['result'],
            meshy_status='pending',
            meshy_response=task_response
        )
        
        # Update model status
        model.status = 'processing'
        model.save()
        
        # Notify owner
        try:
            notify_owner(
                title="New 3D Model Generation Started",
                content=f"User {request.user.username} started generating: {prompt[:100]}"
            )
        except Exception as e:
            logger.warning(f"Failed to send owner notification: {e}")
        
        # Return success HTML fragment
        html = f'''
        <div class="bg-green-100 border border-green-400 text-green-700 px-6 py-4 rounded-lg mb-4">
            <h3 class="font-bold text-lg mb-2">✓ Generation Started!</h3>
            <p class="mb-3">Your 3D model is being generated. This usually takes 2-5 minutes.</p>
            <div class="flex space-x-3">
                <a href="/history" class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition">
                    View in History
                </a>
                <button 
                    hx-get="/api/models/{model.id}/status" 
                    hx-target="#generation-result" 
                    hx-swap="innerHTML"
                    hx-trigger="every 5s"
                    class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                    Check Status
                </button>
            </div>
        </div>
        '''
        return HttpResponse(html)
    
    except Exception as e:
        logger.error(f"Failed to create generation task: {e}")
        return HttpResponse(
            f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Failed to start generation: {str(e)}</div>',
            status=500
        )


@login_required
@require_http_methods(["POST"])
def api_refine_prompt(request):
    """
    HTMX endpoint to refine prompt with LLM.
    Returns updated textarea with refined prompt.
    """
    prompt = request.POST.get('prompt', '').strip()
    
    if not prompt:
        return HttpResponse(
            '<textarea id="prompt" name="prompt" rows="4" required class="w-full px-4 py-3 border border-red-300 rounded-lg" placeholder="Please enter a prompt first"></textarea>',
            status=400
        )
    
    try:
        # Refine prompt using LLM
        result = refine_prompt_with_llm(prompt)
        refined_prompt = result.get('refined_prompt', prompt)
        
        # Return updated textarea
        html = f'''
        <textarea 
            id="prompt" 
            name="prompt" 
            rows="4" 
            required
            class="w-full px-4 py-3 border border-green-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >{refined_prompt}</textarea>
        <p class="text-sm text-green-600 mt-2">✓ Prompt refined with AI suggestions</p>
        '''
        return HttpResponse(html)
    
    except Exception as e:
        logger.error(f"Failed to refine prompt: {e}")
        return HttpResponse(
            f'<textarea id="prompt" name="prompt" rows="4" required class="w-full px-4 py-3 border border-red-300 rounded-lg">{prompt}</textarea><p class="text-sm text-red-600 mt-2">Failed to refine prompt: {str(e)}</p>',
            status=500
        )


@login_required
@require_http_methods(["GET"])
def api_models_list(request):
    """
    HTMX endpoint to list models.
    Returns HTML grid of model cards.
    """
    status_filter = request.GET.get('status', 'all')
    
    # Get user's models
    models = Model3D.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply status filter
    if status_filter and status_filter != 'all':
        models = models.filter(status=status_filter)
    
    # Render model cards
    if models.exists():
        html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
        for model in models:
            card_html = render_to_string('partials/model_card.html', {'model': model})
            html += card_html
        html += '</div>'
    else:
        html = '''
        <div class="text-center py-16">
            <svg class="w-24 h-24 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
            </svg>
            <h3 class="text-xl font-bold text-gray-600 mb-2">No models found</h3>
            <p class="text-gray-500 mb-6">Start generating your first 3D model!</p>
            <a href="/generate" class="bg-purple-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-purple-700 transition inline-block">
                Generate Model
            </a>
        </div>
        '''
    
    return HttpResponse(html)


@login_required
@require_http_methods(["GET"])
def api_model_status(request, model_id):
    """
    HTMX endpoint to check model generation status.
    Returns updated model card or status message.
    """
    model = get_object_or_404(Model3D, id=model_id, user=request.user)
    
    if model.status == 'completed':
        # Return updated model card
        return HttpResponse(render_to_string('partials/model_card.html', {'model': model}))
    
    if model.status == 'failed':
        return HttpResponse(
            f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Generation failed: {model.error_message}</div>',
            status=400
        )
    
    try:
        # Get generation job
        job = model.generation_job
        
        # Check status with Meshy
        meshy_client = MeshyClient()
        task_status = meshy_client.get_task_status(job.meshy_task_id)
        
        # Update job
        job.meshy_status = task_status['status']
        job.meshy_response = task_status
        job.progress = task_status.get('progress', 0)
        job.last_checked_at = timezone.now()
        job.save()
        
        # Update model if completed
        if task_status['status'] == 'SUCCEEDED':
            model.status = 'completed'
            model.completed_at = timezone.now()
            
            # Store file URLs
            model.glb_url = task_status.get('model_urls', {}).get('glb')
            model.obj_url = task_status.get('model_urls', {}).get('obj')
            model.fbx_url = task_status.get('model_urls', {}).get('fbx')
            model.usdz_url = task_status.get('model_urls', {}).get('usdz')
            model.thumbnail_url = task_status.get('thumbnail_url')
            
            model.save()
            
            # Notify owner
            try:
                notify_owner(
                    title="3D Model Generation Completed",
                    content=f"Model '{model.prompt[:100]}' completed successfully"
                )
            except Exception as e:
                logger.warning(f"Failed to send owner notification: {e}")
            
            # Return updated model card
            return HttpResponse(render_to_string('partials/model_card.html', {'model': model}))
        
        elif task_status['status'] == 'FAILED':
            model.status = 'failed'
            model.error_message = task_status.get('error', 'Unknown error')
            model.save()
            
            # Notify owner
            try:
                notify_owner(
                    title="3D Model Generation Failed",
                    content=f"Model '{model.prompt[:100]}' failed: {model.error_message}"
                )
            except Exception as e:
                logger.warning(f"Failed to send owner notification: {e}")
            
            return HttpResponse(render_to_string('partials/model_card.html', {'model': model}))
        
        else:
            # Still processing - return progress indicator
            progress = job.progress
            html = f'''
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 class="font-bold text-lg mb-2">Generating...</h3>
                <div class="w-full bg-gray-200 rounded-full h-4 mb-2">
                    <div class="bg-blue-600 h-4 rounded-full transition-all duration-500" style="width: {progress}%"></div>
                </div>
                <p class="text-sm text-gray-600">{progress}% complete</p>
            </div>
            '''
            return HttpResponse(html)
    
    except Exception as e:
        logger.error(f"Failed to check generation status: {e}")
        return HttpResponse(
            f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Failed to check status: {str(e)}</div>',
            status=500
        )


@login_required
@require_http_methods(["DELETE"])
def api_model_delete(request, model_id):
    """
    HTMX endpoint to delete a model.
    Returns redirect to history page.
    """
    model = get_object_or_404(Model3D, id=model_id, user=request.user)
    model.delete()
    
    # Return HX-Redirect header to redirect to history
    response = HttpResponse(status=200)
    response['HX-Redirect'] = '/history'
    return response


@login_required
@require_http_methods(["GET"])
def api_model_status(request, model_id):
    """
    HTMX endpoint to check single model status.
    Checks Meshy.ai API if still processing.
    Returns updated model card HTML.
    """
    model = get_object_or_404(Model3D, id=model_id, user=request.user)
    
    # If still processing, check Meshy.ai for updates
    if model.status == 'processing':
        try:
            job = GenerationJob.objects.filter(model=model).first()
            if job and job.meshy_task_id:
                meshy_client = MeshyClient()
                status_response = meshy_client.get_task_status(job.meshy_task_id)
                
                # Update job status
                job.meshy_status = status_response.get('status', 'unknown')
                job.meshy_response = status_response
                job.save()
                
                # Check if completed
                if status_response.get('status') == 'SUCCEEDED':
                    model.status = 'completed'
                    model.glb_url = status_response.get('model_urls', {}).get('glb')
                    model.obj_url = status_response.get('model_urls', {}).get('obj')
                    model.thumbnail_url = status_response.get('thumbnail_url')
                    model.save()
                    
                    # Notify owner
                    try:
                        notify_owner(
                            title="3D Model Generation Completed",
                            content=f"Model '{model.prompt[:50]}' is ready!"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")
                
                elif status_response.get('status') in ['FAILED', 'EXPIRED']:
                    model.status = 'failed'
                    model.save()
        
        except Exception as e:
            logger.error(f"Failed to check model status: {e}")
    
    # Return updated model card
    return render(request, 'partials/model_card.html', {'model': model})
