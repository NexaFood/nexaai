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


class Printer(models.Model):
    """
    3D Printer information and configuration.
    Supports Prusa (3D print only) and Snapmaker (multi-mode).
    """
    PRINTER_TYPES = [
        ('prusa', 'Prusa'),
        ('snapmaker', 'Snapmaker'),
    ]
    
    SNAPMAKER_MODES = [
        ('3d_print', '3D Printing'),
        ('cnc', 'CNC Milling'),
        ('laser', 'Laser Engraving'),
    ]
    
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('printing', 'Printing'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='printers')
    
    # Basic info
    name = models.CharField(max_length=100)
    printer_type = models.CharField(max_length=20, choices=PRINTER_TYPES)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    
    # Network info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Build volume (in mm)
    build_volume_x = models.IntegerField(help_text="Build volume X dimension in mm")
    build_volume_y = models.IntegerField(help_text="Build volume Y dimension in mm")
    build_volume_z = models.IntegerField(help_text="Build volume Z dimension in mm")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    
    # Snapmaker-specific: current mode
    current_mode = models.CharField(
        max_length=20, 
        choices=SNAPMAKER_MODES, 
        null=True, 
        blank=True,
        help_text="Only for Snapmaker printers"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_online = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'printers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'printer_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.model})"
    
    def can_print_3d(self):
        """Check if printer can currently print 3D models."""
        if self.printer_type == 'prusa':
            return True
        elif self.printer_type == 'snapmaker':
            return self.current_mode == '3d_print'
        return False
    
    def get_build_volume(self):
        """Return build volume as tuple (x, y, z) in mm."""
        return (self.build_volume_x, self.build_volume_y, self.build_volume_z)


class PrintJob(models.Model):
    """
    Print job history and tracking.
    Links 3D models to printers and tracks print status.
    """
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('printing', 'Printing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='print_jobs')
    model = models.ForeignKey(Model3D, on_delete=models.CASCADE, related_name='print_jobs')
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name='print_jobs')
    
    # Job info
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    notes = models.TextField(null=True, blank=True)
    
    # Print settings
    material = models.CharField(max_length=50, null=True, blank=True, help_text="e.g., PLA, ABS, PETG")
    layer_height = models.FloatField(null=True, blank=True, help_text="Layer height in mm")
    infill_percentage = models.IntegerField(null=True, blank=True, help_text="Infill percentage 0-100")
    
    # Time tracking
    estimated_duration = models.IntegerField(null=True, blank=True, help_text="Estimated duration in minutes")
    actual_duration = models.IntegerField(null=True, blank=True, help_text="Actual duration in minutes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'print_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['printer', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Print Job #{self.id} - {self.model.prompt[:30]} on {self.printer.name}"
