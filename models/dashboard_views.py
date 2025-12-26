from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from models.mongodb import db, to_object_id
from datetime import datetime

@login_required
def dashboard(request, dashboard_id=None):
    """
    Main dashboard view - home automation hub with multi-dashboard support
    """
    user_id = str(request.user.id)
    
    # Get or create default dashboard
    if dashboard_id:
        # Load specific dashboard
        current_dashboard = db.dashboards.find_one({
            '_id': to_object_id(dashboard_id),
            'user_id': user_id
        })
        if not current_dashboard:
            # Fallback to default
            current_dashboard = db.dashboards.find_one({
                'user_id': user_id,
                'is_default': True
            })
    else:
        # Load default dashboard
        current_dashboard = db.dashboards.find_one({
            'user_id': user_id,
            'is_default': True
        })
    
    # Create default dashboard if none exists
    if not current_dashboard:
        current_dashboard = {
            'user_id': user_id,
            'name': 'Main Dashboard',
            'room': 'Home',
            'icon': '🏠',
            'is_default': True,
            'widgets': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = db.dashboards.insert_one(current_dashboard)
        current_dashboard['_id'] = result.inserted_id
    
    context = {
        'user': request.user,
        'dashboard_id': str(current_dashboard['_id']),
        'dashboard_name': current_dashboard.get('name', 'Dashboard'),
        'dashboard_icon': current_dashboard.get('icon', '🏠')
    }
    return render(request, 'dashboard.html', context)
