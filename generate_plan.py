import json
import random

# Templates for prompts
sphere_prompts = [
    "A sphere with diameter {D}mm",
    "{D}mm diameter sphere",
    "Sphere d={D}",
    "Create a sphere of {D}mm diameter",
    "Simple sphere {D}mm",
    "Sphere with a diameter of {D}mm"
]

cylinder_prompts = [
    "A cylinder with diameter {D}mm and height {H}mm",
    "Cylinder d={D} h={H}",
    "{D}mm diameter {H}mm tall cylinder",
    "Cylinder {D}x{H}mm",
    "Create a cylinder {D}mm wide and {H}mm high"
]

cube_prompts = [
    "A cube with side {S}mm",
    "{S}mm cube",
    "Cube s={S}",
    "Box {S}x{S}x{S}",
    "Create a cube of {S}mm"
]

examples = []

# Generate 33 Spheres
for _ in range(33):
    d = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100])
    prompt_template = random.choice(sphere_prompts)
    prompt = prompt_template.format(D=d)
    radius = d / 2
    if radius.is_integer():
        radius = int(radius)
    
    code = f'import cadquery as cq\nresult = cq.Workplane("XY").sphere({radius})'
    examples.append({"prompt": prompt, "code": code, "type": "sphere"})

# Generate 33 Cylinders
for _ in range(33):
    d = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100])
    h = random.choice([5, 10, 15, 20, 30, 40, 50, 80, 100])
    prompt_template = random.choice(cylinder_prompts)
    prompt = prompt_template.format(D=d, H=h)
    radius = d / 2
    if radius.is_integer():
        radius = int(radius)
    
    code = f'import cadquery as cq\nresult = cq.Workplane("XY").circle({radius}).extrude({h})'
    examples.append({"prompt": prompt, "code": code, "type": "cylinder"})

# Generate 34 Cubes
for _ in range(34):
    s = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100])
    prompt_template = random.choice(cube_prompts)
    prompt = prompt_template.format(S=s)
    
    code = f'import cadquery as cq\nresult = cq.Workplane("XY").box({s}, {s}, {s})'
    examples.append({"prompt": prompt, "code": code, "type": "cube"})

# Shuffle
random.shuffle(examples)

# Add IDs
for i, ex in enumerate(examples):
    ex['id'] = i + 1

with open('training_plan.json', 'w') as f:
    json.dump(examples, f, indent=2)

print(f"Generated {len(examples)} examples.")
