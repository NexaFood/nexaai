import json
import random

def generate_plan():
    shapes = []
    
    # 1. Spheres (34 items)
    # Prompts: "Sphere {d}mm", "Sphere with diameter {d}mm", "{d}mm Sphere"
    for _ in range(34):
        d = random.randint(5, 50)
        r = d / 2
        if d % 2 == 0:
            r = int(r) # Clean integer if possible
        
        prompt_fmt = random.choice([
            f"Sphere {d}mm",
            f"Sphere with diameter {d}mm",
            f"{d}mm Sphere",
            f"Create a sphere of {d}mm diameter"
        ])
        
        code = f'import cadquery as cq\nresult = cq.Workplane("XY").sphere({r})'
        shapes.append({"prompt": prompt_fmt, "code": code, "type": "sphere"})

    # 2. Cylinders (33 items)
    # Prompts: "Cylinder {d}mm dia {h}mm high", "Cylinder d={d} h={h}", etc.
    for _ in range(33):
        d = random.randint(5, 40)
        h = random.randint(10, 60)
        r = d / 2
        if d % 2 == 0:
            r = int(r)
            
        prompt_fmt = random.choice([
            f"Cylinder {d}mm dia {h}mm high",
            f"Cylinder diameter {d}mm height {h}mm",
            f"{d}mm diameter cylinder, {h}mm tall",
            f"Cylinder d={d} h={h}"
        ])
        
        code = f'import cadquery as cq\nresult = cq.Workplane("XY").circle({r}).extrude({h})'
        shapes.append({"prompt": prompt_fmt, "code": code, "type": "cylinder"})

    # 3. Cubes (33 items)
    # Prompts: "Cube {s}mm", "Box {s}x{s}x{s}", etc.
    for _ in range(33):
        s = random.randint(5, 50)
        
        prompt_fmt = random.choice([
            f"Cube {s}mm",
            f"Cube side {s}mm",
            f"Box {s}x{s}x{s}mm",
            f"{s}mm Cube"
        ])
        
        code = f'import cadquery as cq\nresult = cq.Workplane("XY").box({s}, {s}, {s})'
        shapes.append({"prompt": prompt_fmt, "code": code, "type": "cube"})

    random.shuffle(shapes)
    
    with open('training_plan.json', 'w') as f:
        json.dump(shapes, f, indent=2)
    
    print(f"Generated {len(shapes)} items in training_plan.json")

if __name__ == "__main__":
    generate_plan()
