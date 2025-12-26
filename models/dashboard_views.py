from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    """
    Main dashboard view - home automation hub
    """
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)
