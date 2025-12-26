"""
Dashboard Manager Views
Handles creating, editing, and switching between room-specific dashboards
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from models.mongodb import db, to_object_id
from models.views import session_login_required
from datetime import datetime
import json


@session_login_required
@require_http_methods(["GET"])
def api_get_dashboards(request):
    """Get all dashboards for the current user"""
    try:
        user_id = str(request.user.id)
        
        # Get all dashboards for this user
        dashboards = list(db.dashboards.find(
            {'user_id': user_id}
        ).sort('is_default', -1).sort('name', 1))
        
        # Convert to JSON-serializable format
        dashboard_list = []
        for dashboard in dashboards:
            dashboard_list.append({
                'id': str(dashboard['_id']),
                'name': dashboard['name'],
                'room': dashboard.get('room', ''),
                'icon': dashboard.get('icon', '🏠'),
                'is_default': dashboard.get('is_default', False),
                'widget_count': len(dashboard.get('widgets', [])),
                'created_at': dashboard.get('created_at', '').isoformat() if dashboard.get('created_at') else '',
                'updated_at': dashboard.get('updated_at', '').isoformat() if dashboard.get('updated_at') else ''
            })
        
        return JsonResponse({
            'success': True,
            'dashboards': dashboard_list
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_create_dashboard(request):
    """Create a new dashboard"""
    try:
        user_id = str(request.user.id)
        
        # Get form data
        name = request.POST.get('name', '').strip()
        room = request.POST.get('room', '').strip()
        icon = request.POST.get('icon', '🏠')
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Dashboard name is required'
            }, status=400)
        
        # Check if this is the first dashboard for this user
        existing_count = db.dashboards.count_documents({'user_id': user_id})
        is_default = existing_count == 0
        
        # Create dashboard
        dashboard = {
            'user_id': user_id,
            'name': name,
            'room': room,
            'icon': icon,
            'is_default': is_default,
            'widgets': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.dashboards.insert_one(dashboard)
        dashboard['_id'] = result.inserted_id
        
        return JsonResponse({
            'success': True,
            'dashboard': {
                'id': str(dashboard['_id']),
                'name': dashboard['name'],
                'room': dashboard['room'],
                'icon': dashboard['icon'],
                'is_default': dashboard['is_default']
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_update_dashboard(request, dashboard_id):
    """Update dashboard settings"""
    try:
        user_id = str(request.user.id)
        
        # Verify ownership
        dashboard = db.dashboards.find_one({
            '_id': to_object_id(dashboard_id),
            'user_id': user_id
        })
        
        if not dashboard:
            return JsonResponse({
                'success': False,
                'error': 'Dashboard not found'
            }, status=404)
        
        # Get update data
        name = request.POST.get('name', '').strip()
        room = request.POST.get('room', '').strip()
        icon = request.POST.get('icon', dashboard.get('icon', '🏠'))
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Dashboard name is required'
            }, status=400)
        
        # Update dashboard
        db.dashboards.update_one(
            {'_id': to_object_id(dashboard_id)},
            {'$set': {
                'name': name,
                'room': room,
                'icon': icon,
                'updated_at': datetime.utcnow()
            }}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Dashboard updated successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_delete_dashboard(request, dashboard_id):
    """Delete a dashboard"""
    try:
        user_id = str(request.user.id)
        
        # Verify ownership
        dashboard = db.dashboards.find_one({
            '_id': to_object_id(dashboard_id),
            'user_id': user_id
        })
        
        if not dashboard:
            return JsonResponse({
                'success': False,
                'error': 'Dashboard not found'
            }, status=404)
        
        # Don't allow deleting the last dashboard
        dashboard_count = db.dashboards.count_documents({'user_id': user_id})
        if dashboard_count <= 1:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete the last dashboard'
            }, status=400)
        
        # If this was the default, make another one default
        if dashboard.get('is_default'):
            other_dashboard = db.dashboards.find_one({
                'user_id': user_id,
                '_id': {'$ne': to_object_id(dashboard_id)}
            })
            if other_dashboard:
                db.dashboards.update_one(
                    {'_id': other_dashboard['_id']},
                    {'$set': {'is_default': True}}
                )
        
        # Delete dashboard
        db.dashboards.delete_one({'_id': to_object_id(dashboard_id)})
        
        return JsonResponse({
            'success': True,
            'message': 'Dashboard deleted successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_set_default_dashboard(request, dashboard_id):
    """Set a dashboard as the default"""
    try:
        user_id = str(request.user.id)
        
        # Verify ownership
        dashboard = db.dashboards.find_one({
            '_id': to_object_id(dashboard_id),
            'user_id': user_id
        })
        
        if not dashboard:
            return JsonResponse({
                'success': False,
                'error': 'Dashboard not found'
            }, status=404)
        
        # Unset all other defaults
        db.dashboards.update_many(
            {'user_id': user_id},
            {'$set': {'is_default': False}}
        )
        
        # Set this one as default
        db.dashboards.update_one(
            {'_id': to_object_id(dashboard_id)},
            {'$set': {'is_default': True}}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Default dashboard updated'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["GET"])
def api_get_dashboard_layout(request, dashboard_id):
    """Get widget layout for a specific dashboard"""
    try:
        user_id = str(request.user.id)
        
        # Verify ownership
        dashboard = db.dashboards.find_one({
            '_id': to_object_id(dashboard_id),
            'user_id': user_id
        })
        
        if not dashboard:
            return JsonResponse({
                'success': False,
                'error': 'Dashboard not found'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'widgets': dashboard.get('widgets', [])
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@session_login_required
@require_http_methods(["POST"])
def api_save_dashboard_layout(request, dashboard_id):
    """Save widget layout for a specific dashboard"""
    try:
        user_id = str(request.user.id)
        
        # Verify ownership
        dashboard = db.dashboards.find_one({
            '_id': to_object_id(dashboard_id),
            'user_id': user_id
        })
        
        if not dashboard:
            return JsonResponse({
                'success': False,
                'error': 'Dashboard not found'
            }, status=404)
        
        # Get widget data
        widgets_json = request.POST.get('widgets', '[]')
        widgets = json.loads(widgets_json)
        
        # Update dashboard
        db.dashboards.update_one(
            {'_id': to_object_id(dashboard_id)},
            {'$set': {
                'widgets': widgets,
                'updated_at': datetime.utcnow()
            }}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Layout saved successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
