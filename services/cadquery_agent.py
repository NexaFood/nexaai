"""
CadQuery AI Agent

Generates CadQuery Python code from natural language design descriptions.
Much simpler than Onshape API - just generates code that creates the 3D model.
"""

import os
import logging
from openai import OpenAI
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CadQueryAgent:
    """AI agent that generates CadQuery Python code for 3D models."""
    
    def __init__(self, model="gpt-4.1-mini"):
        """
        Initialize the CadQuery AI agent.
        
        Args:
            model: LLM model to use for code generation
                  Options: gpt-4.1-mini (best available), gpt-4.1-nano, gemini-2.5-flash
        """
        self.client = OpenAI()  # Uses OPENAI_API_KEY from environment
        self.model = model
        logger.info(f"CadQuery AI Agent initialized with model: {model}")
    
    def generate_code(self, prompt: str) -> Dict[str, Any]:
        """
        Generate CadQuery Python code from a natural language prompt.
        
        Args:
            prompt: Natural language description of the design
            
        Returns:
            Dict with:
                - code: Python code using CadQuery
                - description: What the code creates
                - parts: List of parts created
        """
        logger.info(f"Generating CadQuery code from prompt: {prompt}")
        
        # Import examples library
        from services.cadquery_examples import get_examples_for_prompt
        
        examples_text = get_examples_for_prompt(max_examples=15)
        
        system_prompt = f"""You are an expert CAD engineer who writes CadQuery Python code.

CadQuery is a Python library for building parametric 3D CAD models.

## CRITICAL RULES (MUST FOLLOW):

1. **ALWAYS create a solid shape FIRST** before using .faces()
   - Use .box(), .circle().extrude(), or .polygon().extrude()
   - NEVER call .faces() on an empty workplane

2. **Face selection only works on solids**
   - .faces(">Z") selects top face
   - .faces("<Z") selects bottom face
   - .faces("|Z") selects faces parallel to Z axis

3. **Use realistic dimensions**
   - Small parts: 10-100mm
   - Medium parts: 100-500mm
   - Large parts: 500-2000mm

4. **Keep designs simple and manufacturable**
   - Avoid complex curves unless necessary
   - Use standard shapes (boxes, cylinders, holes)
   - Think about how it would be 3D printed or CNC machined

5. **Variable naming**
   - Final model MUST be in variable named 'result'
   - Use descriptive intermediate variable names

6. **Common patterns**
   - Box with holes: .box() → .faces(">Z") → .workplane() → .hole()
   - Cylinder: .circle() → .extrude()
   - Hollow tube: .circle(outer) → .circle(inner) → .extrude()
   - L-bracket: create two boxes → .union()

## HIGH-QUALITY EXAMPLES:

{examples_text}

## COMMON MISTAKES TO AVOID:

❌ BAD: .faces(">Z") before creating solid
✅ GOOD: .box() THEN .faces(">Z")

❌ BAD: Complex splines and curves for simple parts
✅ GOOD: Use basic shapes (box, cylinder, polygon)

❌ BAD: Unrealistic dimensions (1mm thick plate, 10000mm long beam)
✅ GOOD: Realistic dimensions based on part function

Generate clean, well-commented CadQuery code. Think about manufacturability.
"""

        user_prompt = f"""Generate CadQuery Python code for: {prompt}

Requirements:
1. Use 'import cadquery as cq'
2. Final model MUST be in variable named 'result'
3. Add comments explaining each step
4. Use millimeters for all dimensions
5. ALWAYS create a solid shape FIRST (use .box() or .extrude())
6. ONLY use .faces() AFTER creating a solid
7. Keep the design simple and manufacturable
8. Use realistic dimensions based on the part description

Return ONLY the Python code, no explanations or markdown."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3  # Lower temperature for more consistent, reliable code
        )
        
        code = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()
        
        logger.info(f"Generated {len(code)} characters of CadQuery code")
        
        return {
            "code": code,
            "description": prompt,
            "language": "python",
            "library": "cadquery"
        }
    
    def generate_multi_part_design(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a multi-part design with separate CadQuery code for each part.
        
        Args:
            prompt: Natural language description of the complete design
            
        Returns:
            Dict with:
                - parts: List of parts, each with code and description
                - assembly_notes: How to assemble the parts
        """
        logger.info(f"Generating multi-part design from prompt: {prompt}")
        
        system_prompt = """You are an expert CAD engineer who designs multi-part assemblies.

Analyze the design request and break it into individual parts.
For each part, generate CadQuery Python code.

Return a JSON object with this structure:
{
    "parts": [
        {
            "name": "Part name",
            "description": "What this part does",
            "manufacturing": "3D Print" or "CNC",
            "material": "Suggested material",
            "code": "CadQuery Python code"
        }
    ],
    "assembly_notes": "How to assemble the parts together"
}

Each part's code must:
1. Import cadquery as cq
2. Store final model in 'result' variable
3. Use millimeters for dimensions
4. Be complete and runnable
"""

        user_prompt = f"""Design a multi-part assembly for: {prompt}

Break it into individual parts that can be manufactured separately.
For each part, generate complete CadQuery code.

Return ONLY valid JSON, no other text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        logger.info(f"Generated multi-part design with {len(result.get('parts', []))} parts")
        
        return result
