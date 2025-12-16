import json
import random

def generate_plan():
    plan = []
    
    # 1. Double Boxes / Squares (100 items)
    # Variations: side-by-side, stacked, different sizes
    prompt_templates_boxes = [
        "Two boxes, one {w1}x{l1}x{h1} at origin, another {w2}x{l2}x{h2} at ({x},{y},{z})",
        "A base box {w1}x{l1}x{h1} with a smaller box {w2}x{l2}x{h2} on top",
        "Create a cube of side {s1} and place a box {w2}x{l2}x{h2} next to it at x={x}",
        "Two cubes: side {s1} at origin and side {s2} at ({x}, {y})",
        "Union of a {w1}x{l1}x{h1} box and a {w2}x{l2}x{h2} box translated by ({x}, {y}, {z})"
    ]
    
    for _ in range(100):
        template = random.choice(prompt_templates_boxes)
        
        # Random dims
        w1, l1, h1 = random.randint(10, 50), random.randint(10, 50), random.randint(5, 30)
        w2, l2, h2 = random.randint(5, 20), random.randint(5, 20), random.randint(5, 20)
        s1, s2 = random.randint(10, 40), random.randint(5, 20)
        x, y, z = random.randint(10, 50), random.randint(10, 50), h1 
        
        prompt = template.format(w1=w1, l1=l1, h1=h1, w2=w2, l2=l2, h2=h2, s1=s1, s2=s2, x=x, y=y, z=z)
        
        # Decide code based on template logic roughly (simplified for robustness)
        if "Union" in prompt:
            code = f"import cadquery as cq\nresult = cq.Workplane('XY').box({w1}, {l1}, {h1}).union(cq.Workplane('XY').box({w2}, {l2}, {h2}).translate(({x}, {y}, {z})))"
        elif "on top" in prompt:
             # Stacked
             code = f"import cadquery as cq\nresult = cq.Workplane('XY').box({w1}, {l1}, {h1}).faces('>Z').workplane().box({w2}, {l2}, {h2})"
        elif "Two cubes" in prompt:
             code = f"import cadquery as cq\nbox1 = cq.Workplane('XY').box({s1}, {s1}, {s1})\nbox2 = cq.Workplane('XY').box({s2}, {s2}, {s2}).translate(({x}, {y}, 0))\nresult = box1.union(box2)"
        elif "Create a cube" in prompt:
             code = f"import cadquery as cq\nbox1 = cq.Workplane('XY').box({s1}, {s1}, {s1})\nbox2 = cq.Workplane('XY').box({w2}, {l2}, {h2}).translate(({x}, 0, 0))\nresult = box1.union(box2)"
        else:
            # Default side by side
            code = f"import cadquery as cq\nbox1 = cq.Workplane('XY').box({w1}, {l1}, {h1})\nbox2 = cq.Workplane('XY').box({w2}, {l2}, {h2}).translate(({x}, {y}, {z}))\nresult = box1.union(box2)"
            
        plan.append({"prompt": prompt, "code": code})

    # 2. Cylinders (100 items)
    prompt_templates_cyl = [
        "Cylinder with diameter {d} and height {h}",
        "A {h}mm tall cylinder with radius {r}",
        "Cylinder dia {d}, height {h}, positioned at ({x}, {y})",
        "Create a simple cylinder r={r} h={h}",
        "Vertical rod diameter {d} length {h}"
    ]
    
    for _ in range(100):
        template = random.choice(prompt_templates_cyl)
        d = random.randint(5, 50)
        r = d / 2
        h = random.randint(10, 100)
        x, y = random.randint(-50, 50), random.randint(-50, 50)
        
        prompt = template.format(d=d, r=r, h=h, x=x, y=y)
        
        if "at (" in prompt or "positioned" in prompt:
             code = f"import cadquery as cq\nresult = cq.Workplane('XY').circle({r}).extrude({h}).translate(({x}, {y}, 0))"
        else:
             code = f"import cadquery as cq\nresult = cq.Workplane('XY').circle({r}).extrude({h})"
             
        plan.append({"prompt": prompt, "code": code})
        
    # 3. Spheres (100 items)
    prompt_templates_sphere = [
        "Sphere with radius {r}",
        "A {d}mm diameter sphere",
        "Sphere r={r} at ({x}, {y}, {z})",
        "Ball with diameter {d}",
        "Create a sphere of size {r} positioned at origin"
    ]
    
    for _ in range(100):
        template = random.choice(prompt_templates_sphere)
        d = random.randint(5, 50)
        r = d / 2
        x, y, z = random.randint(-20, 20), random.randint(-20, 20), random.randint(0, 20)
        
        prompt = template.format(d=d, r=r, x=x, y=y, z=z)
        
        if "at (" in prompt:
             code = f"import cadquery as cq\nresult = cq.Workplane('XY').sphere({r}).translate(({x}, {y}, {z}))"
        else:
             code = f"import cadquery as cq\nresult = cq.Workplane('XY').sphere({r})"
             
        plan.append({"prompt": prompt, "code": code})
        
    return plan

if __name__ == "__main__":
    plan = generate_plan()
    with open("extended_training_plan.json", "w") as f:
        json.dump(plan, f, indent=2)
    print(f"Generated {len(plan)} items in extended_training_plan.json")
