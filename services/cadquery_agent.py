"""
CadQuery AI Agent

Generates CadQuery Python code from natural language design descriptions.
Supports both custom fine-tuned model and GPT-4 fallback.
"""

import os
import logging
from openai import OpenAI
from typing import Dict, Any, List, Optional
from pathlib import Path
from services.cadquery_prompts import get_system_prompt_gpt, get_user_prompt_gpt, MULTIPART_SYSTEM_PROMPT, get_multipart_user_prompt

logger = logging.getLogger(__name__)

# Global singleton storage
_SHARED_MODEL = None
_SHARED_TOKENIZER = None

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
                logger.info("✅ Custom CadQuery model ready")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load custom model: {e}")
                logger.info("Falling back to GPT-4")
                self.use_custom_model = False
                self.client = OpenAI()
        else:
            self.client = OpenAI()
            logger.info(f"CadQuery AI Agent initialized with GPT model: {model}")
    
    def _load_custom_model(self):
        """Load the custom fine-tuned CadQuery model (using Singleton pattern)"""
        global _SHARED_MODEL, _SHARED_TOKENIZER
        
        # specific to this method: import only when needed to save memory if not using custom model
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel
        
        # 1. Check if already loaded
        if _SHARED_MODEL is not None and _SHARED_TOKENIZER is not None:
            self.custom_model = _SHARED_MODEL
            self.tokenizer = _SHARED_TOKENIZER
            logger.info("Using cached custom model instance")
            return
            
        logger.info("Loading custom CadQuery model for the first time...")
        
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
        logger.info("Loading Qwen2.5-Coder base model...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        base_model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-7B-Instruct",
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # Load LoRA adapters
        logger.info(f"Loading LoRA adapters from {checkpoint_path}...")
        self.custom_model = PeftModel.from_pretrained(base_model, str(checkpoint_path))
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # Update global cache
        _SHARED_MODEL = self.custom_model
        _SHARED_TOKENIZER = self.tokenizer
        
        logger.info("✅ Custom model loaded successfully and cached")
    
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
        import torch
        from transformers import StoppingCriteria, StoppingCriteriaList
        
        # Custom stopping criterion: stop when we see markers of next example
        class StopOnNextExample(StoppingCriteria):
            def __init__(self, tokenizer):
                self.tokenizer = tokenizer
                # Multiple stop patterns to catch different separators
                self.stop_patterns = [
                    "### Prompt:",  # Next training example
                    "\n---\n",      # Markdown horizontal rule
                    "\n## ",        # Markdown heading level 2
                    "\n# ",         # Markdown heading level 1
                ]
                self.stop_ids_list = [
                    tokenizer.encode(pattern, add_special_tokens=False)
                    for pattern in self.stop_patterns
                ]
            
            def __call__(self, input_ids, scores, **kwargs):
                # Check if the last N tokens match any stop pattern
                for i in range(len(input_ids)):
                    for stop_ids in self.stop_ids_list:
                        if len(stop_ids) == 0:
                            continue
                        last_tokens = input_ids[i, -len(stop_ids):].tolist()
                        if last_tokens == stop_ids:
                            return True
                return False
        
        # Format prompt to match training format: "### Prompt: {prompt}\n### Code:\n{code}"
        formatted_prompt = f"### Prompt: {prompt}\n### Code:\n"
        
        # Tokenize
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.custom_model.device)
        
        # Create stopping criteria
        stopping_criteria = StoppingCriteriaList([
            StopOnNextExample(self.tokenizer)  # Now handles multiple stop patterns
        ])
        
        # Generate
        with torch.no_grad():
            outputs = self.custom_model.generate(
                **inputs,
                max_new_tokens=1024,  # Allow longer code
                temperature=0.3,  # Lower temperature for more focused output
                top_p=0.9,  # Slightly more focused sampling
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.2,  # Higher penalty to prevent repetitive code
                stopping_criteria=stopping_criteria,  # Stop at next example
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
        
        system_prompt = get_system_prompt_gpt()
        user_prompt = get_user_prompt_gpt(prompt)

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
            
            # Keep empty lines
            if not stripped:
                cleaned_lines.append(line)
                continue
            
            # Stop at markdown separators
            if stripped in ['---', '===', '***']:
                # Markdown horizontal rule, stop here
                break
            
            # Stop if we hit something that looks like HTML
            if stripped.startswith('<') and any(tag in stripped for tag in ['div', 'span', 'p', '/div', '/span', '/p', 'html', 'body']):
                break
            
            # Keep single-line comments (but stop at markdown headings)
            if stripped.startswith('#'):
                # Check if this is a markdown heading (### or ## followed by prose)
                if (stripped.startswith('###') or stripped.startswith('##')) and len(stripped) > 4:
                    # This is likely a markdown heading, stop here
                    break
                # Regular comment, keep it
                cleaned_lines.append(line)
                continue
            
            # Check if this looks like an explanation (prose) rather than code
            # Prose characteristics:
            # - Starts with capital letter
            # - Contains multiple words (3+)
            # - No Python operators or syntax
            # - Forms a complete sentence
            
            words = stripped.split()
            if len(words) == 0:
                cleaned_lines.append(line)
                continue
                
            has_python_syntax = any(char in stripped for char in ['=', '(', ')', '.', '[', ']', ':', ','])
            starts_with_keyword = words[0].lower() in ['import', 'from', 'def', 'class', 'if', 'for', 'while', 'try', 'with', 'return', 'result']
            
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
        
        system_prompt = MULTIPART_SYSTEM_PROMPT
        user_prompt = get_multipart_user_prompt(prompt)

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
