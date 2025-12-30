"""
Enhanced Design Analyzer with 3-stage workflow.
Stage 1: Generate overall design concept
Stage 2: Break down into manufacturable parts
Stage 3: Generate refined prompts for each part
"""
from openai import OpenAI
import json
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client (API key from environment)
client = OpenAI()


def generate_design_concept(original_prompt):
    """
    Stage 1: Generate detailed design concept from user's prompt.
    
    Args:
        original_prompt: User's original design idea
    
    Returns:
        dict: {
            'refined_description': str,
            'design_type': str,
            'key_features': list,
            'estimated_complexity': str,
            'estimated_parts_count': int
        }
    """
    
    # Check if this is a basic geometric primitive
    prompt_lower = original_prompt.lower()
    basic_shapes = {
        'cube': 'cubic shape',
        'box': 'rectangular box',
        'square': 'square shape',
        'rectangle': 'rectangular shape',
        'sphere': 'spherical shape',
        'ball': 'spherical shape',
        'cylinder': 'cylindrical shape',
        'tube': 'tubular shape',
        'cone': 'conical shape',
        'pyramid': 'pyramidal shape',
        'torus': 'toroidal shape',
        'ring': 'ring shape',
        'plate': 'flat plate',
        'disc': 'circular disc',
        'disk': 'circular disc'
    }
    
    # Detect if it's a simple geometric primitive
    # Detect if it's a simple geometric primitive, but EXCLUDE complex systems
    complexity_markers = ['gear', 'system', 'assembly', 'mechanism', 'robot', 'drone', 'vehicle', 'machine', 'enclosure', 'case', 'housing', 'exchanger', 'engine']
    is_complex = any(marker in prompt_lower for marker in complexity_markers)

    for keyword, shape_desc in basic_shapes.items():
        if keyword in prompt_lower and not is_complex:
            logger.info(f"Detected basic geometric primitive: {keyword}")
            return {
                'refined_description': f"A simple {shape_desc} as specified: {original_prompt}. This is a basic geometric primitive that requires no additional features or complexity.",
                'design_type': 'geometric_primitive',
                'key_features': [f'Simple {shape_desc}', 'Single solid part', 'No moving components'],
                'estimated_complexity': 'low',
                'estimated_parts_count': 1
            }
    
    system_prompt = """You are an expert mechanical engineer and product designer. 
Your task is to take a user's design idea and create a detailed, comprehensive design concept.

**CRITICAL: Distinguish between "Primitives" and "Systems"!**
- **Primitives**: Simple shapes (cube, sphere, cylinder). Keep these SIMPLE.
- **Systems**: Assemblies with multiple interacting parts (gears, heat exchangers, enclosures, robots). Break these down into SUBSYSTEMS.

Examples:
- User: "Planetary gear system" -> Concept: "Sun gear, 3 planet gears, ring gear, carrier. Interlocking teeth." (NOT "a simple ring shape")
- User: "Heat exchanger" -> Concept: "Shell vessel, 7 internal tubes in hex pattern, baffles." (NOT "a simple tube")
- User: "Enclosure with posts" -> Concept: "Main box shell, lid, 4 corner mounting posts, cable cutouts."

Focus on:
1. Overall structure and architecture
2. Key functional components (LIST THEM EXPLICITLY)
3. Assembly approach (how parts interacting)
4. Realistic engineering features (fillets, chamfers, mounts)
"""

    user_prompt = f"""Design Concept Request: {original_prompt}

Please provide a detailed design concept including:
1. A comprehensive description of the overall design (2-3 paragraphs)
2. Design type/category:
   - "geometric_primitive" (only for simple shapes)
   - "mechanical_system" (gears, linkages, machines)
   - "enclosure" (cases, housings)
   - "structural" (brackets, frames)
3. Key features and components (list 3-10 major features)
4. Estimated complexity (low/medium/high)
5. Estimated number of parts needed:
   - Simple shapes: 1 part
   - Enclosures/Brackets: 2-10 parts
   - Systems/Machines: 10-50+ parts

Return ONLY a JSON object with this structure:
{{
    "refined_description": "detailed description here",
    "design_type": "category",
    "key_features": ["feature1", "feature2", ...],
    "estimated_complexity": "low/medium/high",
    "estimated_parts_count": 5
}}"""

    try:
        response = client.chat.completions.create(
            model="ft:gpt-4.1-mini-2025-04-14:nexafood:nexaai:Cs8FToAS",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # LOGGING FOR FINE-TUNING
        try:
            from pathlib import Path
            log_entry = {
                "original_prompt": original_prompt,
                "gpt_response": result,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            log_file = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/concept_logs.jsonl")
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as log_e:
            logger.warning(f"Failed to log concept: {log_e}")

        logger.info(f"Generated design concept: {result.get('design_type')}, {result.get('estimated_parts_count')} parts")
        return result
    
    except Exception as e:
        logger.error(f"Failed to generate design concept: {e}")
        # Fallback
        return {
            'refined_description': f"Detailed design for: {original_prompt}",
            'design_type': 'unknown',
            'key_features': [],
            'estimated_complexity': 'medium',
            'estimated_parts_count': 10
        }


def break_down_into_parts(design_concept, original_prompt):
    """
    Stage 2: Break down approved design concept into manufacturable parts.
    
    Args:
        design_concept: The approved design concept dict
        original_prompt: Original user prompt
    
    Returns:
        list: List of part dicts with manufacturing recommendations
    """
    
    # Check if this is a simple single-part object
    prompt_lower = original_prompt.lower()
    single_part_keywords = [
        'cube', 'box', 'square', 'rectangle', 'sphere', 'ball', 'cylinder',
        'tube', 'cone', 'pyramid', 'torus', 'ring', 'plate', 'block',
        'disc', 'disk', 'rod', 'bar', 'beam'
    ]
    
    # Check if it's a basic geometric primitive
    is_single_part = any(keyword in prompt_lower for keyword in single_part_keywords)
    
    # Also check if the design concept indicates it's simple
    estimated_parts = design_concept.get('estimated_parts_count', 10)
    complexity = design_concept.get('estimated_complexity', 'medium')
    
    # If it's a single-part design OR very simple prompt, return single part
    if is_single_part or (estimated_parts <= 2 and complexity == 'low'):
        logger.info(f"Detected single-part design: {original_prompt}")
        return [{
            'part_number': 1,
            'name': original_prompt.strip(),
            'description': f'Single-part design: {original_prompt}',
            'manufacturing_method': '3d_print',
            'material_recommendation': 'PLA',
            'estimated_dimensions': {'x': 100, 'y': 100, 'z': 100},
            'complexity': 'low',
            'quantity': 1,
            'notes': 'This is a single-part design that does not need to be broken down further.'
        }]
    
    system_prompt = """You are an expert manufacturing engineer specializing in 3D printing and CNC machining.

Your task is to break down a design into INDIVIDUAL MANUFACTURABLE PARTS.

CRITICAL RULES FOR PART SPLITTING:
1. **IF THE DESIGN IS ALREADY A SINGLE PART, RETURN JUST ONE PART!** (e.g., a simple bracket, plate, or enclosure)
2. Each part must fit on a 3D printer (max ~250x250x250mm) or CNC machine (max ~400x400x100mm)
3. Split large assemblies into smaller components that can be assembled
4. Separate parts that need different manufacturing methods
5. Consider assembly - parts should bolt/snap/glue together
6. For complex assemblies, create 50-200+ parts as needed

MANUFACTURING METHOD SELECTION:
**3D Print** - Use for:
- Complex geometries, curves, organic shapes
- Internal structures, hollow parts
- Lightweight components
- Parts with intricate details
- Brackets, mounts, enclosures
- Prototyping parts

**CNC** - Use for:
- Flat plates, structural frames
- High-precision parts
- Load-bearing components
- Metal parts
- Parts requiring tight tolerances
- Gears, shafts (if simple geometry)

EXAMPLES:

Rocket:
- Nose cone (3D Print - aerodynamic shape)
- Body tube sections x4 (3D Print - cylindrical, lightweight)
- Fin set x4 (CNC - flat, structural)
- Motor mount (CNC - load-bearing)
- Payload bay (3D Print - complex internal structure)
- Parachute compartment (3D Print)
- Electronics bay (3D Print - cable routing)
- Launch lugs x3 (CNC - precision mounting)
- Centering rings x6 (CNC - precise fit)
- Bulkheads x4 (CNC - structural)
... and 20+ more parts for wiring, fasteners, etc.

Quadcopter Drone:
- Center plate (CNC - structural, load-bearing)
- Motor arms x4 (CNC - strength required)
- Motor mounts x4 (3D Print - vibration dampening)
- Landing gear legs x4 (3D Print - flexible)
- Camera gimbal base (3D Print - complex geometry)
- Camera gimbal arms x2 (3D Print)
- Battery tray (CNC - flat, strong)
- Electronics enclosure (3D Print - cable management)
- Antenna mounts x2 (3D Print)
- Prop guards x4 (3D Print - flexible)
... and 30+ more parts for full assembly

Robot Arm:
- Base plate (CNC - stability)
- Shoulder joint housing (3D Print - complex geometry)
- Upper arm segment (3D Print - lightweight)
- Elbow joint housing (3D Print)
- Forearm segment (3D Print)
- Wrist joint housing (3D Print)
- Gripper base (3D Print)
- Gripper fingers x2 (3D Print - articulated)
- Servo mounts x6 (3D Print - custom fit)
- Cable routing clips x10 (3D Print)
- Bearing housings x6 (CNC - precision)
... and 40+ more parts for full assembly"""

    user_prompt = f"""Original Design: {original_prompt}

Design Concept:
{design_concept.get('refined_description', '')}

Key Features:
{', '.join(design_concept.get('key_features', []))}

Break this down into INDIVIDUAL MANUFACTURABLE PARTS. Be thorough - include ALL parts needed for a complete assembly.

For each part, provide:
1. Part number (sequential)
2. Name (descriptive)
3. Description (what it does, key features)
4. Manufacturing method ('3d_print' or 'cnc')
5. Material recommendation (PLA, ABS, Aluminum, Steel, etc.)
6. Estimated dimensions {{x, y, z}} in mm
7. Complexity ('low', 'medium', 'high')
8. Quantity (how many of this part needed)
9. Notes (assembly info, special considerations)

Return ONLY a JSON object:
{{
    "parts": [
        {{
            "part_number": 1,
            "name": "Part Name",
            "description": "What this part does",
            "manufacturing_method": "3d_print",
            "material_recommendation": "PLA",
            "estimated_dimensions": {{"x": 100, "y": 50, "z": 20}},
            "complexity": "medium",
            "quantity": 1,
            "notes": "Assembly notes"
        }},
        ...
    ]
}}

Remember: It's better to have MORE parts that fit on machines than fewer parts that are too large!"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        parts_list = result.get('parts', [])
        
        logger.info(f"Generated {len(parts_list)} parts breakdown")
        return parts_list
    
    except Exception as e:
        logger.error(f"Failed to break down into parts: {e}")
        # Fallback - create a simple single-part breakdown
        return [{
            'part_number': 1,
            'name': 'Main Component',
            'description': f'Main component for {original_prompt}',
            'manufacturing_method': '3d_print',
            'material_recommendation': 'PLA',
            'estimated_dimensions': {'x': 100, 'y': 100, 'z': 100},
            'complexity': 'medium',
            'quantity': 1,
            'notes': 'Single component design'
        }]


def generate_part_prompts(parts_list, design_concept):
    """
    Stage 3: Generate refined 3D generation prompts for each part.
    
    Args:
        parts_list: List of part dicts from breakdown
        design_concept: Original design concept for context
    
    Returns:
        list: Parts list with added 'refined_prompt' field
    """
    system_prompt = """You are an expert at creating prompts for 3D model generation.

Your task is to create detailed, specific prompts for generating individual 3D parts.

Good prompts:
- Are specific and detailed
- Describe geometry clearly
- Mention key features and dimensions
- Include material/finish if relevant
- Are concise (under 200 characters)

Examples:
"Aerodynamic nose cone for model rocket, 120mm long, 50mm diameter, smooth pointed tip, hollow interior, mounting flange at base"
"Quadcopter motor arm, 200mm long carbon fiber tube, 15mm diameter, motor mount holes at end, center mounting plate"
"Robot gripper finger, articulated 3-segment design, 80mm total length, servo mounting points, textured grip surface"""

    for part in parts_list:
        try:
            user_prompt = f"""Create a detailed 3D generation prompt for this part:

Part: {part['name']}
Description: {part['description']}
Dimensions: {part['estimated_dimensions']['x']}mm x {part['estimated_dimensions']['y']}mm x {part['estimated_dimensions']['z']}mm
Material: {part['material_recommendation']}
Manufacturing: {part['manufacturing_method']}

Context: Part of a larger design - {design_concept.get('design_type', 'assembly')}

Generate a concise, detailed prompt (max 200 chars) for 3D model generation.
Return ONLY the prompt text, no JSON."""

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            refined_prompt = response.choices[0].message.content.strip()
            part['refined_prompt'] = refined_prompt
            
        except Exception as e:
            logger.error(f"Failed to generate prompt for part {part['name']}: {e}")
            # Fallback
            part['refined_prompt'] = f"{part['name']}, {part['description']}"
    
    return parts_list
