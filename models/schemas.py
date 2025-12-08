"""
MongoDB document schemas and helper functions.
Defines the structure of documents stored in MongoDB collections.
"""
from datetime import datetime
from bson import ObjectId


class Model3DSchema:
    """Schema for 3D model documents."""
    
    @staticmethod
    def create(user_id, prompt, **kwargs):
        """Create a new 3D model document."""
        return {
            'user_id': str(user_id),  # Store as string for MongoDB users
            'prompt': prompt,
            'refined_prompt': kwargs.get('refined_prompt'),
            'art_style': kwargs.get('art_style'),
            'quality': kwargs.get('quality', 'preview'),
            'polygon_count': kwargs.get('polygon_count', 30000),
            'status': kwargs.get('status', 'pending'),
            'error_message': None,
            'glb_url': None,
            'obj_url': None,
            'fbx_url': None,
            'usdz_url': None,
            'thumbnail_url': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'completed_at': None,
        }
    
    @staticmethod
    def update(updates):
        """Prepare update document."""
        updates['updated_at'] = datetime.utcnow()
        return {'$set': updates}


class PrinterSchema:
    """Schema for printer documents."""
    
    @staticmethod
    def create(user_id, name, printer_type, model, build_volume_x, build_volume_y, build_volume_z, **kwargs):
        """Create a new printer document."""
        doc = {
            'user_id': str(user_id),  # Store as string for MongoDB users
            'name': name,
            'printer_type': printer_type,  # 'prusa' or 'snapmaker'
            'model': model,
            'serial_number': kwargs.get('serial_number'),
            'ip_address': kwargs.get('ip_address'),
            'build_volume_x': build_volume_x,
            'build_volume_y': build_volume_y,
            'build_volume_z': build_volume_z,
            'status': kwargs.get('status', 'idle'),  # idle, printing, offline, error
            'current_mode': kwargs.get('current_mode'),  # For Snapmaker: 3d_print, cnc, laser
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_online': None,
        }
        return doc
    
    @staticmethod
    def update(updates):
        """Prepare update document."""
        updates['updated_at'] = datetime.utcnow()
        return {'$set': updates}
    
    @staticmethod
    def can_print_3d(printer):
        """Check if printer can currently print 3D models."""
        if printer['printer_type'] == 'prusa':
            return True
        elif printer['printer_type'] == 'snapmaker':
            return printer.get('current_mode') == '3d_print'
        return False


class PrintJobSchema:
    """Schema for print job documents."""
    
    @staticmethod
    def create(user_id, model_id, printer_id, **kwargs):
        """Create a new print job document."""
        return {
            'user_id': str(user_id),  # Store as string for MongoDB users
            'model_id': ObjectId(model_id) if isinstance(model_id, str) else model_id,
            'printer_id': ObjectId(printer_id) if isinstance(printer_id, str) else printer_id,
            'status': kwargs.get('status', 'queued'),  # queued, printing, completed, failed, cancelled
            'notes': kwargs.get('notes'),
            'material': kwargs.get('material'),  # PLA, ABS, PETG, etc.
            'layer_height': kwargs.get('layer_height'),  # mm
            'infill_percentage': kwargs.get('infill_percentage'),  # 0-100
            'estimated_duration': kwargs.get('estimated_duration'),  # minutes
            'actual_duration': None,
            'created_at': datetime.utcnow(),
            'started_at': None,
            'completed_at': None,
        }
    
    @staticmethod
    def update(updates):
        """Prepare update document."""
        return {'$set': updates}


class GenerationJobSchema:
    """Schema for generation job documents."""
    
    @staticmethod
    def create(model_id, meshy_task_id, **kwargs):
        """Create a new generation job document."""
        return {
            'model_id': ObjectId(model_id) if isinstance(model_id, str) else model_id,
            'meshy_task_id': meshy_task_id,
            'meshy_status': kwargs.get('meshy_status', 'PENDING'),
            'meshy_response': kwargs.get('meshy_response', {}),
            'progress': kwargs.get('progress', 0),  # 0-100
            'last_checked_at': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
    
    @staticmethod
    def update(updates):
        """Prepare update document."""
        updates['updated_at'] = datetime.utcnow()
        return {'$set': updates}


# Display name mappings
PRINTER_TYPE_DISPLAY = {
    'prusa': 'Prusa',
    'snapmaker': 'Snapmaker',
}

PRINTER_STATUS_DISPLAY = {
    'idle': 'Idle',
    'printing': 'Printing',
    'offline': 'Offline',
    'error': 'Error',
}

SNAPMAKER_MODE_DISPLAY = {
    '3d_print': '3D Printing',
    'cnc': 'CNC Milling',
    'laser': 'Laser Engraving',
}

MODEL_STATUS_DISPLAY = {
    'pending': 'Pending',
    'processing': 'Processing',
    'completed': 'Completed',
    'failed': 'Failed',
}

PRINT_JOB_STATUS_DISPLAY = {
    'queued': 'Queued',
    'printing': 'Printing',
    'completed': 'Completed',
    'failed': 'Failed',
    'cancelled': 'Cancelled',
}


def get_display_name(value, mapping):
    """Get display name from mapping."""
    return mapping.get(value, value)
