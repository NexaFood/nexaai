"""
Design Analyzer Service - Uses LLM to analyze designs and recommend manufacturing methods.

This service:
1. Refines user prompts for better 3D generation
2. Analyzes designs to determine part splitting requirements
3. Recommends manufacturing methods (3D printing vs CNC) for each part
"""
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class DesignAnalyzer:
    """
    Analyzes design requests and provides manufacturing recommendations.
    """
    
    def __init__(self):
        """Initialize the OpenAI client (API key is pre-configured in environment)."""
        self.client = OpenAI()
        self.model = "gpt-4.1-mini"  # Fast and cost-effective
    
    def analyze_and_refine(self, user_prompt):
        """
        Analyze a user's design request and provide:
        1. Refined prompts for 3D generation
        2. Part splitting recommendations
        3. Manufacturing method suggestions
        
        Args:
            user_prompt: The user's original design description
        
        Returns:
            dict: Analysis results with refined prompts and recommendations
        """
        system_prompt = """You are an expert in 3D modeling, manufacturing, and design for production.
Your task is to analyze design requests and provide detailed recommendations for manufacturing.

For each design request, you must:
1. Refine the prompt to be more detailed and optimized for 3D model generation
2. Determine if the design should be split into multiple parts for manufacturing
3. For each part, recommend the best manufacturing method (3D printing or CNC machining)

Consider these factors:
- **3D Printing**: Best for complex geometries, organic shapes, internal structures, lightweight parts, prototypes
- **CNC Machining**: Best for high precision, flat surfaces, metal parts, structural components, load-bearing parts

Respond in JSON format with this structure:
{
  "original_prompt": "user's original prompt",
  "analysis": "brief analysis of the design requirements",
  "parts": [
    {
      "name": "descriptive part name",
      "description": "what this part is and its function",
      "refined_prompt": "detailed prompt optimized for 3D generation",
      "manufacturing_method": "3d_print" or "cnc",
      "reasoning": "why this method is recommended",
      "material_suggestion": "recommended material",
      "estimated_dimensions": "approximate size (e.g., '100x50x20mm')",
      "complexity": "low/medium/high"
    }
  ],
  "assembly_notes": "how the parts fit together (if multiple parts)"
}

Be specific and detailed in the refined prompts. Include details about:
- Exact shapes, dimensions, and proportions
- Surface textures and finishes
- Functional features (holes, slots, mounting points)
- Structural requirements
- Aesthetic details"""

        try:
            logger.info(f"Analyzing design request: {user_prompt[:100]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Design request: {user_prompt}"}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Design analysis complete: {len(result.get('parts', []))} parts identified")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to analyze design: {e}")
            # Fallback to simple refinement
            return self._fallback_analysis(user_prompt)
    
    def _fallback_analysis(self, user_prompt):
        """
        Fallback analysis if LLM fails - creates a simple single-part design.
        
        Args:
            user_prompt: The user's original prompt
        
        Returns:
            dict: Simple analysis with one part
        """
        return {
            "original_prompt": user_prompt,
            "analysis": "Simple single-part design",
            "parts": [
                {
                    "name": "Main Component",
                    "description": "Primary design component",
                    "refined_prompt": f"Detailed 3D model of {user_prompt}, with realistic proportions, smooth surfaces, and proper structural details",
                    "manufacturing_method": "3d_print",
                    "reasoning": "Default to 3D printing for flexibility",
                    "material_suggestion": "PLA or ABS plastic",
                    "estimated_dimensions": "To be determined",
                    "complexity": "medium"
                }
            ],
            "assembly_notes": "Single-part design, no assembly required"
        }
    
    def refine_prompt_simple(self, user_prompt):
        """
        Simple prompt refinement without full analysis (faster).
        
        Args:
            user_prompt: The user's original prompt
        
        Returns:
            str: Refined prompt
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at writing prompts for 3D model generation. Enhance the user's prompt to be more detailed and specific, including dimensions, materials, textures, and functional details. Keep it concise but descriptive."
                    },
                    {
                        "role": "user",
                        "content": f"Enhance this 3D model prompt: {user_prompt}"
                    }
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            refined = response.choices[0].message.content.strip()
            logger.info(f"Refined prompt: {refined[:100]}...")
            return refined
        
        except Exception as e:
            logger.error(f"Failed to refine prompt: {e}")
            return f"Detailed 3D model of {user_prompt}, with realistic proportions and proper structural details"
