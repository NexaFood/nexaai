
import random
import math
import json
from pathlib import Path

# Setup paths
OUTPUT_DIR = Path("training/data/final_dataset")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
VALIDATION_FILE = OUTPUT_DIR / "validation.jsonl"


def generate_tank_system(idx):
    """
    Generates a Storage Tank with inlet/outlet piping.
    Teaches: Connectivity, Vertical Stacking, Multi-part assemblies.
    """
    radius = random.uniform(500, 1500)
    height = random.uniform(2000, 4000)
    leg_height = random.uniform(500, 1000)
    
    prompt = f"A {int(radius*2)}mm diameter vertical storage tank, {int(height)}mm high, standing on 4 legs. It has a piping system with an inlet at the top and outlet at the bottom."
    
    # Generate the Code
    code = f"""import cadquery as cq
import math

# 1. Tank Body
radius = {radius}
height = {height}
leg_height = {leg_height}

# Main shell
tank = (
    cq.Workplane("XY")
    .workplane(offset=leg_height)
    .circle(radius)
    .extrude(height)
)

# Dished heads (Top and Bottom)
# Simplified as spheres for robustness
top_head = (
    cq.Workplane("XY")
    .workplane(offset=leg_height + height)
    .sphere(radius)
    .cut(
        cq.Workplane("XY")
        .workplane(offset=leg_height + height)
        .rect(radius*4, radius*4)
        .extrude(-radius)
    )
)

# 2. Legs (Structural)
leg_profile = 100
legs = cq.Workplane("XY")

for i in range(4):
    angle = 90 * i
    rad_angle = math.radians(angle)
    # Position legs at 45 deg offsets
    lx = (radius - 50) * math.cos(rad_angle + math.pi/4)
    ly = (radius - 50) * math.sin(rad_angle + math.pi/4)
    
    leg = (
        cq.Workplane("XY")
        .center(lx, ly)
        .rect(leg_profile, leg_profile)
        .extrude(leg_height)
    )
    legs = legs.union(leg)

# 3. Piping System
pipe_dia = 100
inlet_height = leg_height + height - 200
outlet_height = leg_height + 200

# Inlet Pipe (Vertical Riser)
inlet_pipe = (
    cq.Workplane("XY")
    .center(radius + 200, 0)
    .circle(pipe_dia/2)
    .circle(pipe_dia/2 - 5) # Hollow
    .extrude(inlet_height)
)

# Inlet Connection (Horizontal)
inlet_conn = (
    cq.Workplane("YZ")
    .workplane(offset=radius + 200)
    .center(0, inlet_height)
    .circle(pipe_dia/2)
    .circle(pipe_dia/2 - 5)
    .extrude(-(200 + 50)) # Connect to tank
)

# Outlet Pipe (Bottom side)
outlet_pipe = (
    cq.Workplane("YZ")
    .workplane(offset=radius)
    .center(0, outlet_height)
    .circle(pipe_dia/2)
    .circle(pipe_dia/2 - 5)
    .extrude(300) # Stick out
)

# Flange on outlet
outlet_flange = (
    cq.Workplane("YZ")
    .workplane(offset=radius + 300)
    .center(0, outlet_height)
    .circle(pipe_dia)
    .extrude(20)
)

# Union Everything
result = tank.union(top_head).union(legs).union(inlet_pipe).union(inlet_conn).union(outlet_pipe).union(outlet_flange)
"""
    return {"prompt": prompt, "code": code}

def generate_conveyor(idx):
    """
    Generates a Roller Conveyor.
    Teaches: Arrays, Repetition, structural frames.
    """
    length = random.uniform(2000, 5000)
    width = random.uniform(500, 1000)
    pitch = 150 # Roller pitch
    
    prompt = f"A roller conveyor system, {int(length)}mm long and {int(width)}mm wide. Rollers are spaced every {pitch}mm."
    
    code = f"""import cadquery as cq
import math

length = {length}
width = {width}
pitch = {pitch}
roller_dia = 50
frame_height = 100

# 1. Side Frames (C-Channels simplified as Box)
left_rail = (
    cq.Workplane("XY")
    .workplane(offset=600) # Conveyor height
    .center(-width/2, 0)
    .box(50, length, frame_height)
)

right_rail = (
    cq.Workplane("XY")
    .workplane(offset=600)
    .center(width/2, 0)
    .box(50, length, frame_height)
)

# 2. Legs
legs = cq.Workplane("XY")
num_legs = int(length / 1000) + 1
for i in range(num_legs):
    y_pos = -length/2 + i * (length / (num_legs-1))
    
    # Left Leg
    l_leg = (
        cq.Workplane("XY")
        .center(-width/2, y_pos)
        .rect(60, 60)
        .extrude(600)
    )
    # Right Leg
    r_leg = (
        cq.Workplane("XY")
        .center(width/2, y_pos)
        .rect(60, 60)
        .extrude(600)
    )
    legs = legs.union(l_leg).union(r_leg)

# 3. Rollers
rollers = cq.Workplane("XY")
num_rollers = int(length / pitch)

for i in range(num_rollers):
    y_pos = -length/2 + (pitch/2) + i * pitch
    
    roller = (
        cq.Workplane("YZ")
        .workplane(offset=-width/2 + 25)
        .center(0, 600 + frame_height/2) # Top of frame
        .circle(roller_dia/2)
        .extrude(width - 50)
    )
    rollers = rollers.union(roller)

result = left_rail.union(right_rail).union(legs).union(rollers)
"""
    return {"prompt": prompt, "code": code}

def generate_dataset(num_tanks, num_conveyors, filename, mode="w"):
    """Generates a dataset of industrial systems and appends to filename."""
    print(f"Generating {num_tanks + num_conveyors} examples to {filename}...")
    new_examples = []
    
    # 1. Tanks with Piping
    for i in range(num_tanks):
        new_examples.append(generate_tank_system(i))
        
    # 2. Conveyors
    for i in range(num_conveyors):
        new_examples.append(generate_conveyor(i))
        
    # Append to file
    with open(filename, 'a') as f:
        for ex in new_examples:
            # Format consistent with training data
            entry = {
                "instruction": ex["prompt"],
                "input": "",
                "output": ex["code"]
            }
            # Ensure proper JSONL formatting
            f.write(json.dumps(entry) + "\n")
            
    print(f"Successfully appended {len(new_examples)} examples to {filename.name}.")

def main():
    # 1. Training Data (500 items)
    generate_dataset(300, 200, TRAIN_FILE)
    
    # 2. Validation Data (50 items)
    # Important: Generate new examples, random seeds will differ
    generate_dataset(30, 20, VALIDATION_FILE)

if __name__ == "__main__":
    main()
