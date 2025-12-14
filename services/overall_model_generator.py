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
        
        # Check if this is a basic geometric primitive
        prompt_lower = original_prompt.lower()
        is_basic_shape = any(word in prompt_lower for word in [
            'cube', 'box', 'square', 'rectangle', 'sphere', 'ball', 'cylinder', 
            'tube', 'cone', 'pyramid', 'torus', 'ring'
        ])
        
        if is_basic_shape:
            # For basic shapes, be VERY explicit about simplicity
            description = f"""
Create EXACTLY the shape described: {original_prompt}

This is a BASIC GEOMETRIC PRIMITIVE. Do NOT add extra features.

For example:
- "A cube 50x50x50" → JUST a box(50, 50, 50)
- "A cylinder 30mm diameter, 100mm tall" → JUST circle(15).extrude(100)
- "A sphere 40mm diameter" → JUST sphere(20)

Use the SIMPLEST possible code. Usually just 1-2 lines.
Do NOT add fins, motors, decorations, or any extra features.
"""
        else:
            # For complex objects, use the detailed guidelines
            description = f"""
Create a SIMPLE but RECOGNIZABLE 3D model of: {original_prompt}

Your goal: Make a model that someone would immediately recognize as "{original_prompt}".

GUIDELINES:
1. Use appropriate basic shapes for THIS specific object
2. Include the KEY features that make it recognizable
3. Keep each feature simple (no complex curves or details)
4. Use realistic proportions
5. Combine 3-8 simple shapes maximum

GOOD EXAMPLES:

Rocket:
- Main body: tall cylinder (diameter 100mm, height 500mm)
- Nose cone: cone on top (base 100mm, height 150mm)
- Fins: 3-4 small rectangular boxes at base
- Result: Clearly recognizable as a rocket

Car:
- Body: long box (length 400mm, width 180mm, height 80mm)
- Cabin: smaller box on top, offset to back (length 200mm, width 180mm, height 100mm)
- Wheels: 4 cylinders positioned at corners (diameter 60mm, width 30mm)
- Result: Clearly recognizable as a car

Robot:
- Body: box (100x80x120mm)
- Head: cylinder on top (diameter 60mm, height 40mm)
- Arms: 2 long boxes on sides (20x20x100mm each)
- Legs: 2 boxes at bottom (30x30x80mm each)
- Result: Clearly recognizable as a robot

Drone:
- Center body: flat box (150x150x30mm)
- Arms: 4 thin cylinders extending from corners (diameter 10mm, length 100mm)
- Motors: small cylinders at end of each arm (diameter 25mm, height 15mm)
- Result: Clearly recognizable as a drone

Lawn Mower:
- Deck: wide flat box (500x400x100mm)
- Handle: vertical box at back (30x30x400mm) + horizontal box on top (300x30x30mm)
- Wheels: 4 cylinders (diameter 80mm, width 40mm)
- Result: Clearly recognizable as a lawn mower

Your task: Think about what shapes would make "{original_prompt}" IMMEDIATELY RECOGNIZABLE.
Use union() to combine shapes. Keep it simple but distinctive!
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
