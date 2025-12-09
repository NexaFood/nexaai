"""
Views for 3-stage design workflow.
Stage 1: Design Concept → Stage 2: Part Breakdown → Stage 3: 3D Generation
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
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
    
    # Get related data based on stage
    concept = None
    breakdown = None
    models = []
    
    if project['stage'] in ['concept', 'parts', 'generation', 'completed']:
        concept = db.design_concepts.find_one({'project_id': to_object_id(project_id)})
        if concept:
            concept = doc_to_dict(concept)
    
    if project['stage'] in ['parts', 'generation', 'completed']:
        breakdown = db.part_breakdowns.find_one({'project_id': to_object_id(project_id)})
        if breakdown:
            breakdown = doc_to_dict(breakdown)
    
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
        
        # Return HTMX response with concept card
        return HttpResponse(f'''
            <div class="bg-white rounded-lg shadow-lg p-6 mb-6" id="concept-{project_id}">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-2xl font-bold text-gray-800">Design Concept</h3>
                    <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                        Stage 1: Concept
                    </span>
                </div>
                
                <div class="mb-4">
                    <p class="text-sm text-gray-500 mb-2">Original Prompt:</p>
                    <p class="text-gray-700 italic">"{original_prompt}"</p>
                </div>
                
                <div class="mb-4">
                    <p class="text-sm font-semibold text-gray-700 mb-2">AI-Generated Design Concept:</p>
                    <p class="text-gray-800 leading-relaxed">{concept_data['refined_description']}</p>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <p class="text-sm text-gray-500">Design Type:</p>
                        <p class="font-semibold text-gray-800">{concept_data['design_type'].title()}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">Estimated Complexity:</p>
                        <p class="font-semibold text-gray-800">{concept_data['estimated_complexity'].title()}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">Estimated Parts:</p>
                        <p class="font-semibold text-gray-800">{concept_data['estimated_parts_count']} parts</p>
                    </div>
                </div>
                
                <div class="mb-6">
                    <p class="text-sm font-semibold text-gray-700 mb-2">Key Features:</p>
                    <ul class="list-disc list-inside space-y-1">
                        {''.join([f'<li class="text-gray-700">{feature}</li>' for feature in concept_data['key_features']])}
                    </ul>
                </div>
                
                <div class="flex gap-4">
                    <button 
                        hx-post="/api/design/approve-concept/{project_id}/"
                        hx-target="#concept-{project_id}"
                        hx-swap="outerHTML"
                        class="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition">
                        ✓ Approve & Continue to Part Breakdown
                    </button>
                    <button 
                        hx-post="/api/design/refine-concept/{project_id}/"
                        hx-target="#concept-{project_id}"
                        hx-swap="outerHTML"
                        class="flex-1 bg-yellow-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-yellow-700 transition">
                        ↻ Refine Concept
                    </button>
                </div>
            </div>
        ''')
    
    except Exception as e:
        logger.error(f"Failed to create design project: {e}")
        return HttpResponse(f'Error: {e}', status=500)


@session_login_required
@require_http_methods(["POST"])
def api_approve_concept(request, project_id):
    """
    HTMX endpoint to approve concept and move to part breakdown.
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
        
        # Get concept for part breakdown
        concept = db.design_concepts.find_one({'project_id': to_object_id(project_id)})
        
        # Generate part breakdown
        logger.info(f"Generating part breakdown for project {project_id}")
        parts_list = break_down_into_parts(
            design_concept=concept,
            original_prompt=project['original_prompt']
        )
        
        # Add refined prompts to parts
        parts_list = generate_part_prompts(parts_list, concept)
        
        # Save part breakdown
        breakdown_doc = PartBreakdownSchema.create(
            project_id=project_id,
            parts_list=parts_list
        )
        db.part_breakdowns.insert_one(breakdown_doc)
        
        # Update project
        db.design_projects.update_one(
            {'_id': to_object_id(project_id)},
            {'$set': {
                'stage': 'parts',
                'concept_approved_at': datetime.utcnow(),
                'total_parts': len(parts_list),
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Return parts breakdown HTML
        parts_html = ''.join([
            f'''
            <tr class="border-b hover:bg-gray-50">
                <td class="px-4 py-3 text-sm">{part['part_number']}</td>
                <td class="px-4 py-3">
                    <p class="font-semibold text-gray-800">{part['name']}</p>
                    <p class="text-sm text-gray-600">{part['description']}</p>
                </td>
                <td class="px-4 py-3">
                    <span class="px-2 py-1 rounded text-xs font-semibold {'bg-purple-100 text-purple-800' if part['manufacturing_method'] == '3d_print' else 'bg-blue-100 text-blue-800'}">
                        {'3D Print' if part['manufacturing_method'] == '3d_print' else 'CNC'}
                    </span>
                </td>
                <td class="px-4 py-3 text-sm">{part['material_recommendation']}</td>
                <td class="px-4 py-3 text-sm">{part['estimated_dimensions']['x']}×{part['estimated_dimensions']['y']}×{part['estimated_dimensions']['z']}mm</td>
                <td class="px-4 py-3 text-sm text-center">{part['quantity']}</td>
            </tr>
            '''
            for part in parts_list
        ])
        
        return HttpResponse(f'''
            <div class="bg-white rounded-lg shadow-lg p-6 mb-6" id="parts-{project_id}">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-2xl font-bold text-gray-800">Part Breakdown</h3>
                    <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                        Stage 2: Parts
                    </span>
                </div>
                
                <div class="mb-4 grid grid-cols-3 gap-4">
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <p class="text-sm text-gray-500">Total Parts</p>
                        <p class="text-2xl font-bold text-gray-800">{len(parts_list)}</p>
                    </div>
                    <div class="bg-purple-50 p-4 rounded-lg">
                        <p class="text-sm text-gray-500">3D Print</p>
                        <p class="text-2xl font-bold text-purple-800">{sum(1 for p in parts_list if p['manufacturing_method'] == '3d_print')}</p>
                    </div>
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <p class="text-sm text-gray-500">CNC</p>
                        <p class="text-2xl font-bold text-blue-800">{sum(1 for p in parts_list if p['manufacturing_method'] == 'cnc')}</p>
                    </div>
                </div>
                
                <div class="overflow-x-auto mb-6">
                    <table class="w-full">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="px-4 py-3 text-left text-sm font-semibold">#</th>
                                <th class="px-4 py-3 text-left text-sm font-semibold">Part Name & Description</th>
                                <th class="px-4 py-3 text-left text-sm font-semibold">Method</th>
                                <th class="px-4 py-3 text-left text-sm font-semibold">Material</th>
                                <th class="px-4 py-3 text-left text-sm font-semibold">Dimensions</th>
                                <th class="px-4 py-3 text-left text-sm font-semibold">Qty</th>
                            </tr>
                        </thead>
                        <tbody>
                            {parts_html}
                        </tbody>
                    </table>
                </div>
                
                <div class="mb-4">
                    <p class="text-sm font-semibold text-gray-700 mb-2">Choose Generation Method:</p>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 class="font-semibold text-blue-900 mb-1">CadQuery (Recommended)</h4>
                            <p class="text-xs text-blue-700 mb-3">Precise parametric CAD • STEP/STL files • Fast (5-10s/part) • Editable code</p>
                            <button 
                                hx-post="/api/design/cadquery/approve-parts/{project_id}/"
                                hx-target="#parts-{project_id}"
                                hx-swap="outerHTML"
                                class="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
                                ✓ Use CadQuery
                            </button>
                        </div>
                        <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <h4 class="font-semibold text-purple-900 mb-1">Meshy-6 (Artistic)</h4>
                            <p class="text-xs text-purple-700 mb-3">Textured 3D models • Artistic style • Slow (10-20min/part) • GLB files</p>
                            <button 
                                hx-post="/api/design/approve-parts/{project_id}/"
                                hx-target="#parts-{project_id}"
                                hx-swap="outerHTML"
                                class="w-full bg-purple-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-purple-700 transition">
                                ✓ Use Meshy-6
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="flex gap-4">
                    <button 
                        hx-post="/api/design/refine-parts/{project_id}/"
                        hx-target="#parts-{project_id}"
                        hx-swap="outerHTML"
                        class="flex-1 bg-yellow-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-yellow-700 transition">
                        ↻ Refine Part Breakdown
                    </button>
                </div>
            </div>
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
            <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-2xl font-bold text-gray-800">3D Generation Started</h3>
                    <span class="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-semibold">
                        Stage 3: Generation
                    </span>
                </div>
                
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <p class="text-green-800 font-semibold">✓ Generation started for {generated_count} parts!</p>
                    <p class="text-green-700 text-sm mt-2">
                        Using Meshy-6 (latest model) for best quality. Each part will go through:
                        <br>1. Preview generation (5-10 min)
                        <br>2. Automatic refine with textures (10-15 min)
                        <br>3. Automatic GLB download
                    </p>
                </div>
                
                <div class="mb-4">
                    <p class="text-gray-700">
                        Your parts are being generated in the background. You can check progress in the 
                        <a href="/history/" class="text-purple-600 hover:underline font-semibold">History</a> page.
                    </p>
                </div>
                
                <a href="/design/projects/{project_id}/" class="inline-block bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 transition">
                    View Project Details
                </a>
            </div>
        ''')
    
    except Exception as e:
        logger.error(f"Failed to approve parts: {e}")
        return HttpResponse(f'Error: {e}', status=500)
