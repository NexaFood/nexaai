import json
import random
from pathlib import Path

def generate_sketch_example():
    """Generates a single random sketching example."""
    shapes = ['rect', 'circle', 'slot', 'rpolygon', 'ellipse']
    shape = random.choice(shapes)
    
    if shape == 'rect':
        w = random.randint(5, 100)
        h = random.randint(5, 100)
        prompt = random.choice([
            f"Sketch a rectangle {w}x{h}",
            f"Draw a rectangle with width {w} and height {h}",
            f"Create a rectangular sketch {w}mm by {h}mm"
        ])
        code = f"import cadquery as cq\nresult = cq.Sketch().rect({w}, {h})"
        
    elif shape == 'circle':
        r = random.randint(2, 50)
        prompt = random.choice([
            f"Sketch a circle with radius {r}",
            f"Draw a circle r={r}",
            f"Create a circular sketch of radius {r}mm"
        ])
        code = f"import cadquery as cq\nresult = cq.Sketch().circle({r})"
        
    elif shape == 'slot':
        l = random.randint(10, 100)
        w = random.randint(2, 20)
        angle = random.choice([0, 45, 90])
        if angle == 0:
            prompt = f"Sketch a slot length {l} and width {w}"
            code = f"import cadquery as cq\nresult = cq.Sketch().slot({l}, {w})"
        else:
            prompt = f"Sketch a slot {l}x{w} rotated {angle} degrees"
            code = f"import cadquery as cq\nresult = cq.Sketch().slot({l}, {w}, angle={angle})"

    elif shape == 'rpolygon':
        n = random.randint(3, 8)
        r = random.randint(5, 50)
        sides_map = {3: "triangle", 4: "square", 5: "pentagon", 6: "hexagon", 8: "octagon"}
        name = sides_map.get(n, f"{n}-sided polygon")
        prompt = f"Sketch a regular {name} with radius {r}"
        code = f"import cadquery as cq\nresult = cq.Sketch().rpolygon({n}, {r})"
        
    elif shape == 'ellipse':
        w = random.randint(10, 100)
        h = random.randint(5, 50)
        prompt = f"Sketch an ellipse {w}x{h}"
        code = f"import cadquery as cq\nresult = cq.Sketch().ellipse({w}, {h})"

    return {"prompt": prompt, "code": code}

def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    print("🚀 Generating synthetic sketching data...")
    
    # Generate 400 for training
    print(f"  Generating 400 examples for {train_file.name}...")
    with open(train_file, 'a') as f:
        for _ in range(400):
            ex = generate_sketch_example()
            # Add synthetic marker to metadata if we were using it properly, 
            # but for now just raw append as requested.
            f.write(json.dumps(ex) + '\n')
            
    # Generate 80 for validation
    print(f"  Generating 80 examples for {val_file.name}...")
    with open(val_file, 'a') as f:
        for _ in range(80):
            ex = generate_sketch_example()
            f.write(json.dumps(ex) + '\n')
            
    print("✅ Done! Added 480 new sketching examples.")

if __name__ == "__main__":
    main()
