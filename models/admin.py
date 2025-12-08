"""
Django admin configuration for NexaAI models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Model3D, GenerationJob


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    list_display = ['username', 'email', 'role', 'is_staff', 'last_signed_in']
    list_filter = ['role', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('open_id', 'role', 'last_signed_in')}),
    )


@admin.register(Model3D)
class Model3DAdmin(admin.ModelAdmin):
    """Admin interface for Model3D."""
    list_display = ['id', 'user', 'prompt_preview', 'status', 'quality', 'created_at']
    list_filter = ['status', 'quality', 'art_style']
    search_fields = ['prompt', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    def prompt_preview(self, obj):
        return obj.prompt[:50] + '...' if len(obj.prompt) > 50 else obj.prompt
    prompt_preview.short_description = 'Prompt'


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    """Admin interface for GenerationJob."""
    list_display = ['id', 'model', 'meshy_task_id', 'meshy_status', 'progress', 'last_checked_at']
    list_filter = ['meshy_status']
    search_fields = ['meshy_task_id', 'model__prompt']
    readonly_fields = ['created_at', 'updated_at', 'last_checked_at']
