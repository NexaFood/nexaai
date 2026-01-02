
import json
import random
import math
from pathlib import Path

TRAIN_FILE = Path("train.jsonl")
VALIDATION_FILE = Path("validation.jsonl")

def generate_curved_screen_lesson(idx):
    """
    Lesson 1: Placing a screen on a curved surface (Cylinder/Sphere).
    teaches: Workplane(...).transformed(...) instead of .faces(...)
    """
    radius = random.randint(30, 80)
    height = random.randint(80, 150)
    screen_w = random.randint(30, radius)
    screen_h = random.randint(40, height-20)
    
    prompt = f"Create a cylindrical device r={radius} h={height} with a screen {screen_w}x{screen_h} on the front."
    
    # The "Correct" Logic: Offset plane
    code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .circle({radius}).extrude({height})
    # GEOMETRY LESSON: Do not sketch on curved face. Use separate plane.
    .Workplane("XZ").transformed(offset=cq.Vector(0, {radius}, {height}/2), rotate=cq.Vector(0, 0, 0))
    .rect({screen_w}, {screen_h})
    .cutThruAll()
)"""
    return {"prompt": prompt, "code": code}

def generate_robust_boolean_lesson(idx):
    """
    Lesson 2: Robust Booleans.
    teaches: Making cutters LARGER than the object to avoid coincident faces.
    """
    w = random.randint(50, 100)
    cut_w = w + random.randint(10, 20) # Cutter is wider
    
    prompt = f"Cut a slot through a box {w}x{w}x10."
    
    code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({w}, {w}, 10)
    .faces(">Z").workplane()
    # GEOMETRY LESSON: Cutter should be larger than object for clean boolean
    .rect({cut_w}, 5)
    .cutThruAll()
)"""
    return {"prompt": prompt, "code": code}

def generate_safe_fillet_lesson(idx):
    """
    Lesson 3: Safe Fillets.
    teaches: Selecting specific edges instead of .all()
    """
    prompt = "Create a box with rounded vertical corners."
    
    code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box(100, 100, 20)
    # GEOMETRY LESSON: Select only vertical edges for safe filleting
    .edges("|Z").fillet(5)
)"""
    return {"prompt": prompt, "code": code}

def generate_radial_selection_lesson(idx):
    """
    Lesson 4: Radial Edge Selection.
    teaches: Selecting circular edges on Cylinder/Cone using .faces(">Z").edges()
    instead of .edges("Z") or .edges("|Z") which selects the seam.
    """
    r = random.randint(20, 60)
    h = random.randint(50, 100)
    chamfer = random.randint(2, 5)
    
    prompt = f"Create a vertical cylinder r={r} h={h} with {chamfer}mm chamfers on the top and bottom."
    
    code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .circle({r}).extrude({h})
    # GEOMETRY LESSON: Use radial selection for cylinder caps. |Z is invalid (it's the seam).
    .faces(">Z or <Z").edges()
    .chamfer({chamfer})
)"""
    return {"prompt": prompt, "code": code}

def main():
    examples = []
    
    print("Generating Geometric Logic Lessons...")
    
    # Generate 1000 of each for Training
    train_examples = []
    for i in range(1000):
        train_examples.append(generate_curved_screen_lesson(i))
        train_examples.append(generate_safe_fillet_lesson(i))
        train_examples.append(generate_radial_selection_lesson(i))
    
    with open(TRAIN_FILE, 'a') as f:
        for ex in train_examples:
            entry = {
                "instruction": ex["prompt"],
                "input": "",
                "output": ex["code"]
            }
            f.write(json.dumps(entry) + "\n")
            
    # Generate 50 of each for Validation (Total 150)
    val_examples = []
    for i in range(50):
        val_examples.append(generate_curved_screen_lesson(i + 10000)) # Offset ID
        val_examples.append(generate_safe_fillet_lesson(i + 10000))
        val_examples.append(generate_radial_selection_lesson(i + 10000))
        
    with open(VALIDATION_FILE, 'a') as f:
        for ex in val_examples:
            entry = {
                "instruction": ex["prompt"],
                "input": "",
                "output": ex["code"]
            }
            f.write(json.dumps(entry) + "\n")

    print(f"Appended {len(train_examples)} lessons to {TRAIN_FILE}")
    print(f"Appended {len(val_examples)} lessons to {VALIDATION_FILE}")

if __name__ == "__main__":
    main()
