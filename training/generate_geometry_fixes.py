import json
import random
from pathlib import Path

def generate_sphere_examples():
    examples = []
    # Diameters from 5 to 200
    for i in range(100):
        dia = random.randint(5, 200)
        prompts = [
            f"A sphere with diameter {dia}mm",
            f"sphere {dia}mm",
            f"Create a sphere of {dia}mm diameter",
            f"Generate a {dia}mm diameter ball",
            f"I need a sphere that is {dia}mm wide"
        ]
        prompt = random.choice(prompts)
        code = f"import cadquery as cq\n\nresult = cq.Workplane(\"XY\").sphere({dia/2})"
        examples.append({'prompt': prompt, 'code': code})
    
    # Radii
    for i in range(50):
        rad = random.randint(2, 100)
        prompts = [
            f"A sphere with radius {rad}mm",
            f"sphere radius {rad}mm",
            f"Create a sphere of {rad}mm radius"
        ]
        prompt = random.choice(prompts)
        code = f"import cadquery as cq\n\nresult = cq.Workplane(\"XY\").sphere({rad})"
        examples.append({'prompt': prompt, 'code': code})
    return examples

def generate_cylinder_examples():
    examples = []
    for i in range(150):
        dia = random.randint(5, 100)
        h = random.randint(10, 300)
        prompts = [
            f"A cylinder {dia}mm diameter, {h}mm tall",
            f"cylinder {dia}mm x {h}mm",
            f"Create a cylinder of {dia}mm diameter and {h}mm height",
            f"Generate a rod {dia}mm dia and {h}mm long"
        ]
        prompt = random.choice(prompts)
        code = f"import cadquery as cq\n\nresult = cq.Workplane(\"XY\").circle({dia/2}).extrude({h})"
        examples.append({'prompt': prompt, 'code': code})
    return examples

def generate_box_examples():
    examples = []
    for i in range(100):
        l = random.randint(10, 200)
        w = random.randint(10, 200)
        h = random.randint(2, 50)
        prompts = [
            f"A box {l}x{w}x{h}mm",
            f"Plate {l}mm long, {w}mm wide, {h}mm thick",
            f"Create a rectangular block {l}x{w}x{h}",
            f"Generate a {l}x{w}x{h} slab"
        ]
        prompt = random.choice(prompts)
        code = f"import cadquery as cq\n\nresult = cq.Workplane(\"XY\").box({l}, {w}, {h})"
        examples.append({'prompt': prompt, 'code': code})
    return examples

def generate_anti_hallucination_examples():
    """Examples with chatty prompts but clean code responses."""
    examples = []
    shapes = [
        ("sphere of 30mm", "cq.Workplane(\"XY\").sphere(15)"),
        ("box 50x50x10", "cq.Workplane(\"XY\").box(50, 50, 10)"),
        ("cylinder 10mm radius 40mm long", "cq.Workplane(\"XY\").circle(10).extrude(40)"),
        ("torus with 20mm major radius and 5mm minor radius", "cq.Workplane(\"XY\").torus(20, 5)")
    ]
    
    chatter = [
        "Please help me with this design.",
        "I'm new to CadQuery, can you show me how to do this?",
        "Provide only the code please.",
        "Include references and explanations.", # TRAP: We want it to ignore this and only provide code
        "Tell me how to build this step by step." # TRAP: Ignore
    ]
    
    for shape_prompt, shape_code in shapes:
        for chat in chatter:
            prompt = f"{shape_prompt}. {chat}"
            code = f"import cadquery as cq\n\nresult = {shape_code}"
            examples.append({'prompt': prompt, 'code': code})
            
    return examples

def main():
    print("🚀 Generating geometry fix data...")
    
    all_examples = []
    all_examples.extend(generate_sphere_examples())
    all_examples.extend(generate_cylinder_examples())
    all_examples.extend(generate_box_examples())
    all_examples.extend(generate_anti_hallucination_examples())
    
    random.shuffle(all_examples)
    
    output_file = Path("training/data/geometry_fixes.jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        for ex in all_examples:
            f.write(json.dumps(ex) + '\n')
            
    print(f"✅ Generated {len(all_examples)} examples in {output_file}")

if __name__ == "__main__":
    main()
