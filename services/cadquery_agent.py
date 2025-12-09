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
- Add features: .faces().workplane().hole(diameter)
- Combine operations: .union(), .cut()

Example - Simple box:
```python
import cadquery as cq

result = cq.Workplane("XY").box(100, 50, 10)
```

Example - Box with holes:
```python
import cadquery as cq

result = (cq.Workplane("XY")
    .box(100, 50, 10)
    .faces(">Z")
    .workplane()
    .rect(80, 40, forConstruction=True)
    .vertices()
    .hole(5)
)
```

Generate clean, well-commented CadQuery code. The variable MUST be named 'result'.
"""

        user_prompt = f"""Generate CadQuery Python code for: {prompt}

Requirements:
1. Use 'import cadquery as cq'
2. Final model MUST be in variable named 'result'
3. Add comments explaining each step
4. Use millimeters for all dimensions
5. Make the code clean and readable

Return ONLY the Python code, no explanations."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
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
