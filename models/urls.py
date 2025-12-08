"""
URL configuration for NexaAI models app.
"""
from django.urls import path
from . import views

app_name = 'models'

urlpatterns = [
    # Template views (main application)
    path('', views.home, name='home'),
    path('generate/', views.generate, name='generate'),
    path('history/', views.history, name='history'),
    path('viewer/<int:model_id>/', views.viewer, name='viewer'),
    
    # HTMX API endpoints
    path('api/generate', views.api_generate, name='api-generate'),
    path('api/refine-prompt', views.api_refine_prompt, name='api-refine-prompt'),
    path('api/models', views.api_models_list, name='api-models-list'),
    path('api/models/<int:model_id>/status', views.api_model_status, name='api-model-status'),
    path('api/models/<int:model_id>', views.api_model_delete, name='api-model-delete'),
]
