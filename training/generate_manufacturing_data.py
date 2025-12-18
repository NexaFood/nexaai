import json
import random
import math
from pathlib import Path

def generate_bracket_variations(count=50):
    exs = []
    for _ in range(count):
        l = random.randint(30, 100)
        h = random.randint(20, 80)
        w = random.randint(20, 50)
        t = random.randint(3, 8)
        hole_dia = random.randint(4, 10)
        
        prompt = f"L-bracket {l}x{h}x{w} with thickness {t} and {hole_dia}mm mounting holes"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({l}, {w}, {t}, centered=(True, True, False))
    .faces(">Z")
    .workplane()
    .box({t}, {w}, {h}, centered=(False, True, False))
    .faces(">Z").workplane().rect({l-20}, {w-15}, forConstruction=True).vertices().hole({hole_dia})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_gear_variations(count=50):
    exs = []
    for _ in range(count):
        teeth = random.randint(8, 32)
        radius = random.randint(10, 40)
        thickness = random.randint(5, 20)
        bore = random.randint(4, 10)
        
        prompt = f"Spur gear with {teeth} teeth, radius {radius}, thickness {thickness}, bore {bore}mm"
        # Simplified gear logic for training (polygon with teeth)
        code = f"""import cadquery as cq
import math
result = cq.Workplane("XY").gear(teeth={teeth}, circular_pitch={2*math.pi*radius/teeth}, thickness={thickness}, bore_diameter={bore})"""
        # Note: cq.gear is sometimes in plugins, but let's use a standard robust way if we want to be sure
        # For simplicity and robustness in training, let's use a simpler polygon approximation
        code = f"""import cadquery as cq
# Simple gear-like profile
result = (
    cq.Workplane("XY")
    .circle({radius})
    .extrude({thickness})
    .faces(">Z")
    .workplane()
    .hole({bore})
)
# Adding teeth logic
for i in range({teeth}):
    angle = (360.0 / {teeth}) * i
    result = result.faces("|Z").workplane().transformed(rotate=(0, 0, angle)).rect(2, 2).extrude({thickness})
"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_cnc_plate_variations(count=100):
    exs = []
    for _ in range(count):
        l = random.randint(50, 200)
        w = random.randint(50, 200)
        t = random.randint(10, 30)
        fillet = random.randint(2, 10)
        holes = random.randint(4, 8)
        csk_dia = random.randint(6, 12)
        
        prompt = f"CNC base plate {l}x{w}x{t}, filleted corners r={fillet}, with {holes} countersunk holes"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({l}, {w}, {t})
    .edges("|Z")
    .fillet({fillet})
    .faces(">Z")
    .workplane()
    .rect({l-20}, {w-20}, forConstruction=True)
    .vertices()
    .cskHole({csk_dia/2}, {csk_dia}, 90)
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    all_exs = []
    all_exs.extend(generate_bracket_variations(50))
    all_exs.extend(generate_gear_variations(50))
    all_exs.extend(generate_cnc_plate_variations(100))
    
    random.shuffle(all_exs)
    train_count = int(len(all_exs) * 0.8)
    
    print(f"Adding {len(all_exs)} manufacturing examples...")
    
    with open(train_file, 'a') as f_train, open(val_file, 'a') as f_val:
        for i, ex in enumerate(all_exs):
            if i < train_count:
                f_train.write(json.dumps(ex) + '\n')
            else:
                f_val.write(json.dumps(ex) + '\n')
                
    print("Done.")

if __name__ == "__main__":
    main()
