"""
Overall Model Views

Handles Stage 2: Overall 3D Model generation and approval.
"""

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from models.mongodb import db, to_object_id, doc_to_dict
from models.design_schemas import PartBreakdownSchema
from services.overall_model_generator import generate_overall_model
from services.enhanced_design_analyzer import break_down_into_parts, generate_part_prompts
from models.views import session_login_required
from datetime import datetime
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@session_login_required
@require_http_methods(["POST"])
def api_generate_overall_model(request, project_id):
    """
    Generate overall 3D model from concept.
    
    POST /api/design/generate-overall-model/<project_id>/
    """
    try:
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return HttpResponse('Project not found', status=404)
        
        # Get concept
        concept = db.design_concepts.find_one({'project_id': to_object_id(project_id)})
        if not concept:
            return HttpResponse('Concept not found', status=404)
        
        # Create output directory
        output_dir = Path(settings.MEDIA_ROOT) / "cadquery_models" / f"project_{project_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating overall model for project {project_id}")
        
        # Generate overall model
        result = generate_overall_model(
            concept=concept,
            output_dir=str(output_dir),
            model_id="overall_model"
        )
        
        if not result['success']:
            # Update project with error
            db.design_projects.update_one(
                {'_id': to_object_id(project_id)},
                {'$set': {
                    'status': 'failed',
                    'updated_at': datetime.utcnow()
                }}
            )
            
            error_msg = result.get('error', 'Unknown error')
            return HttpResponse(f'''
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    <p class="font-semibold">✗ Overall model generation failed</p>
                    <p class="text-sm mt-1">{error_msg}</p>
                    <button 
                        hx-post="/api/design/generate-overall-model/{project_id}/"
                        hx-target="#overall-model-result"
                        hx-swap="innerHTML"
                        class="mt-3 bg-purple-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-purple-700 transition text-sm">
                        🔄 Retry Generation
                    </button>
                </div>
            ''', status=500)
        
        # Update project with model data
        media_root = str(Path(settings.MEDIA_ROOT))
        step_url = result['step_file'].replace(media_root, '/media').replace('\\\\', '/')
        stl_url = result['stl_file'].replace(media_root, '/media').replace('\\\\', '/')
        
        db.design_projects.update_one(
            {'_id': to_object_id(project_id)},
            {'$set': {
                'overall_model_code': result['code'],
                'overall_model_step_path': result['step_file'],
                'overall_model_stl_path': result['stl_file'],
                'status': 'pending',
                'updated_at': datetime.utcnow()
            }}
        )
        
        logger.info(f"✓ Overall model generated successfully for project {project_id}")
        
        # Return success HTML with download links and approve button
        return HttpResponse(f'''
            <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                <p class="text-green-800 font-semibold mb-2">✓ Overall model generated successfully!</p>
                <p class="text-sm text-gray-700 mb-4">Review the complete design before breaking it into parts.</p>
                
                <div class="flex gap-2 mb-4">
                    <a href="{step_url}" download class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold">
                        📥 Download STEP
                    </a>
                    <a href="{stl_url}" download class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-semibold">
                        📥 Download STL
                    </a>
                </div>
                
                <details class="mb-4">
                    <summary class="cursor-pointer text-gray-600 hover:text-gray-800 font-semibold text-sm">View Generated Code</summary>
                    <pre class="mt-2 bg-gray-800 text-green-400 p-3 rounded overflow-x-auto text-xs">{result['code']}</pre>
                </details>
                
                <div class="flex gap-2">
                    <button 
                        hx-post="/api/design/approve-overall-model/{project_id}/"
                        hx-target="#overall-model-result"
                        hx-swap="innerHTML"
                        class="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition">
                        ✓ Approve & Break Into Parts
                    </button>
                    <button 
                        hx-post="/api/design/generate-overall-model/{project_id}/"
                        hx-target="#overall-model-result"
                        hx-swap="innerHTML"
                        class="bg-yellow-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-yellow-700 transition">
                        🔄 Regenerate
                    </button>
                </div>
            </div>
        ''')
    
    except Exception as e:
        logger.error(f"Overall model generation failed: {e}", exc_info=True)
        return HttpResponse(f'Error: {e}', status=500)


@session_login_required
@require_http_methods(["POST"])
def api_approve_overall_model(request, project_id):
    """
    Approve overall model and move to part breakdown.
    
    POST /api/design/approve-overall-model/<project_id>/
    """
    try:
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return HttpResponse('Project not found', status=404)
        
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
                'overall_model_approved_at': datetime.utcnow(),
                'total_parts': len(parts_list),
                'status': 'pending',
                'updated_at': datetime.utcnow()
            }}
        )
        
        logger.info(f"✓ Overall model approved, generated {len(parts_list)} parts")
        
        # Redirect to project page to show parts
        return HttpResponse(f'''
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                <p class="font-semibold">✓ Overall model approved!</p>
                <p class="text-sm">Generated {len(parts_list)} parts. Redirecting...</p>
            </div>
            <script>
                setTimeout(function() {{
                    window.location.href = '/design/projects/{project_id}/';
                }}, 1000);
            </script>
        ''')
    
    except Exception as e:
        logger.error(f"Failed to approve overall model: {e}", exc_info=True)
        return HttpResponse(f'Error: {e}', status=500)
