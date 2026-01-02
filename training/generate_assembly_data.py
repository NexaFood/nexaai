import random
import json
import math
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("training/data_v17")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_FILE = Path("train.jsonl")
VALIDATION_FILE = Path("validation.jsonl")

def generate_box_and_lid(i):
    """
    Lesson 5.1: Basic Two-Part Assembly (Box + Lid)
    Teaches: Variable separation, cq.Assembly, Location offets
    """
    width = random.randint(50, 150)
    depth = random.randint(50, 150)
    height = random.randint(30, 80)
    wall = random.randint(2, 5)
    lid_thickness = random.randint(2, 5)
    
    prompt = f"Design a box {width}x{depth}x{height} with {wall}mm walls and a separate lid {lid_thickness}mm thick."
    
    code = f"""import cadquery as cq

# part 1: The Box
box = (
    cq.Workplane("XY")
    .box({width}, {depth}, {height})
    .faces(">Z")
    .shell(-{wall})
)

# part 2: The Lid
lid = (
    cq.Workplane("XY")
    .box({width}, {depth}, {lid_thickness})
)

# Assembly
result = cq.Assembly()
result.add(box, name="box", color=cq.Color("silver"))
result.add(lid, name="lid", loc=cq.Location(cq.Vector(0, 0, {height/2 + lid_thickness/2})), color=cq.Color("red"))
"""
    return {"instruction": prompt, "input": "", "output": code}

def generate_hinge_assembly(i):
    """
    Lesson 5.2: Multi-Item Assembly (Base + Arm + Pin)
    Teaches: 3+ parts, rotation in location, clear variable naming
    """
    base_w = random.randint(40, 60)
    arm_l = random.randint(40, 80)
    pin_r = random.randint(3, 6)
    
    prompt = f"Create a simple hinge assembly with a {base_w}mm wide base, a {arm_l}mm long arm, and a {pin_r}mm radius pin."
    
    code = f"""import cadquery as cq

# 1. Base Plate
base = (
    cq.Workplane("XY")
    .box({base_w}, {base_w}, 5)
    .faces(">Z").workplane()
    .tag("top")
    .rect({base_w}, 10).extrude(15)  # Hinge knuckle
    .faces(">Y").workplane()
    .circle({pin_r}).cutThruAll()    # Pin hole
)

# 2. Moving Arm
arm = (
    cq.Workplane("XY")
    .box({base_w-2}, {arm_l}, 5)
    .faces("<Y").workplane()
    .tag("knuckle")
    .rect({base_w-2}, 10).extrude(10)
    .faces(">Y").workplane()
    .circle({pin_r}).cutThruAll()
)

# 3. Pin
pin = (
    cq.Workplane("YZ")
    .circle({pin_r})
    .extrude({base_w + 10})
)

# Assembly
result = cq.Assembly()
result.add(base, name="base", color=cq.Color("gray"))
result.add(arm, name="arm", loc=cq.Location(cq.Vector(0, 0, 10)), color=cq.Color("blue"))
result.add(pin, name="pin", loc=cq.Location(cq.Vector(-{base_w/2 + 5}, 0, 10)), color=cq.Color("yellow"))
"""
    return {"instruction": prompt, "input": "", "output": code}

def main():
    print("Generating v17 Assembly Data...")
    
    # 1. Box and Lid (1000 examples)
    train_data = []
    val_data = []
    
    print("  - Generating Boxes & Lids...")
    for i in range(1000):
        train_data.append(generate_box_and_lid(i))
    for i in range(50):
        val_data.append(generate_box_and_lid(i))
        
    # 2. Hinges (1000 examples)
    print("  - Generating Hinges...")
    for i in range(1000):
        train_data.append(generate_hinge_assembly(i))
    for i in range(50):
        val_data.append(generate_hinge_assembly(i))
        
    # Write to files
    print(f"  - Appending {len(train_data)} to {TRAIN_FILE}...")
    with open(TRAIN_FILE, 'a') as f:
        for entry in train_data:
            f.write(json.dumps(entry) + "\n")
            
    print(f"  - Appending {len(val_data)} to {VALIDATION_FILE}...")
    with open(VALIDATION_FILE, 'a') as f:
        for entry in val_data:
            f.write(json.dumps(entry) + "\n")
            
    print("Done.")

if __name__ == "__main__":
    main()
