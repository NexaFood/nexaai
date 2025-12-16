import json
import random
from pathlib import Path

def generate_sketch_extrude_example():
    """Generates a single random sketch+extrude example."""
    shapes = ['rect', 'circle', 'slot', 'rpolygon', 'ellipse']
    shape = random.choice(shapes)
    height = random.randint(5, 50)
    
    if shape == 'rect':
        w = random.randint(5, 100)
        h = random.randint(5, 100)
        prompt = random.choice([
            f"Sketch a rectangle {w}x{h} and extrude it {height}mm",
            f"Create a box by extruding a {w}x{h} rectangular sketch by {height}",
            f"Extrude a rectangle of size {w}x{h} with height {height}"
        ])
        code = f"""import cadquery as cq
s = cq.Sketch().rect({w}, {h})
result = cq.Workplane("XY").placeSketch(s).extrude({height})"""
        
    elif shape == 'circle':
        r = random.randint(2, 50)
        prompt = random.choice([
            f"Sketch a circle with radius {r} and extrude {height}mm",
            f"Create a cylinder from a circular sketch r={r}, height={height}",
            f"Extrude a circle of radius {r} by {height}"
        ])
        code = f"""import cadquery as cq
s = cq.Sketch().circle({r})
result = cq.Workplane("XY").placeSketch(s).extrude({height})"""
        
    elif shape == 'slot':
        l = random.randint(10, 100)
        w = random.randint(2, 20)
        angle = random.choice([0, 45, 90])
        if angle == 0:
            prompt = f"Sketch a slot {l}x{w} and extrude {height}mm"
            code_sketch = f"cq.Sketch().slot({l}, {w})"
        else:
            prompt = f"Sketch a slot {l}x{w} at {angle} deg and extrude {height}mm"
            code_sketch = f"cq.Sketch().slot({l}, {w}, angle={angle})"
            
        code = f"""import cadquery as cq
s = {code_sketch}
result = cq.Workplane("XY").placeSketch(s).extrude({height})"""

    elif shape == 'rpolygon':
        n = random.randint(3, 8)
        r = random.randint(5, 50)
        sides_map = {3: "triangle", 4: "square", 5: "pentagon", 6: "hexagon", 8: "octagon"}
        name = sides_map.get(n, f"{n}-sided polygon")
        prompt = f"Extrude a {name} sketch (radius {r}) by {height}mm"
        code = f"""import cadquery as cq
s = cq.Sketch().rpolygon({n}, {r})
result = cq.Workplane("XY").placeSketch(s).extrude({height})"""
        
    elif shape == 'ellipse':
        w = random.randint(10, 100)
        h = random.randint(5, 50)
        prompt = f"Create an extruded ellipse {w}x{h} with height {height}"
        code = f"""import cadquery as cq
s = cq.Sketch().ellipse({w}, {h})
result = cq.Workplane("XY").placeSketch(s).extrude({height})"""

    return {"prompt": prompt, "code": code}

def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    print("🚀 Generating synthetic sketch+extrude data...")
    
    # Generate 400 for training
    print(f"  Generating 400 examples for {train_file.name}...")
    with open(train_file, 'a') as f:
        for _ in range(400):
            ex = generate_sketch_extrude_example()
            f.write(json.dumps(ex) + '\n')
            
    # Generate 80 for validation
    print(f"  Generating 80 examples for {val_file.name}...")
    with open(val_file, 'a') as f:
        for _ in range(80):
            ex = generate_sketch_extrude_example()
            f.write(json.dumps(ex) + '\n')
            
    print("✅ Done! Added 480 new sketch+extrude examples.")

if __name__ == "__main__":
    main()
