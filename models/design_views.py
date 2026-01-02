"""
Views for 3-stage design workflow.
Stage 1: Design Concept → Stage 2: Part Breakdown → Stage 3: 3D Generation
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from models.mongodb import db, to_object_id, doc_to_dict
from models.design_schemas import (
    DesignProjectSchema, DesignConceptSchema, PartBreakdownSchema, PartSchema
)
from models.schemas import Model3DSchema, GenerationJobSchema
from services.enhanced_design_analyzer import (
    generate_design_concept, break_down_into_parts, generate_part_prompts
)
from services.meshy_client import MeshyClient
from models.views import session_login_required
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


@session_login_required
@require_http_methods(["GET"])
def design_projects(request):
    """Design projects page - shows all user's design projects."""
    projects = list(db.design_projects.find({'user_id': str(request.user.id)}).sort('created_at', -1))
    
    for project in projects:
        project = doc_to_dict(project)
    
    return render(request, 'design_projects.html', {'projects': projects})


@session_login_required
@require_http_methods(["GET"])
def design_project_detail(request, project_id):
    """Design project detail page - shows current stage and allows progression."""
    project = db.design_projects.find_one({
        '_id': to_object_id(project_id),
        'user_id': str(request.user.id)
    })
    
    if not project:
        return HttpResponse('Project not found', status=404)
    
    project = doc_to_dict(project)
    
    # Convert overall model file paths to URLs
    from pathlib import Path
    media_root = str(Path(settings.MEDIA_ROOT))
    if project.get('overall_model_step_path'):
        project['overall_model_step_url'] = project['overall_model_step_path'].replace(media_root, '/media').replace('\\\\', '/')
    if project.get('overall_model_stl_path'):
        project['overall_model_stl_url'] = project['overall_model_stl_path'].replace(media_root, '/media').replace('\\\\', '/')
    
    # Get related data based on stage
    concept = None
    breakdown = None
    models = []
    
    if project['stage'] in ['concept', 'overall_model', 'parts', 'generation', 'completed']:
        concept = db.design_concepts.find_one({'project_id': to_object_id(project_id)})
        if concept:
            concept = doc_to_dict(concept)
    
    if project['stage'] in ['parts', 'generation', 'completed']:
        breakdown = db.part_breakdowns.find_one({'project_id': to_object_id(project_id)})
        if breakdown:
            breakdown = doc_to_dict(breakdown)
            # Convert file paths to URLs for each part
            part_media_root = str(Path(settings.MEDIA_ROOT))
            for part in breakdown.get('parts', []):
                if part.get('step_file_path'):
                    part['step_url'] = part['step_file_path'].replace(part_media_root, '/media').replace('\\\\', '/')
                if part.get('stl_file_path'):
                    part['stl_url'] = part['stl_file_path'].replace(part_media_root, '/media').replace('\\\\', '/')
    
    if project['stage'] in ['generation', 'completed']:
        models = list(db.models.find({'project_id': to_object_id(project_id)}))
        for model in models:
            model = doc_to_dict(model)
    
    return render(request, 'design_project_detail.html', {
        'project': project,
        'concept': concept,
        'breakdown': breakdown,
        'models': models
    })


# ============================================================================
# STAGE 1: DESIGN CONCEPT API ENDPOINTS
# ============================================================================

