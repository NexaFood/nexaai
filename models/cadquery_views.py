"""
Views for CadQuery-based CAD generation workflow.
Replaces Meshy API with local CadQuery generation for precise parametric CAD.
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from models.mongodb import db, to_object_id, doc_to_dict
from models.design_schemas import PartSchema
from models.views import session_login_required
from services.cadquery_agent import CadQueryAgent
from services.cadquery_executor import CadQueryExecutor
from datetime import datetime
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)


@session_login_required
@require_http_methods(["POST"])
def api_generate_part_cadquery(request, project_id, part_number):
    """
    HTMX endpoint to generate a single part using CadQuery.
    This replaces Meshy API for precise parametric CAD generation.
    """
    try:
        # Get project and part breakdown
        project = db.design_projects.find_one({
            '_id': to_object_id(project_id),
            'user_id': str(request.user.id)
        })
        
        if not project:
            return HttpResponse('Project not found', status=404)
        
        breakdown = db.part_breakdowns.find_one({'project_id': to_object_id(project_id)})
        if not breakdown:
            return HttpResponse('Part breakdown not found', status=404)
        
        # Find the specific part
        part = None
        for p in breakdown['parts']:
            if p['part_number'] == int(part_number):
                part = p
                break
        
        if not part:
            return HttpResponse('Part not found', status=404)
        
        # Update part status to generating
        db.part_breakdowns.update_one(
            {'project_id': to_object_id(project_id), 'parts.part_number': int(part_number)},
            {'$set': {'parts.$.status': 'generating'}}
        )
        
        # Generate CadQuery code using AI
        logger.info(f"Generating CadQuery code for part {part_number}: {part['name']}")
        agent = CadQueryAgent()
        
        # Build description from part data
        description = f"{part['description']}. "
        if part.get('estimated_dimensions'):
            dims = part['estimated_dimensions']
            description += f"Approximate dimensions: {dims.get('x', 'auto')}mm x {dims.get('y', 'auto')}mm x {dims.get('z', 'auto')}mm. "
        if part.get('material_recommendation'):
            description += f"Material: {part['material_recommendation']}. "
        if part.get('notes'):
            description += part['notes']
        
        code_result = agent.generate_code(description)
        
        if not code_result or 'code' not in code_result:
            # Update part with error
            error_msg = 'Failed to generate CadQuery code'
            db.part_breakdowns.update_one(
                {'project_id': to_object_id(project_id), 'parts.part_number': int(part_number)},
                {'$set': {
                    'parts.$.status': 'failed',
                    'parts.$.generation_error': error_msg
                }}
            )
            return HttpResponse(f"Failed to generate code: {error_msg}", status=500)
        
        # Execute the code and export files
        logger.info(f"Executing CadQuery code for part {part_number}")
        
        # Create output directory for this project (cross-platform)
        output_dir = Path(settings.MEDIA_ROOT) / "cadquery_models" / f"project_{project_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir = str(output_dir)  # Convert back to string for compatibility
        
        # Generate model_id based on part name
        safe_name = part['name'].lower().replace(' ', '_').replace('-', '_')
        model_id = f"part_{part_number}_{safe_name}"
        
        # Initialize executor with project-specific output directory
        executor = CadQueryExecutor(output_dir=output_dir)
        
        exec_result = executor.execute_code(
            code_result['code'],
            model_id=model_id,
            export_formats=["step", "stl"]
        )
        
        if not exec_result['success']:
            # Update part with error
            db.part_breakdowns.update_one(
                {'project_id': to_object_id(project_id), 'parts.part_number': int(part_number)},
                {'$set': {
                    'parts.$.status': 'failed',
                    'parts.$.generation_error': exec_result.get('error', 'Unknown error')
                }}
            )
            return HttpResponse(f"Failed to execute code: {exec_result.get('error', 'Unknown error')}", status=500)
        
        # Get file paths from result
        step_file = exec_result['files'].get('step', '')
        stl_file = exec_result['files'].get('stl', '')
        
        # Update part with success data
        db.part_breakdowns.update_one(
            {'project_id': to_object_id(project_id), 'parts.part_number': int(part_number)},
            {'$set': {
                'parts.$.status': 'completed',
                'parts.$.cadquery_code': code_result['code'],
                'parts.$.step_file_path': step_file,
                'parts.$.stl_file_path': stl_file,
                'parts.$.generation_error': None
            }}
        )
        
        # Update project progress
        breakdown = db.part_breakdowns.find_one({'project_id': to_object_id(project_id)})
        completed_parts = sum(1 for p in breakdown['parts'] if p['status'] == 'completed')
        total_parts = len(breakdown['parts'])
        
        db.design_projects.update_one(
            {'_id': to_object_id(project_id)},
            {'$set': {
                'generated_parts': completed_parts,
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Check if all parts are done
        if completed_parts == total_parts:
            db.design_projects.update_one(
                {'_id': to_object_id(project_id)},
                {'$set': {
                    'stage': 'completed',
                    'status': 'completed',
                    'completed_at': datetime.utcnow()
                }}
            )
        
        # Return success HTML with download links (cross-platform)
        # Convert absolute paths to URLs
        media_root = str(Path(settings.MEDIA_ROOT))
        step_url = step_file.replace(media_root, '/media').replace('\\', '/')
        stl_url = stl_file.replace(media_root, '/media').replace('\\', '/')
        
        return HttpResponse(f'''
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <p class="text-green-800 font-semibold mb-2">✓ Part {part_number} generated successfully!</p>
                <p class="text-sm text-gray-700 mb-3">{part['name']}</p>
                
                <div class="flex gap-2 mb-3">
                    <a href="{step_url}" download class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        Download STEP
                    </a>
                    <a href="{stl_url}" download class="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700">
                        Download STL
                    </a>
                </div>
                
                <details class="text-sm">
                    <summary class="cursor-pointer text-gray-600 hover:text-gray-800 font-semibold">View Generated Code</summary>
                    <pre class="mt-2 bg-gray-800 text-green-400 p-3 rounded overflow-x-auto text-xs">{code_result['code']}</pre>
                </details>
                
                <p class="text-xs text-gray-500 mt-2">Progress: {completed_parts}/{total_parts} parts completed</p>
            </div>
        ''')
    
    except Exception as e:
        logger.error(f"CadQuery generation failed for part {part_number}: {e}")
        
        # Update part with error
        try:
            db.part_breakdowns.update_one(
                {'project_id': to_object_id(project_id), 'parts.part_number': int(part_number)},
                {'$set': {
                    'parts.$.status': 'failed',
                    'parts.$.generation_error': str(e)
                }}
            )
        except:
            pass
        
        return HttpResponse(f'Error: {e}', status=500)


@session_login_required
@require_http_methods(["POST"])
def api_approve_parts_cadquery(request, project_id):
    """
    HTMX endpoint to approve parts and start CadQuery generation for all parts.
    This is the CadQuery version of api_approve_parts.
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
                'total_parts': len(parts_list),
                'generated_parts': 0,
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Generate parts HTML with CadQuery generation buttons
        parts_html = ''.join([
            f'''
            <div class="border rounded-lg p-4 mb-3" id="part-{part['part_number']}">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-semibold text-gray-800">Part {part['part_number']}: {part['name']}</h4>
                    <span class="px-2 py-1 rounded text-xs font-semibold {'bg-purple-100 text-purple-800' if part['manufacturing_method'] == '3d_print' else 'bg-blue-100 text-blue-800'}">
                        {'3D Print' if part['manufacturing_method'] == '3d_print' else 'CNC'}
                    </span>
                </div>
                <p class="text-sm text-gray-600 mb-3">{part['description']}</p>
                <div class="text-xs text-gray-500 mb-3">
                    Material: {part['material_recommendation']} | 
                    Dimensions: {part['estimated_dimensions']['x']}×{part['estimated_dimensions']['y']}×{part['estimated_dimensions']['z']}mm
                </div>
                <div id="part-{part['part_number']}-status">
                    <button 
                        hx-post="/api/design/generate/{project_id}/{part['part_number']}/"
                        hx-target="#part-{part['part_number']}-status"
                        hx-swap="innerHTML"
                        class="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition text-sm">
                        Generate CAD Model
                    </button>
                </div>
            </div>
            '''
            for part in parts_list
        ])
        
        return HttpResponse(f'''
            <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-2xl font-bold text-gray-800">CAD Generation Ready</h3>
                    <span class="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-semibold">
                        Stage 3: Generation (CadQuery)
                    </span>
                </div>
                
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <p class="text-blue-800 font-semibold">✓ Parts approved! Ready for CAD generation.</p>
                    <p class="text-blue-700 text-sm mt-2">
                        Using CadQuery AI for precise parametric CAD generation:
                        <br>• Fast generation (5-10 seconds per part)
                        <br>• Manufacturing-ready STEP files for CAD software
                        <br>• 3D-printable STL files
                        <br>• Editable Python code for customization
                    </p>
                </div>
                
                <div class="mb-4">
                    <p class="text-gray-700 font-semibold mb-3">Click "Generate CAD Model" for each part:</p>
                    {parts_html}
                </div>
                
                <div class="text-sm text-gray-500">
                    <p>💡 Tip: You can edit the generated Python code to customize your designs!</p>
                </div>
            </div>
        ''')
    
    except Exception as e:
        logger.error(f"Failed to approve parts for CadQuery generation: {e}")
        return HttpResponse(f'Error: {e}', status=500)
