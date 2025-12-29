"""
URL configuration for NexaAI models app.
"""
from django.urls import path
from . import views
from . import design_views
from . import cadquery_views
from . import print_job_views
from . import overall_model_views
from . import feedback_views
from . import dashboard_views
from . import home_automation_views
from . import printer_dashboard_views
from . import cad_dashboard_views
from . import dashboard_manager_views
from . import ledvance_views

app_name = 'models'

urlpatterns = [
    # Template views (main application)
    path('', dashboard_views.dashboard, name='home'),
    path('dashboard/', dashboard_views.dashboard, name='dashboard'),
    path('dashboard/<str:dashboard_id>/', dashboard_views.dashboard, name='dashboard_view'),
    path('lights/', ledvance_views.lights_management, name='lights-management'),
    
    # Dashboard Management API
    path('api/dashboards/', dashboard_manager_views.api_get_dashboards, name='api_get_dashboards'),
    path('api/dashboards/create/', dashboard_manager_views.api_create_dashboard, name='api_create_dashboard'),
    path('api/dashboards/<str:dashboard_id>/update/', dashboard_manager_views.api_update_dashboard, name='api_update_dashboard'),
    path('api/dashboards/<str:dashboard_id>/delete/', dashboard_manager_views.api_delete_dashboard, name='api_delete_dashboard'),
    path('api/dashboards/<str:dashboard_id>/set-default/', dashboard_manager_views.api_set_default_dashboard, name='api_set_default_dashboard'),
    path('api/dashboards/<str:dashboard_id>/layout/', dashboard_manager_views.api_get_dashboard_layout, name='api_get_dashboard_layout'),
    path('api/dashboards/<str:dashboard_id>/save-layout/', dashboard_manager_views.api_save_dashboard_layout, name='api_save_dashboard_layout'),
    
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
    path('api/design/generate-overall-model/<str:project_id>/', overall_model_views.api_generate_overall_model, name='api-generate-overall-model'),
    path('api/design/approve-overall-model/<str:project_id>/', overall_model_views.api_approve_overall_model, name='api-approve-overall-model'),
    path('api/design/approve-parts/<str:project_id>/', cadquery_views.api_approve_parts_cadquery, name='api-approve-parts'),
    path('api/design/generate/<str:project_id>/<int:part_number>/', cadquery_views.api_generate_part_cadquery, name='api-generate-part'),
    
    # Feedback endpoints
    path('api/design/feedback/<str:project_id>/', feedback_views.submit_feedback, name='api-submit-feedback'),
    
    # Print job endpoints
    path('api/design/send-to-printer/<str:project_id>/<int:part_number>/', print_job_views.api_send_to_printer, name='api-send-to-printer'),
    path('api/printers/<str:printer_id>/status/', print_job_views.api_get_printer_status, name='api-printer-status'),
    
    # Ledvance Smart Lights API endpoints
    path('api/ledvance/lights/', ledvance_views.api_list_lights, name='api-ledvance-list-lights'),
    path('api/ledvance/lights/add/', ledvance_views.api_add_light, name='api-ledvance-add-light'),
    path('api/ledvance/scan/', ledvance_views.api_scan_network, name='api-ledvance-scan'),
    path('api/ledvance/lights/<str:light_id>/remove/', ledvance_views.api_remove_light, name='api-ledvance-remove-light'),
    path('api/ledvance/lights/<str:light_id>/toggle/', ledvance_views.api_toggle_light, name='api-ledvance-toggle-light'),
    path('api/ledvance/lights/<str:light_id>/brightness/', ledvance_views.api_set_light_brightness, name='api-ledvance-set-brightness'),
    path('api/ledvance/lights/<str:light_id>/color/', ledvance_views.api_set_light_color, name='api-ledvance-set-color'),
    path('api/ledvance/lights/<str:light_id>/temperature/', ledvance_views.api_set_light_temperature, name='api-ledvance-set-temperature'),
    path('api/ledvance/groups/', ledvance_views.api_list_groups, name='api-ledvance-list-groups'),
    path('api/ledvance/groups/create/', ledvance_views.api_create_group, name='api-ledvance-create-group'),
    path('api/ledvance/groups/<str:group_id>/update/', ledvance_views.api_update_group, name='api-ledvance-update-group'),
    path('api/ledvance/groups/<str:group_id>/delete/', ledvance_views.api_delete_group, name='api-ledvance-delete-group'),
    path('api/ledvance/groups/<str:group_id>/toggle/', ledvance_views.api_toggle_group, name='api-ledvance-toggle-group'),
    path('api/ledvance/groups/<str:group_id>/on/', ledvance_views.api_turn_on_group, name='api-ledvance-turn-on-group'),
    path('api/ledvance/groups/<str:group_id>/off/', ledvance_views.api_turn_off_group, name='api-ledvance-turn-off-group'),
    path('api/ledvance/groups/<str:group_id>/brightness/', ledvance_views.api_set_group_brightness, name='api-ledvance-set-group-brightness'),
    path('api/ledvance/groups/<str:group_id>/color/', ledvance_views.api_set_group_color, name='api-ledvance-set-group-color'),
    
    # Home Automation API endpoints (Mock Data)
    path('api/home/lights/', home_automation_views.api_get_lights, name='api-get-lights'),
    path('api/home/lights/<str:light_id>/', home_automation_views.api_toggle_light, name='api-toggle-light'),
    path('api/home/climate/', home_automation_views.api_get_climate, name='api-get-climate'),
    path('api/home/climate/set/', home_automation_views.api_set_climate, name='api-set-climate'),
    path('api/home/devices/', home_automation_views.api_get_devices, name='api-get-devices'),
    path('api/home/devices/<str:device_id>/', home_automation_views.api_toggle_device, name='api-toggle-device'),
    
    # 3D Printer Dashboard API endpoints
    path('api/printers/all/', printer_dashboard_views.api_get_printers, name='api-get-all-printers'),
    path('api/printers/<str:printer_id>/status/', printer_dashboard_views.api_get_printer_status, name='api-get-printer-status-dash'),
    path('api/printers/<str:printer_id>/files/', printer_dashboard_views.api_get_printer_files, name='api-get-printer-files'),
    path('api/printers/<str:printer_id>/start/', printer_dashboard_views.api_start_print, name='api-start-print'),
    path('api/printers/<str:printer_id>/pause/', printer_dashboard_views.api_pause_print, name='api-pause-print'),
    path('api/printers/<str:printer_id>/resume/', printer_dashboard_views.api_resume_print, name='api-resume-print'),
    path('api/printers/<str:printer_id>/cancel/', printer_dashboard_views.api_cancel_print, name='api-cancel-print'),
    path('api/printers/<str:printer_id>/temperature/', printer_dashboard_views.api_set_temperature, name='api-set-temperature'),
    path('api/print-job/', printer_dashboard_views.api_get_print_job, name='api-get-print-job'),
    
    # CAD AI Dashboard API endpoints
    path('api/cad/recent-projects/', cad_dashboard_views.api_get_recent_projects, name='api-get-recent-projects'),
    path('api/cad/stats/', cad_dashboard_views.api_get_project_stats, name='api-get-project-stats'),
]
