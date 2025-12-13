"""
CadQuery AI Agent

Generates CadQuery Python code from natural language design descriptions.
Supports both custom fine-tuned model and GPT-4 fallback.
"""

import os
import logging
import torch
from openai import OpenAI
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CadQueryAgent:
    """AI agent that generates CadQuery Python code for 3D models."""
    
    def __init__(self, use_custom_model: bool = True, model: str = "gpt-4.1-mini"):
        """
        Initialize the CadQuery AI agent.
        
        Args:
            use_custom_model: If True, use custom fine-tuned model. If False, use GPT-4.
            model: GPT model to use as fallback (gpt-4.1-mini, gpt-4.1-nano, gemini-2.5-flash)
        """
        self.use_custom_model = use_custom_model
        self.gpt_model = model
        self.custom_model = None
        self.tokenizer = None
        
        if use_custom_model:
            try:
                self._load_custom_model()
                logger.info("✅ Custom CadQuery model loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load custom model: {e}")
                logger.info("Falling back to GPT-4")
                self.use_custom_model = False
                self.client = OpenAI()
        else:
            self.client = OpenAI()
            logger.info(f"CadQuery AI Agent initialized with GPT model: {model}")
    
    def _load_custom_model(self):
        """Load the custom fine-tuned CadQuery model"""
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel
        
        # Find the trained model
        checkpoint_dir = Path(__file__).parent.parent / "training" / "cadquery_model"
        
        # Try models in order of preference
        checkpoint_paths = [
            checkpoint_dir / "final_model",      # Production model (best)
            checkpoint_dir / "checkpoint-1200",  # Final checkpoint
            checkpoint_dir / "checkpoint-1000",  # Second checkpoint
            checkpoint_dir / "checkpoint-500",   # First checkpoint
        ]
        
        checkpoint_path = None
        for path in checkpoint_paths:
            if path.exists():
                checkpoint_path = path
                logger.info(f"Found checkpoint: {path}")
                break
        
        if not checkpoint_path:
            raise FileNotFoundError("No trained checkpoint found")
        
        # Load base model with 4-bit quantization
        logger.info("Loading CodeLlama base model...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        base_model = AutoModelForCausalLM.from_pretrained(
            "codellama/CodeLlama-7b-hf",
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # Load LoRA adapters
        logger.info(f"Loading LoRA adapters from {checkpoint_path}...")
        self.custom_model = PeftModel.from_pretrained(base_model, str(checkpoint_path))
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-hf")
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        logger.info("✅ Custom model loaded successfully")
    
    def generate_code(self, prompt: str) -> Dict[str, Any]:
        """
        Generate CadQuery Python code from a natural language prompt.
        
        Args:
            prompt: Natural language description of the design
            
        Returns:
            Dict with:
                - code: Python code using CadQuery
                - description: What the code creates
                - model_used: Which model generated the code
        """
        logger.info(f"Generating CadQuery code from prompt: {prompt}")
        
        if self.use_custom_model and self.custom_model is not None:
            code = self._generate_with_custom_model(prompt)
            model_used = "custom-cadquery-model"
        else:
            code = self._generate_with_gpt(prompt)
            model_used = self.gpt_model
        
        logger.info(f"Generated {len(code)} characters of CadQuery code using {model_used}")
        
        return {
            "code": code,
            "description": prompt,
            "language": "python",
            "library": "cadquery",
            "model_used": model_used
        }
    
    def _generate_with_custom_model(self, prompt: str) -> str:
        """Generate code using the custom fine-tuned model"""
        
        # Format prompt to match training format: "### Prompt: {prompt}\n### Code:\n{code}"
        formatted_prompt = f"### Prompt: {prompt}\n### Code:\n"
        
        # Tokenize
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.custom_model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.custom_model.generate(
                **inputs,
                max_new_tokens=1024,  # Increased from 512 to allow longer code
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,  # Prevent repetitive code
            )
        
        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the code part (after "### Code:\n")
        if "### Code:" in generated_text:
            code = generated_text.split("### Code:", 1)[1].strip()
        else:
            code = generated_text
        
        # Clean up the code
        code = self._clean_generated_code(code)
        
        return code
    
    def _generate_with_gpt(self, prompt: str) -> str:
        """Generate code using GPT-4"""
        
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
            model=self.gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        code = response.choices[0].message.content.strip()
        code = self._clean_generated_code(code)
        
        return code
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean up generated code and remove trailing explanations"""
        
        # Remove markdown code blocks (start and end)
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        
        code = code.strip()
        
        # Remove any remaining code fences that appear in the middle
        # (AI sometimes adds these as separators)
        lines = code.split('\n')
        lines = [line for line in lines if line.strip() not in ['```', '```python', '```py']]
        code = '\n'.join(lines)
        
        # Remove trailing explanations (common with LLMs)
        # Look for lines that are clearly prose, not code
        lines = code.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Keep empty lines and comments
            if not stripped or stripped.startswith('#'):
                cleaned_lines.append(line)
                continue
            
            # Check if this looks like an explanation (prose) rather than code
            # Prose characteristics:
            # - Starts with capital letter
            # - Contains multiple words (3+)
            # - No Python operators or syntax
            # - Forms a complete sentence
            
            words = stripped.split()
            has_python_syntax = any(char in stripped for char in ['=', '(', ')', '.', '[', ']', ':', ','])
            starts_with_keyword = stripped.split()[0].lower() in ['import', 'from', 'def', 'class', 'if', 'for', 'while', 'try', 'with', 'return', 'result']
            
            is_prose = (
                len(words) >= 3 and
                stripped[0].isupper() and
                not has_python_syntax and
                not starts_with_keyword and
                not stripped.endswith((':', ',', ')', ']', '}'))
            )
            
            if is_prose:
                # This looks like an explanation, stop here
                break
            
            cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines).strip()
        
        # Ensure it starts with import
        if not code.startswith("import cadquery"):
            code = "import cadquery as cq\n\n" + code
        
        return code
    
    def generate_multi_part_design(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a multi-part design with separate CadQuery code for each part.
        Currently only supported with GPT-4.
        
        Args:
            prompt: Natural language description of the complete design
            
        Returns:
            Dict with:
                - parts: List of parts, each with code and description
                - assembly_notes: How to assemble the parts
        """
        logger.info(f"Generating multi-part design from prompt: {prompt}")
        
        # Multi-part generation requires structured output, use GPT-4
        if not hasattr(self, 'client'):
            self.client = OpenAI()
        
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
            model=self.gpt_model,
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
