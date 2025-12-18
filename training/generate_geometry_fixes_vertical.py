import json
import random
import math
from pathlib import Path

def generate_vertical_assemblies(count=300):
    """
    Generates examples of vertical assemblies where components need to be stacked relative to Z.
    Focuses on 'standing on' and 'mounted on top' relationships.
    """
    exs = []
    
    # 1. Tanks on Legs (The specific fix for the user's issue)
    for _ in range(count // 3):
        vol_m3 = random.randint(5, 50)
        vol_mm3 = vol_m3 * 1e9
        
        # Determine logical dimensions
        radius = random.randint(1000, 2500)
        height = int(vol_mm3 / (math.pi * radius**2))
        
        leg_height = random.randint(600, 1500)
        leg_radius = random.randint(80, 200)
        
        prompt = f"A {vol_m3}m3 vertical storage tank standing on 4 legs ({leg_height}mm high). Bottom outlet flange."
        
        # Key logic: Tank is TRANSLATED up by leg_height
        # Legs encompass the space from 0 to leg_height
        
        code = f"""import cadquery as cq

# Dimensions
tank_radius = {radius}
tank_height = {height}
leg_height = {leg_height}
leg_radius = {leg_radius}

# 1. Create the Tank Body (elevated by leg_height)
# The tank bottom sits at Z = leg_height
tank = (
    cq.Workplane("XY")
    .workplane(offset=leg_height)  # ELEVATE TANK
    .circle(tank_radius)
    .extrude(tank_height)
)

# 2. Create Legs (standing on ground Z=0, up to Z=leg_height)
leg_offset = tank_radius * 0.7
legs = cq.Workplane("XY")
leg_positions = [
    ( leg_offset,  leg_offset),
    (-leg_offset,  leg_offset),
    ( leg_offset, -leg_offset),
    (-leg_offset, -leg_offset),
]

for x, y in leg_positions:
    leg = (
        cq.Workplane("XY")
        .center(x, y)
        .circle(leg_radius)
        .extrude(leg_height)
    )
    legs = legs.union(leg)

# 3. Create Bottom Flange (attached to tank bottom at Z=leg_height)
bottom_flange = (
    cq.Workplane("XY")
    .workplane(offset=leg_height)  # START AT TANK BOTTOM
    .circle(100) # DN80 approx
    .extrude(-50) # Extrude DOWNWARDS from tank bottom
)

result = tank.union(legs).union(bottom_flange)"""
        
        exs.append({"prompt": prompt, "code": code})
        
    # 2. Stacked Hoppers/Silos
    for _ in range(count // 3):
        h1 = random.randint(1000, 2000)
        h2 = random.randint(500, 1000)
        
        prompt = f"Two stacked cylinders, bottom one {h1}mm high, top one {h2}mm high."
        
        code = f"""import cadquery as cq

# Bottom cylinder (starts at Z=0)
bottom = cq.Workplane("XY").circle(500).extrude({h1})

# Top cylinder (starts at Z={h1}, on top of bottom one)
top = (
    cq.Workplane("XY")
    .workplane(offset={h1})
    .circle(300)
    .extrude({h2})
)

result = bottom.union(top)"""
        exs.append({"prompt": prompt, "code": code})

    return exs

def main():
    print("🚀 Generating vertical assembly fix data...")
    exs = generate_vertical_assemblies(300)
    
    output_file = Path("training/data/geometry_fixes_vertical.jsonl")
    
    with open(output_file, 'w') as f:
        for ex in exs:
            f.write(json.dumps(ex) + '\n')
            
    # Append to main train file
    train_file = Path("training/data/final_dataset/train.jsonl")
    with open(train_file, 'a') as f:
        for ex in exs:
            f.write(json.dumps(ex) + '\n')
            
    print(f"✅ Added {len(exs)} vertical stacking examples to training data.")

if __name__ == "__main__":
    main()
