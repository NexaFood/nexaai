"""
LLM-powered prompt refinement service.
Uses OpenAI or compatible LLM API to improve 3D model generation prompts.
"""
from openai import OpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def refine_prompt_with_llm(prompt):
    """
    Refine a user's prompt using LLM to improve 3D model generation results.
    
    Args:
        prompt: Original user prompt
    
    Returns:
        dict: Refinement results with improved prompt and suggestions
    """
    try:
        client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_URL
        )
        
        system_prompt = """You are an expert at creating detailed prompts for 3D model generation.
Your task is to refine user prompts to make them more specific, detailed, and suitable for AI 3D model generation.

Focus on:
1. Adding specific details about shape, form, and structure
2. Specifying materials, textures, and surface properties
3. Describing proportions and scale
4. Including style and aesthetic details
5. Removing ambiguous or conflicting descriptions

Return a JSON object with:
- refined_prompt: The improved prompt (keep it concise, under 200 words)
- suggestions: List of 3-5 specific suggestions for further improvement
- improvements: List of key improvements made to the original prompt
"""
        
        user_message = f"""Original prompt: "{prompt}"

Please refine this prompt for 3D model generation."""
        
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1000
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        return {
            'original_prompt': prompt,
            'refined_prompt': result.get('refined_prompt', prompt),
            'suggestions': result.get('suggestions', []),
            'improvements': result.get('improvements', [])
        }
    
    except Exception as e:
        logger.error(f"Failed to refine prompt with LLM: {e}")
        # Return original prompt if refinement fails
        return {
            'original_prompt': prompt,
            'refined_prompt': prompt,
            'suggestions': [
                "Add more specific details about shape and form",
                "Specify materials and textures",
                "Include scale and proportions"
            ],
            'improvements': ["Unable to refine prompt - using original"]
        }


def generate_prompt_suggestions(context=""):
    """
    Generate example prompts or suggestions for users.
    
    Args:
        context: Optional context for suggestions
    
    Returns:
        list: List of example prompts
    """
    examples = [
        "A ceramic coffee mug with a curved handle, smooth glazed surface, realistic style, 3D model",
        "A modern office chair with ergonomic design, mesh back, chrome base with wheels, detailed 3D model",
        "A wooden treasure chest with metal hinges, aged texture, slightly open lid, fantasy style",
        "A sleek smartphone with rounded edges, glass screen, metallic frame, modern design",
        "A vintage typewriter with mechanical keys, worn metal finish, realistic details"
    ]
    
    return examples
