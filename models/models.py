"""
Django models for NexaAI - 3D Model Generation Platform.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Stores user authentication and profile information.
    """
    open_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=[('user', 'User'), ('admin', 'Admin')],
        default='user'
    )
    last_signed_in = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.username or self.email


class Model3D(models.Model):
    """
    3D Model metadata and generation information.
    Stores information about generated 3D models.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='models')
    
    # Prompt and generation settings
    prompt = models.TextField()
    refined_prompt = models.TextField(null=True, blank=True)
    art_style = models.CharField(max_length=50, null=True, blank=True)
    quality = models.CharField(max_length=20, default='preview')
    polygon_count = models.IntegerField(default=30000)
    
    # Generation status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(null=True, blank=True)
    
    # File URLs (stored in S3 or Meshy CDN)
    glb_url = models.URLField(max_length=500, null=True, blank=True)
    obj_url = models.URLField(max_length=500, null=True, blank=True)
    fbx_url = models.URLField(max_length=500, null=True, blank=True)
    usdz_url = models.URLField(max_length=500, null=True, blank=True)
    thumbnail_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'models_3d'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.prompt[:50]}... ({self.status})"


class GenerationJob(models.Model):
    """
    Tracks the status of a 3D model generation job with Meshy.ai.
    Links to Model3D and stores Meshy API task information.
    """
    model = models.OneToOneField(Model3D, on_delete=models.CASCADE, related_name='generation_job')
    
    # Meshy.ai task information
    meshy_task_id = models.CharField(max_length=100, unique=True)
    meshy_status = models.CharField(max_length=50)
    meshy_response = models.JSONField(default=dict)
    
    # Progress tracking
    progress = models.IntegerField(default=0)  # 0-100
    last_checked_at = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'generation_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meshy_task_id']),
            models.Index(fields=['meshy_status']),
        ]
    
    def __str__(self):
        return f"Job {self.meshy_task_id} - {self.meshy_status}"
