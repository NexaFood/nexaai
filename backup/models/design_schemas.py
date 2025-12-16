"""
Design project schemas for multi-stage workflow.
Handles: Overall Design → Part Breakdown → 3D Generation
"""
from datetime import datetime
from bson import ObjectId


class DesignProjectSchema:
    """Schema for design project documents (tracks entire workflow)."""
    
    @staticmethod
    def create(user_id, original_prompt, **kwargs):
        """Create a new design project document."""
        return {
            'user_id': str(user_id),
            'original_prompt': original_prompt,
            'stage': 'concept',  # 'concept', 'overall_model', 'parts', 'generation', 'completed'
            'status': 'pending',  # 'pending', 'approved', 'generating', 'completed', 'failed'
            
            # Stage 1: Concept
            'concept_description': None,
            'concept_approved_at': None,
            
            # Stage 2: Overall Model
            'overall_model_code': None,
            'overall_model_step_path': None,
            'overall_model_stl_path': None,
            'overall_model_approved_at': None,
            
            # Stage 3: Parts
            'parts_breakdown': [],  # List of part objects
            'parts_approved_at': None,
            
            # Stage 4: Generation
            'total_parts': 0,
            'generated_parts': 0,
            'failed_parts': 0,
            
            # Metadata
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'completed_at': None,
        }
    
    @staticmethod
    def update(updates):
        """Prepare update document."""
        updates['updated_at'] = datetime.utcnow()
        return {'$set': updates}


class DesignConceptSchema:
    """Schema for design concept documents (Stage 1)."""
    
    @staticmethod
    def create(project_id, original_prompt, **kwargs):
        """Create a new design concept document."""
        return {
            'project_id': ObjectId(project_id) if isinstance(project_id, str) else project_id,
            'original_prompt': original_prompt,
            'refined_description': kwargs.get('refined_description'),
            'design_type': kwargs.get('design_type'),  # 'vehicle', 'robot', 'structure', etc.
            'key_features': kwargs.get('key_features', []),
            'estimated_complexity': kwargs.get('estimated_complexity', 'medium'),  # 'low', 'medium', 'high'
            'estimated_parts_count': kwargs.get('estimated_parts_count', 0),
            'status': 'pending',  # 'pending', 'approved', 'rejected'
            'created_at': datetime.utcnow(),
            'approved_at': None,
        }
    
    @staticmethod
    def update(updates):
        """Prepare update document."""
        return {'$set': updates}


class PartBreakdownSchema:
    """Schema for part breakdown documents (Stage 2)."""
    
    @staticmethod
    def create(project_id, parts_list, **kwargs):
        """Create a new part breakdown document."""
        return {
            'project_id': ObjectId(project_id) if isinstance(project_id, str) else project_id,
            'parts': parts_list,  # List of part objects with manufacturing info
            'total_parts': len(parts_list),
            'parts_by_method': {
                '3d_print': sum(1 for p in parts_list if p.get('manufacturing_method') == '3d_print'),
                'cnc': sum(1 for p in parts_list if p.get('manufacturing_method') == 'cnc'),
            },
            'status': 'pending',  # 'pending', 'approved', 'rejected'
            'created_at': datetime.utcnow(),
            'approved_at': None,
        }
    
    @staticmethod
    def update(updates):
        """Prepare update document."""
        return {'$set': updates}


class PartSchema:
    """Schema for individual part within a breakdown."""
    
    @staticmethod
    def create(name, description, manufacturing_method, **kwargs):
        """Create a part object (not a MongoDB document, just a dict)."""
        return {
            'part_number': kwargs.get('part_number', 1),
            'name': name,
            'description': description,
            'manufacturing_method': manufacturing_method,  # '3d_print' or 'cnc'
            'material_recommendation': kwargs.get('material_recommendation', 'PLA'),
            'estimated_dimensions': kwargs.get('estimated_dimensions', {}),  # {x, y, z} in mm
            'complexity': kwargs.get('complexity', 'medium'),  # 'low', 'medium', 'high'
            'quantity': kwargs.get('quantity', 1),
            'notes': kwargs.get('notes', ''),
            'refined_prompt': kwargs.get('refined_prompt', ''),  # For 3D generation
            'model_id': None,  # Will be set when 3D model is generated
            
            # CadQuery generation data
            'cadquery_code': None,  # Generated Python code
            'step_file_path': None,  # Path to STEP file
            'stl_file_path': None,  # Path to STL file
            'generation_error': None,  # Error message if generation failed
            
            'status': 'pending',  # 'pending', 'generating', 'completed', 'failed'
        }


# Display name mappings
DESIGN_STAGE_DISPLAY = {
    'concept': 'Design Concept',
    'parts': 'Part Breakdown',
    'generation': '3D Generation',
    'completed': 'Completed',
}

MANUFACTURING_METHOD_DISPLAY = {
    '3d_print': '3D Print',
    'cnc': 'CNC',
}

COMPLEXITY_DISPLAY = {
    'low': 'Low',
    'medium': 'Medium',
    'high': 'High',
}
