"""
Overall Model Generator

Generates a complete 3D model of the design concept using CadQuery AI.
This is shown in Stage 2 before breaking down into parts.
"""

import logging
from services.cadquery_agent import CadQueryAgent
from services.cadquery_executor import CadQueryExecutor

logger = logging.getLogger(__name__)


def generate_overall_model(concept, output_dir, model_id="overall_model"):
    """
    Generate an overall 3D model from the design concept.
    
    Args:
        concept: Design concept document with description and features
        output_dir: Directory to save STEP/STL files
        model_id: Model identifier (default: "overall_model")
        
    Returns:
        Dict with:
            - success: Boolean
            - code: Generated CadQuery code
            - step_file: Path to STEP file
            - stl_file: Path to STL file
            - error: Error message if failed
    """
    try:
        # Build description for overall model
        description = f"""
Design: {concept.get('original_prompt')}

Overview: {concept.get('overview', '')}

Key Features:
{chr(10).join('- ' + f for f in concept.get('key_features', []))}

Technical Specs: {concept.get('technical_specs', '')}

IMPORTANT: Create a SINGLE, COMPLETE model that represents the entire design.
This is an overall concept model, not individual parts.
Make it visually representative of the design concept.
Keep it relatively simple but recognizable.
"""
        
        logger.info(f"Generating overall model for: {concept.get('original_prompt')}")
        
        # Generate CadQuery code
        agent = CadQueryAgent()
        code_result = agent.generate_code(description)
        
        if not code_result or 'code' not in code_result:
            return {
                'success': False,
                'error': 'Failed to generate CadQuery code'
            }
        
        logger.info(f"Generated {len(code_result['code'])} characters of CadQuery code")
        
        # Execute code and export files
        executor = CadQueryExecutor(output_dir=output_dir)
        exec_result = executor.execute_code(
            code_result['code'],
            model_id=model_id,
            export_formats=["step", "stl"]
        )
        
        if not exec_result['success']:
            return {
                'success': False,
                'code': code_result['code'],
                'error': exec_result.get('error', 'Execution failed')
            }
        
        # Get file paths
        step_file = exec_result['files'].get('step', '')
        stl_file = exec_result['files'].get('stl', '')
        
        logger.info(f"✓ Overall model generated successfully")
        logger.info(f"  STEP: {step_file}")
        logger.info(f"  STL: {stl_file}")
        
        return {
            'success': True,
            'code': code_result['code'],
            'step_file': step_file,
            'stl_file': stl_file
        }
        
    except Exception as e:
        logger.error(f"Overall model generation failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