@session_login_required
@require_http_methods(["POST"])
def api_create_design_project(request):
    """
    HTMX endpoint to create a new design project and generate concept.
    """
    try:
        original_prompt = request.POST.get('prompt', '').strip()
        
        if not original_prompt:
            return HttpResponse('Design prompt is required', status=400)
        
        # Create design project
        project_doc = DesignProjectSchema.create(
            user_id=request.user.id,
            original_prompt=original_prompt
        )
        result = db.design_projects.insert_one(project_doc)
        project_id = result.inserted_id
        
        # Generate design concept using AI
        logger.info(f"Generating design concept for project {project_id}")
        concept_data = generate_design_concept(original_prompt)
        
        # Save design concept
        concept_doc = DesignConceptSchema.create(
            project_id=project_id,
            original_prompt=original_prompt,
            **concept_data
        )
        db.design_concepts.insert_one(concept_doc)
        
        # Update project
        db.design_projects.update_one(
            {'_id': project_id},
            {'$set': {
                'concept_description': concept_data['refined_description'],
                'status': 'pending',
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Return HTMX response with concept card (dark theme)
        return HttpResponse(f'''
            <div class="cad-card mb-6" id="concept-{project_id}">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-2xl font-bold" style="color: #ffffff;">Design Concept</h3>
                    <span class="stage-badge stage-badge-concept">
                        Stage 1: Concept
                    </span>
                </div>
                
                <div class="mb-4">
                    <p class="text-sm mb-2" style="color: #8a8694;">Original Prompt:</p>
                    <p class="italic" style="color: #c084fc;">"{original_prompt}"</p>
                </div>
                
                <div class="mb-4">
                    <p class="text-sm font-semibold mb-2" style="color: #b8b4c5;">AI-Generated Design Concept:</p>
                    <p class="leading-relaxed" style="color: #e0dce8;">{concept_data['refined_description']}</p>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <p class="text-sm" style="color: #8a8694;">Design Type:</p>
                        <p class="font-semibold" style="color: #ffffff;">{concept_data['design_type'].title()}</p>
                    </div>
                    <div>
                        <p class="text-sm" style="color: #8a8694;">Estimated Complexity:</p>
                        <p class="font-semibold" style="color: #ffffff;">{concept_data['estimated_complexity'].title()}</p>
                    </div>
                    <div>
                        <p class="text-sm" style="color: #8a8694;">Estimated Parts:</p>
                        <p class="font-semibold" style="color: #ffffff;">{concept_data['estimated_parts_count']} parts</p>
                    </div>
                </div>
                
                <div class="mb-6">
                    <p class="text-sm font-semibold mb-2" style="color: #b8b4c5;">Key Features:</p>
                    <ul class="list-disc list-inside space-y-1">
                        {''.join([f'<li style="color: #e0dce8;">{feature}</li>' for feature in concept_data['key_features']])}
                    </ul>
                </div>
                
                <div class="flex gap-4">
                    <button 
                        hx-post="/api/design/approve-concept/{project_id}/"
                        hx-target="#concept-{project_id}"
                        hx-swap="outerHTML"
                        class="cad-btn-primary flex-1">
                        ✓ Approve & Generate Overall Model
                    </button>
                    <button 
                        onclick="document.getElementById('refine-form-{project_id}').classList.toggle('hidden')"
                        class="cad-btn-secondary flex-1">
                        ↻ Refine Concept
                    </button>
                </div>
                
                <div id="refine-form-{project_id}" class="mt-4 hidden">
                    <form hx-post="/api/design/refine-concept/{project_id}/" hx-target="#concept-{project_id}" hx-swap="outerHTML">
                        <label class="block text-sm font-semibold mb-2" style="color: #b8b4c5;">Provide feedback to refine the concept:</label>
                        <textarea 
                            name="feedback" 
                            rows="3" 
                            placeholder="Example: Make it smaller, use aluminum instead of plastic, add more storage..."
                            class="cad-textarea"
                            required></textarea>
                        <button type="submit" class="cad-btn-primary mt-2">
                            Refine Concept
                        </button>
                    </form>
                </div>
            </div>
        ''')
    
    except Exception as e:
        logger.error(f"Failed to create design project: {e}")
        return HttpResponse(f'Error: {e}', status=500)


@session_login_required
@require_http_methods(["POST"])
def api_refine_concept(request, project_id):
    """
    HTMX endpoint to refine the design concept based on user feedback.
    """
    try:
        feedback = request.POST.get('feedback', '').strip()
        
        if not feedback:
            return HttpResponse('Feedback is required', status=400)
        
        # Get project and original concept
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return HttpResponse('Project not found', status=404)
        
        # Get original concept
        concept = db.design_concepts.find_one({'project_id': to_object_id(project_id)})
        
        if not concept:
            return HttpResponse('Concept not found', status=404)
        
        # Combine original prompt with feedback
        original_prompt = project.get('original_prompt', '')
        refined_prompt = f"{original_prompt}\n\nUser Feedback: {feedback}"
        
        logger.info(f"Refining design concept for project {project_id} with feedback")
        
        # Generate refined concept using AI
        concept_data = generate_design_concept(refined_prompt)
        
        # Update existing concept with refined data (only fields that exist)
        update_fields = {
            'refined_description': concept_data.get('refined_description', ''),
            'design_type': concept_data.get('design_type', ''),
            'key_features': concept_data.get('key_features', []),
            'estimated_complexity': concept_data.get('estimated_complexity', ''),
            'estimated_parts_count': concept_data.get('estimated_parts_count', 1),
            'user_feedback': feedback,
            'updated_at': datetime.utcnow()
        }
        
        db.design_concepts.update_one(
            {'project_id': to_object_id(project_id)},
            {'$set': update_fields}
        )
        
        # Update project
        db.design_projects.update_one(
            {'_id': to_object_id(project_id)},
            {'$set': {
                'concept_description': concept_data['refined_description'],
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Reload updated concept from database
        updated_concept = db.design_concepts.find_one({'project_id': to_object_id(project_id)})
        
        # Return success message - let the page reload to show updated concept
        return HttpResponse('''
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
                <strong class="font-bold">Success!</strong>
                <span class="block sm:inline">Concept has been refined. Refreshing...</span>
            </div>
            <script>
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            </script>
        ''')
    
    except Exception as e:
        logger.error(f"Error refining concept: {e}")
        return HttpResponse(f'Error refining concept: {str(e)}', status=500)


@session_login_required
@require_http_methods(["POST"])
def api_approve_concept(request, project_id):
    """
    HTMX endpoint to approve concept and move to overall model generation.
    """
    try:
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return HttpResponse('Project not found', status=404)
        
        # Approve concept
        db.design_concepts.update_one(
            {'project_id': to_object_id(project_id)},
            {'$set': {'status': 'approved', 'approved_at': datetime.utcnow()}}
        )
        
        # Update project to overall_model stage
        db.design_projects.update_one(
            {'_id': to_object_id(project_id)},
            {'$set': {
                'stage': 'overall_model',
                'concept_approved_at': datetime.utcnow(),
                'status': 'generating',
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Redirect to project detail page to show overall model stage
        return HttpResponse(f'''
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                <p class="font-semibold">✓ Concept approved!</p>
                <p class="text-sm">Redirecting to overall model generation...</p>
            </div>
            <script>
                setTimeout(function() {{
                    window.location.href = '/design/projects/{project_id}/';
                }}, 1000);
            </script>
        ''')
    
    except Exception as e:
        logger.error(f"Failed to approve concept: {e}")
        return HttpResponse(f'Error: {e}', status=500)


# ============================================================================
# STAGE 3: 3D GENERATION API ENDPOINTS
# ============================================================================

@session_login_required
@require_http_methods(["POST"])
def api_approve_parts(request, project_id):
    """
    HTMX endpoint to approve parts and start 3D generation for all parts.
    """
    try:
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return HttpResponse('Project not found', status=404)
        
        # Approve parts
        db.part_breakdowns.update_one(
            {'project_id': to_object_id(project_id)},
            {'$set': {'status': 'approved', 'approved_at': datetime.utcnow()}}
        )
        
        # Get parts breakdown
        breakdown = db.part_breakdowns.find_one({'project_id': to_object_id(project_id)})
        parts_list = breakdown['parts']
        
        # Update project stage
        db.design_projects.update_one(
            {'_id': to_object_id(project_id)},
            {'$set': {
                'stage': 'generation',
                'parts_approved_at': datetime.utcnow(),
                'status': 'generating',
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Start generating 3D models for each part
        meshy_client = MeshyClient()
        generated_count = 0
        
        for part in parts_list:
            try:
                # Create model document
                model_doc = Model3DSchema.create(
                    user_id=request.user.id,
                    prompt=part['refined_prompt'],
                    refined_prompt=part['refined_prompt'],
                    art_style='realistic',
                    quality='high',  # Use high quality for final parts
                    polygon_count=60000,
                    status='processing'
                )
                model_doc['project_id'] = to_object_id(project_id)
                model_doc['part_number'] = part['part_number']
                model_doc['part_name'] = part['name']
                model_doc['manufacturing_method'] = part['manufacturing_method']
                
                result = db.models.insert_one(model_doc)
                model_id = result.inserted_id
                
                # Start Meshy generation with Meshy-6
                meshy_result = meshy_client.create_text_to_3d_task(
                    prompt=part['refined_prompt'],
                    art_style='realistic',
                    target_polycount=60000,
                    ai_model='latest'  # Use Meshy-6
                )
                task_id = meshy_result.get('result')
                
                # Create generation job
                job_doc = GenerationJobSchema.create(
                    model_id=model_id,
                    meshy_task_id=task_id,
                    stage='preview'
                )
                db.generation_jobs.insert_one(job_doc)
                
                # Update part with model_id
                part['model_id'] = str(model_id)
                part['status'] = 'generating'
                
                generated_count += 1
                logger.info(f"Started generation for part {part['part_number']}: {part['name']}")
            
            except Exception as e:
                logger.error(f"Failed to start generation for part {part['name']}: {e}")
                part['status'] = 'failed'
        
        # Update parts in breakdown
        db.part_breakdowns.update_one(
            {'project_id': to_object_id(project_id)},
            {'$set': {'parts': parts_list}}
        )
        
        return HttpResponse(f'''
            <div class="cad-card mb-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-2xl font-bold" style="color: #ffffff;">3D Generation Started</h3>
                    <span class="stage-badge stage-badge-generation">
                        Stage 3: Generation
                    </span>
                </div>
                
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem;">
                    <p style="color: #34d399; font-weight: 600;">✓ Generation started for {generated_count} parts!</p>
                    <p style="color: #6ee7b7; font-size: 0.875rem; margin-top: 0.5rem;">
                        Using Meshy-6 (latest model) for best quality. Each part will go through:
                        <br>1. Preview generation (5-10 min)
                        <br>2. Automatic refine with textures (10-15 min)
                        <br>3. Automatic GLB download
                    </p>
                </div>
                
                <div class="mb-4">
                    <p style="color: #e0dce8;">
                        Your parts are being generated in the background. You can check progress in the 
                        <a href="/history/" style="color: #c084fc; text-decoration: underline;">History</a> page.
                    </p>
                </div>
                
                <a href="/design/projects/{project_id}/" class="cad-btn-primary">
                    View Project Details
                </a>
            </div>
        ''')
    
    except Exception as e:
        logger.error(f"Failed to approve parts: {e}")
        return HttpResponse(f'Error: {e}', status=500)
