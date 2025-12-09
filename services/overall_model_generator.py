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
        # Build simplified description for overall model
        # Extract just the essential shape/form from the prompt
        original_prompt = concept.get('original_prompt', '')
        
        description = f"""
Create a SIMPLE, RECOGNIZABLE 3D model of: {original_prompt}

IMPORTANT RULES:
1. Keep it VERY SIMPLE - use basic shapes (boxes, cylinders, cones)
2. Focus on the OVERALL FORM, not details
3. This is a CONCEPT MODEL - just show the basic shape
4. Use realistic proportions based on what this object is
5. DO NOT try to model every feature - just the main body/shape

Examples:
- "a rocket" → tall cylinder (body) + cone (nose) + small cylinders (fins)
- "a robot" → box (body) + cylinder (head) + boxes (limbs)
- "a car" → long box (body) + smaller box (cabin) + cylinders (wheels)
- "a drone" → flat box (body) + thin cylinders (arms)

Keep it simple and manufacturable!
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
