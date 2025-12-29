
import random
import math
import json
from pathlib import Path

# Setup paths
OUTPUT_DIR = Path("training/data/final_dataset")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
VALIDATION_FILE = OUTPUT_DIR / "validation.jsonl"

def generate_smart_hub(idx):
    """
    Generates a Smart Hub Display.
    Feature: Lofted base + Angled Screen.
    """
    # Randomize dimensions
    base_w = random.uniform(120, 180)
    base_d = random.uniform(80, 120)
    top_w = base_w * 0.8  # Tapered
    top_d = base_d * 0.6
    height = random.uniform(80, 120)
    screen_angle = 15 # degrees tilt
    
    prompt = f"A modern smart hub with a {int(base_w/25.4 * 2)} inch angled touchscreen display. It has a sleek tapered body and a fabric speaker base."
    
    code = f"""import cadquery as cq
import math

# Dimensions
base_w = {base_w}
base_d = {base_d}
top_w = {top_w}
top_d = {top_d}
height = {height}

# 1. Main Body (Lofted for Sleekness)
# Define bottom profile
bottom = (
    cq.Workplane("XY")
    .rect(base_w, base_d)
)

# Define top profile (offset and smaller)
top = (
    cq.Workplane("XY")
    .workplane(offset=height)
    .rect(top_w, top_d)
)

# Loft between them
body = (
    bottom.add(top)
    .toPending()
    .loft()
)

# 2. Fillet vertical edges for "soft" look
# Select edges aligned with Z axis
body = body.edges("|Z").fillet(10)

# 3. Screen Cutout (Angled)
# Create a workplane on the front face, then tilt it
# Or simpler: Cut from the front at an angle
screen_w = top_w * 0.9
screen_h = height * 0.7

screen_cut = (
    cq.Workplane("XZ")
    .workplane(offset=base_d/2) # Start at front
    .transformed(rotate=(15, 0, 0)) # Tilt back 15 deg
    .center(0, height/2)
    .rect(screen_w, screen_h)
    .extrude(-10) # Cut into body
)

body = body.cut(screen_cut)

# 4. Speaker Grille (Back)
# Array of small holes
grille = (
    cq.Workplane("XZ")
    .workplane(offset=-base_d/2) # Back face
    .center(0, height/3)
    .rarray(5, 5, 8, 4) # 8x4 grid, 5mm spacing
    .circle(1.5)
    .extrude(10) # Cut into body
)

result = body.cut(grille)
"""
    return {"prompt": prompt, "code": code}

def generate_thermostat(idx):
    """
    Generates a Round Smart Thermostat.
    Feature: Chamfered Cylinder + Rotary Ring.
    """
    dia = random.uniform(80, 120)
    thickness = random.uniform(20, 30)
    
    prompt = f"A round smart thermostat, {int(dia)}mm diameter. It has a rotary control ring and a central display."
    
    code = f"""import cadquery as cq

dia = {dia}
thickness = {thickness}

# 1. Main Puck
puck = (
    cq.Workplane("XY")
    .circle(dia/2)
    .extrude(thickness)
)

# Chamfer the back edge for "floating" look
puck = puck.edges("<Z").chamfer(5)

# 2. Rotary Ring (Outer)
# Cut a groove to separate ring
groove = (
    cq.Workplane("XY")
    .workplane(offset=thickness - 5)
    .circle(dia/2 - 5)
    .circle(dia/2 - 6)
    .extrude(5)
)
puck = puck.cut(groove)

# 3. Screen Area (Central Recess)
screen = (
    cq.Workplane("XY")
    .workplane(offset=thickness)
    .circle(dia/2 - 15)
    .extrude(-2) # Slight recess
)
puck = puck.cut(screen)

result = puck
"""
    return {"prompt": prompt, "code": code}

def generate_smart_speaker(idx):
    """
    Generates a Vertical Smart Speaker.
    Feature: Filleted Box + 360 Grille.
    """
    w = random.uniform(80, 100)
    h = random.uniform(150, 200)
    
    prompt = f"A tall rectangular smart speaker with rounded corners and 360-degree audio grille."
    
    code = f"""import cadquery as cq

w = {w}
h = {h}

# 1. Main Tower
body = (
    cq.Workplane("XY")
    .rect(w, w)
    .extrude(h)
)

# Heavy fillet on vertical edges (almost cylindrical)
body = body.edges("|Z").fillet(20)

# Top fillet (smaller)
body = body.edges(">Z").fillet(5)

# 2. 360 Grille (Slots on all sides)
# Only doing front/back for simplicity/stability in training
# Logic: Create a slot profile and cut
slot_w = w * 0.6
slot_h = 4

grille_cut = (
    cq.Workplane("XZ")
    .workplane(offset=w/2) # Front
    .rarray(1, 8, 1, 15) # Vertical stack of 15 slots
    .rect(slot_w, slot_h)
    .extrude(-w) # Cut all the way through
)

result = body.cut(grille_cut)
"""
    return {"prompt": prompt, "code": code}

def generate_dataset(num_hubs, num_therms, num_speakers, filename, mode="w"):
    print(f"Generating sleek electronics to {filename}...")
    new_examples = []
    
    for i in range(num_hubs):
        new_examples.append(generate_smart_hub(i))
    for i in range(num_therms):
        new_examples.append(generate_thermostat(i))
    for i in range(num_speakers):
        new_examples.append(generate_smart_speaker(i))
        
    with open(filename, 'a') as f:
        for ex in new_examples:
            entry = {
                "instruction": ex["prompt"],
                "input": "",
                "output": ex["code"]
            }
            f.write(json.dumps(entry) + "\n")
            
    print(f"Appended {len(new_examples)} examples to {filename.name}.")

def main():
    # Training: 5000 items total (Massive scale-up to fix bias)
    generate_dataset(2000, 1500, 1500, TRAIN_FILE)
    
    # Validation: 250 items
    generate_dataset(100, 75, 75, VALIDATION_FILE)

if __name__ == "__main__":
    main()
