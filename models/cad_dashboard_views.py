"""
CAD AI Dashboard API Views
Integration with existing CAD AI system
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .mongodb import db, to_object_id


@login_required
@require_http_methods(["GET"])
def api_get_recent_projects(request):
    """Get recent CAD projects for dashboard widget"""
    try:
        # Get user's recent projects
        projects = list(db.design_projects.find(
            {'user_id': str(request.user.id)}
        ).sort('created_at', -1).limit(5))
        
        project_list = []
        for project in projects:
            project_data = {
                'id': str(project['_id']),
                'description': project.get('description', ''),
                'status': project.get('status', 'unknown'),
                'created_at': project.get('created_at', '').isoformat() if project.get('created_at') else '',
                'has_overall_model': bool(project.get('overall_model_stl')),
            }
            project_list.append(project_data)
        
        return JsonResponse({
            'success': True,
            'projects': project_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def api_get_project_stats(request):
    """Get CAD project statistics for dashboard"""
    try:
        total_projects = db.design_projects.count_documents({'user_id': str(request.user.id)})
        completed_projects = db.design_projects.count_documents({
            'user_id': str(request.user.id),
            'status': 'completed'
        })
        in_progress_projects = db.design_projects.count_documents({
            'user_id': str(request.user.id),
            'status': {'$in': ['concept_approved', 'overall_approved', 'parts_generated']}
        })
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total': total_projects,
                'completed': completed_projects,
                'in_progress': in_progress_projects
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
