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
        
        system_prompt = """You are an expert CAD engineer who writes CadQuery Python code.

CadQuery is a Python library for building parametric 3D CAD models.

Key CadQuery concepts:
- Start with a Workplane: cq.Workplane("XY")
- Create 2D shapes: .box(), .circle(), .rect()
- Extrude to 3D: .extrude(height)
- Add features AFTER creating solid: .faces(selector).workplane().hole()
- Combine operations: .union(), .cut()

IMPORTANT RULES:
1. ALWAYS create a solid shape FIRST before using .faces()
2. Use .box() or .extrude() to create the base solid
3. THEN select faces and add features
4. Keep designs simple and manufacturable
5. Use realistic dimensions (10-500mm typical)

Example - Simple box (GOOD):
```python
import cadquery as cq

# Create a simple rectangular plate
result = cq.Workplane("XY").box(100, 50, 10)
```

Example - Box with holes (GOOD):
```python
import cadquery as cq

# Create base plate
result = (
    cq.Workplane("XY")
    .box(100, 50, 10)  # Create solid FIRST
    .faces(">Z")        # THEN select top face
    .workplane()
    .rect(80, 40, forConstruction=True)
    .vertices()
    .hole(5)
)
```

Example - Mounting bracket (GOOD):
```python
import cadquery as cq

# Create L-shaped mounting bracket
base = cq.Workplane("XY").box(50, 40, 5)
wall = cq.Workplane("XZ").workplane(offset=-20).box(50, 30, 5)
result = base.union(wall)
```

Example - Cylinder (GOOD):
```python
import cadquery as cq

# Create a simple cylinder
result = cq.Workplane("XY").circle(20).extrude(50)
```

BAD Example (AVOID - creates empty result):
```python
# DON'T DO THIS - no solid created before .faces()
result = cq.Workplane("XY").faces(">Z")  # ERROR!
```

Generate clean, well-commented CadQuery code. The variable MUST be named 'result'.
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
