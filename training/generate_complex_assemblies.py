import json
import random
import math
from pathlib import Path

def generate_complex_assemblies(count=100):
    exs = []
    
    # 1. Planetary Gear Systems
    for _ in range(count // 3):
        sun_r = random.randint(10, 30)
        planet_r = random.randint(5, 15)
        # Standard calculation: Ring = Sun + 2*Planet
        ring_r = sun_r + 2 * planet_r
        thickness = random.randint(5, 15)
        num_planets = random.choice([3, 4, 5])
        
        prompt = f"A planetary gear system with a central sun gear (radius {sun_r}mm), {num_planets} planet gears (radius {planet_r}mm), and a ring gear (radius {ring_r}mm). Thickness {thickness}mm."
        
        # NOTE: Using simplified "teeth" via cutouts to avoid non-existent gear API
        # STRICT MATH: Ensuring 'import math' and usage of 'math.cos' etc
        code = f"""import cadquery as cq
import math

# Dimensions
sun_radius = {sun_r}
planet_radius = {planet_r}
ring_radius = {ring_r}
thickness = {thickness}
num_planets = {num_planets}

# Helper to look like a gear (cylinder with notch)
def make_gear(radius, width):
    c = cq.Workplane("XY").circle(radius).extrude(width)
    # Add a mock tooth cut for visual indication
    cut = cq.Workplane("XY").rect(2, 5).extrude(width)
    return c.cut(cut)

# 1. Sun Gear (Central)
sun_gear = make_gear(sun_radius, thickness)

# 2. Planet Gears
planets = cq.Workplane("XY")
orbit_radius = sun_radius + planet_radius
angle_step = 360 / num_planets

for i in range(num_planets):
    angle = i * angle_step
    # Calculate position (Using standard math library)
    x = orbit_radius * math.cos(math.radians(angle))
    y = orbit_radius * math.sin(math.radians(angle))
    
    planet = (
        cq.Workplane("XY")
        .center(x, y)
        .circle(planet_radius)
        .extrude(thickness)
    )
    planets = planets.union(planet)

# 3. Ring Gear (Outer Housing)
ring_gear = (
    cq.Workplane("XY")
    .circle(ring_radius + 5) # Outer rim
    .circle(ring_radius)     # Inner rim
    .extrude(thickness)
)

result = sun_gear.union(planets).union(ring_gear)"""
        exs.append({"prompt": prompt, "code": code})

    # 2. Electronics Enclosures
    for _ in range(count // 3):
        w = random.randint(50, 100)
        l = random.randint(80, 150)
        h = random.randint(20, 40)
        wall = random.randint(2, 4)
        
        prompt = f"Electronics enclosure {l}x{w}x{h}mm with {wall}mm walls. 4 corner posts and USB cutout."
        
        code = f"""import cadquery as cq

# Dimensions
length = {l}
width = {w}
height = {h}
wall_thickness = {wall}

# 1. Main Shell (Hollow Box)
shell = (
    cq.Workplane("XY")
    .box(length, width, height)
    .faces("+Z")
    .shell(wall_thickness)
)

# 2. Corner Posts
post_d = 6
posts = cq.Workplane("XY")
post_offsets = [
    (length/2 - 5, width/2 - 5),
    (-length/2 + 5, width/2 - 5),
    (length/2 - 5, -width/2 + 5),
    (-length/2 + 5, -width/2 + 5)
]

for x, y in post_offsets:
    post = (
        cq.Workplane("XY")
        .center(x, y)
        .circle(post_d/2)
        .extrude(height - 5) # Slightly shorter than case
    )
    posts = posts.union(post)

# 3. Cutout (USB)
cutout = (
    cq.Workplane("YZ") # Side face
    .workplane(offset=length/2) # Move to right face
    .center(0, 0)
    .rect(12, 6) # USB size
    .extrude(-10, combine="cut")
)

# Combine and cut
result = shell.union(posts).cut(cutout)"""
        exs.append({"prompt": prompt, "code": code})

    # 3. Heat Exchangers (FIXED v11: Additive Tubes + Baffles)
    for _ in range(count // 3):
        shell_d = random.randint(80, 150)
        length = random.randint(150, 300)
        tube_d = random.randint(8, 12)
        baffle_spacing = 50
        num_baffles = length // baffle_spacing
        
        prompt = f"Shell and tube heat exchanger. Shell dia {shell_d}mm, length {length}mm. 7 internal tubes (dia {tube_d}mm) in hex pattern. Baffles every {baffle_spacing}mm."
        
        code = f"""import cadquery as cq
import math

# Dimensions
shell_diameter = {shell_d}
length = {length}
tube_diameter = {tube_d}
baffle_spacing = {baffle_spacing}
num_baffles = {num_baffles}

# 1. Main Shell (Hollow Tube)
shell = (
    cq.Workplane("XY")
    .circle(shell_diameter/2)
    .circle(shell_diameter/2 - 2) # 2mm wall thickness
    .extrude(length)
)

# 2. Internal Tubes (Additive Hex pattern)
tubes = cq.Workplane("XY")
offsets = [(0,0)] # Center tube
r_offset = shell_diameter / 4
for i in range(6):
    angle = math.radians(i * 60)
    offsets.append((r_offset * math.cos(angle), r_offset * math.sin(angle)))

# Create tubes
for x, y in offsets:
    tube = (
        cq.Workplane("XY")
        .center(x, y)
        .circle(tube_diameter/2)
        .circle(tube_diameter/2 - 1) # 1mm wall thickness
        .extrude(length)
    )
    tubes = tubes.union(tube)

# 3. Baffles (Disks with holes for tubes)
baffles = cq.Workplane("XY")
for i in range(num_baffles):
    z_pos = (i + 1) * baffle_spacing
    if z_pos >= length: break
    
    # Create solid disk
    baffle = (
        cq.Workplane("XY")
        .workplane(offset=z_pos)
        .circle(shell_diameter/2 - 3) # Fit inside shell
        .extrude(2) # 2mm thick
    )
    
    # Cut holes for tubes in baffle
    for x, y in offsets:
        hole = (
            cq.Workplane("XY")
            .workplane(offset=z_pos)
            .center(x, y)
            .circle(tube_diameter/2 + 0.5) # Clearance
            .extrude(2)
        )
        baffle = baffle.cut(hole)
        
    baffles = baffles.union(baffle)

# Combine all: Shell + Tubes + Baffles
result = shell.union(tubes).union(baffles)"""
        exs.append({"prompt": prompt, "code": code})
        
    return exs

def main():
    print("⚙️ Generating complex assembly training data...")
    exs = generate_complex_assemblies(300)
    
    output_file = Path("training/data/complex_assemblies.jsonl")
    
    with open(output_file, 'w') as f:
        for ex in exs:
            f.write(json.dumps(ex) + '\n')
            
    # Also append to main train file
    train_file = Path("training/data/final_dataset/train.jsonl")
    with open(train_file, 'a') as f:
        for ex in exs:
            f.write(json.dumps(ex) + '\n')
            
    print(f"✅ Added {len(exs)} complex examples to training data.")

if __name__ == "__main__":
    main()
