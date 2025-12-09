"""
URL configuration for NexaAI models app.
"""
from django.urls import path
from . import views
from . import design_views

app_name = 'models'

urlpatterns = [
    # Template views (main application)
    path('', views.home, name='home'),
    path('generate/', views.generate, name='generate'),
    path('history/', views.history, name='history'),
    path('viewer/<str:model_id>/', views.viewer, name='viewer'),
    
    # Printer management
    path('printers/', views.printers, name='printers'),
    path('printers/add/', views.printer_add, name='printer-add'),
    path('printers/edit/<str:printer_id>/', views.printer_edit, name='printer-edit'),
    
    # HTMX API endpoints
    path('api/generate', views.api_generate, name='api-generate'),
    path('api/refine-prompt', views.api_refine_prompt, name='api-refine-prompt'),
    path('api/models', views.api_models_list, name='api-models-list'),
    path('api/models/<str:model_id>/status', views.api_model_status, name='api-model-status'),
    path('api/models/<str:model_id>/glb', views.proxy_glb, name='proxy-glb'),
    path('api/models/<str:model_id>', views.api_model_delete, name='api-model-delete'),
    
    # Printer API endpoints
    path('api/printers', views.api_printers_list, name='api-printers-list'),
    path('api/printers/<str:printer_id>/mode', views.api_printer_change_mode, name='api-printer-change-mode'),
    path('api/printers/<str:printer_id>', views.api_printer_delete, name='api-printer-delete'),
    
    # Design workflow (3-stage)
    path('design/projects/', design_views.design_projects, name='design-projects'),
    path('design/projects/<str:project_id>/', design_views.design_project_detail, name='design-project-detail'),
    
    # Design workflow API endpoints
    path('api/design/create-project/', design_views.api_create_design_project, name='api-create-design-project'),
    path('api/design/approve-concept/<str:project_id>/', design_views.api_approve_concept, name='api-approve-concept'),
    path('api/design/approve-parts/<str:project_id>/', design_views.api_approve_parts, name='api-approve-parts'),
]
