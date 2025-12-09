"""
URL configuration for NexaAI models app.
"""
from django.urls import path
from . import views
from . import design_views
from . import cadquery_views

app_name = 'models'

urlpatterns = [
    # Template views (main application)
    path('', views.home, name='home'),
    
    # Printer management
    path('printers/', views.printers, name='printers'),
    path('printers/add/', views.printer_add, name='printer-add'),
    path('printers/edit/<str:printer_id>/', views.printer_edit, name='printer-edit'),
    
    # Printer API endpoints
    path('api/printers', views.api_printers_list, name='api-printers-list'),
    path('api/printers/<str:printer_id>/mode', views.api_printer_change_mode, name='api-printer-change-mode'),
    path('api/printers/<str:printer_id>', views.api_printer_delete, name='api-printer-delete'),
    
    # Design workflow (3-stage) - Main CAD generation interface
    path('design/projects/', design_views.design_projects, name='design-projects'),
    path('design/projects/<str:project_id>/', design_views.design_project_detail, name='design-project-detail'),
    
    # Design workflow API endpoints
    path('api/design/create-project/', design_views.api_create_design_project, name='api-create-design-project'),
    path('api/design/approve-concept/<str:project_id>/', design_views.api_approve_concept, name='api-approve-concept'),
    path('api/design/approve-parts/<str:project_id>/', cadquery_views.api_approve_parts_cadquery, name='api-approve-parts'),
    path('api/design/generate/<str:project_id>/<int:part_number>/', cadquery_views.api_generate_part_cadquery, name='api-generate-part'),
]
