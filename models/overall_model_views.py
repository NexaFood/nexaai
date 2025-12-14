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
            error_msg = result.get('error', 'Unknown error')
            failed_code = result.get('code', '')  # May have partial code
            
            # Read the actual executed script file
            script_path = result.get('script_path')
            actual_script = ""
            if script_path and Path(script_path).exists():
                actual_script = Path(script_path).read_text()
            else:
                actual_script = failed_code  # Fallback to generated code
            
            # Save both AI code and script path to database
            db.design_projects.update_one(
                {'_id': to_object_id(project_id)},
                {'$set': {
                    'overall_model_ai_code': failed_code,  # Just AI-generated code
                    'overall_model_script_path': script_path,  # Path to full script
                    'overall_model_error': error_msg,
                    'overall_model_success': False,  # Track if generation succeeded
                    'status': 'failed',
                    'updated_at': datetime.utcnow()
                }}
            )
            
            return HttpResponse(f'''
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    <p class="font-semibold">✗ Overall model generation failed</p>
                    <p class="text-sm mt-1">{error_msg}</p>
                    
                    {f'''<div class="mt-3 border-t border-red-300 pt-3">
                        <p class="text-sm font-semibold mb-2">📄 Executed Script (overall_model_script.py):</p>
                        <pre class="bg-gray-900 text-yellow-300 p-3 rounded text-xs overflow-x-auto max-h-60 overflow-y-auto">{actual_script}</pre>
                    </div>''' if actual_script else '<p class="text-sm mt-2 italic">No code was generated.</p>'}
                    
                    <div class="mt-4 border-t border-red-300 pt-3">
                        <p class="text-sm font-semibold mb-2">📊 Help improve the AI:</p>
                        <button 
                            onclick="submitFeedback('{project_id}', 'overall_model', 'bad')"
                            class="mr-2 px-3 py-1 bg-red-200 text-red-800 rounded hover:bg-red-300 transition text-sm font-semibold">
                            ❌ Report Failure
                        </button>
                        
                        <details class="mt-3" open>
                            <summary class="cursor-pointer text-sm text-blue-600 hover:text-blue-700 font-semibold">✏️ Fix the code and submit correction</summary>
                            <div class="mt-2 p-3 bg-blue-50 rounded">
                                <p class="text-xs text-gray-600 mb-2">Edit the code below to fix it, then submit:</p>
                                <textarea 
                                    id="correction-overall_model-{project_id}"
                                    class="w-full h-64 p-2 border rounded font-mono text-xs"
                                    placeholder="import cadquery as cq\n\nresult = ...">{actual_script if actual_script else 'import cadquery as cq\n\nresult = '}</textarea>
                                <button 
                                    onclick="submitCorrection('{project_id}', 'overall_model')"
                                    class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold">
                                    Submit Correction
                                </button>
                            </div>
                        </details>
                    </div>
                    
                    <button 
                        hx-post="/api/design/generate-overall-model/{project_id}/"
                        hx-target="#overall-model-result"
                        hx-swap="innerHTML"
                        class="mt-3 bg-purple-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-purple-700 transition text-sm">
                        🔄 Retry Generation
                    </button>
                </div>
            ''')  # Return 200 so HTMX displays the error HTML
        
        # Update project with model data
        media_root = str(Path(settings.MEDIA_ROOT))
        step_url = result['step_file'].replace(media_root, '/media').replace('\\\\', '/')
        stl_url = result['stl_file'].replace(media_root, '/media').replace('\\\\', '/')
        
        db.design_projects.update_one(
            {'_id': to_object_id(project_id)},
            {'$set': {
                'overall_model_ai_code': result['code'],  # Just AI-generated code
                'overall_model_script_path': result.get('script_path'),  # Path to full script
                'overall_model_step_path': result['step_file'],
                'overall_model_stl_path': result['stl_file'],
                'overall_model_success': True,  # Track if generation succeeded
                'status': 'pending',
                'updated_at': datetime.utcnow()
            }}
        )
        
        logger.info(f"✓ Overall model generated successfully for project {project_id}")
        
        # Read the actual executed script file
        script_path = result.get('script_path')
        actual_script = ""
        
        logger.info(f"Script path from result: {script_path}")
        
        if script_path:
            script_file_path = Path(script_path)
            logger.info(f"Checking if script exists: {script_file_path.exists()}")
            if script_file_path.exists():
                actual_script = script_file_path.read_text()
                logger.info(f"Read {len(actual_script)} characters from script file")
            else:
                logger.warning(f"Script file not found at {script_path}, using generated code")
                actual_script = result.get('code', 'No code available')
        else:
            logger.warning("No script_path in result, using generated code")
            actual_script = result.get('code', 'No code available')
        
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
                
                <details class="mb-4" open>
                    <summary class="cursor-pointer text-gray-600 hover:text-gray-800 font-semibold text-sm">📄 View Executed Script (overall_model_script.py)</summary>
                    <pre class="mt-2 bg-gray-900 text-green-300 p-4 rounded overflow-x-auto text-xs max-h-96 overflow-y-auto">{actual_script}</pre>
                </details>
                
                <div class="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <p class="text-sm font-semibold mb-2">📊 Help improve the AI:</p>
                    <div class="flex gap-2 mb-3">
                        <button 
                            onclick="submitFeedback('{project_id}', 'overall_model', 'good')"
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-semibold">
                            ✅ Perfect!
                        </button>
                        <button 
                            onclick="submitFeedback('{project_id}', 'overall_model', 'needs_work')"
                            class="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm font-semibold">
                            ⚠️ Needs Work
                        </button>
                        <button 
                            onclick="submitFeedback('{project_id}', 'overall_model', 'bad')"
                            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-semibold">
                            ❌ Failed
                        </button>
                    </div>
                    
                    <details class="mt-3">
                        <summary class="cursor-pointer text-sm text-blue-600 hover:text-blue-700 font-semibold">✏️ I can improve this code</summary>
                        <div class="mt-2 p-3 bg-blue-50 rounded">
                            <p class="text-xs text-gray-600 mb-2">Edit the code below to improve it, then submit:</p>
                            <textarea 
                                id="correction-overall_model-{project_id}"
                                class="w-full h-64 p-2 border rounded font-mono text-xs"
                                placeholder="import cadquery as cq\n\nresult = ...">{actual_script}</textarea>
                            <button 
                                onclick="submitCorrection('{project_id}', 'overall_model')"
                                class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold">
                                Submit Correction
                            </button>
                        </div>
                    </details>
                </div>
                
                <div class="flex gap-2 mt-4">
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
