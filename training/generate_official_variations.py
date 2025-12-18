import json
import random
from pathlib import Path

def generate_ex001_variations(count=100):
    exs = []
    for _ in range(count):
        l = random.randint(10, 100)
        h = random.randint(10, 100)
        t = random.randint(10, 100)
        prompt = f"Create a simple block with length {l}, height {h} and thickness {t}"
        code = f"""import cadquery as cq
result = cq.Workplane("XY").box({l}, {h}, {t})"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_ex002_variations(count=100):
    # Ex002_Block_With_Bored_Center_Hole.py
    exs = []
    for _ in range(count):
        l = random.randint(30, 120)
        h = random.randint(20, 100)
        t = random.randint(5, 50)
        hole_dia = random.randint(2, min(l, h) - 10)
        
        prompt = f"Block {l}x{h}x{t} with a {hole_dia}mm center hole"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({l}, {h}, {t})
    .faces(">Z")
    .workplane()
    .hole({hole_dia})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_ex003_variations(count=100):
    # Ex003_Pillow_Block_With_Counterbored_Holes.py
    # Simplified version or full logic? Let's do simplified based on title logic.
    exs = []
    for _ in range(count):
        l = random.randint(50, 150)
        w = random.randint(20, 80)
        t = random.randint(10, 40)
        cb_dia = random.randint(5, 15)
        hole_dia = cb_dia / 2
        
        prompt = f"Pillow block {l}x{w}x{t} with counterbored holes (dia {hole_dia}, cb {cb_dia})"
        # Reconstruct logical code for pillow block holes
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({l}, {w}, {t})
    .faces(">Z")
    .workplane()
    .rect({l-20}, {w/2}, forConstruction=True)
    .vertices()
    .cboreHole({hole_dia}, {cb_dia}, {t/2})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_ex004_variations(count=100):
    # Ex004_Extruded_Cylindrical_Plate.py
    exs = []
    for _ in range(count):
        r = random.randint(10, 60)
        t = random.randint(2, 20)
        hole_r = random.randint(2, r - 5)
        
        prompt = f"Extruded cylindrical plate radius {r}, thickness {t} with center hole r={hole_r}"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .circle({r})
    .circle({hole_r})
    .extrude({t})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_ex008_variations(count=100):
    # Ex008_Polygon_Creation.py
    exs = []
    for _ in range(count):
        sides = random.randint(3, 12)
        dia = random.randint(10, 100)
        h = random.randint(1, 50)
        
        prompt = f"Extruded polygon with {sides} sides, diameter {dia}, height {h}"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .polygon({sides}, {dia})
    .extrude({h})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_ex010_variations(count=100):
    # Ex010_Defining_an_Edge_with_a_Spline.py
    # This usually involves making a face from points and extruding.
    exs = []
    for _ in range(count):
        w = random.randint(2, 20)
        h = random.randint(2, 20)
        # Create random points for spline
        p1 = (random.randint(0, 10), 0)
        p2 = (random.randint(2, 10), random.randint(2, 10))
        p3 = (random.randint(5, 15), 0)
        
        prompt = f"Extruded spline shape passing through {p1}, {p2}, {p3} with thickness {h}"
        code = f"""import cadquery as cq
pts = [{p1}, {p2}, {p3}]
result = (
    cq.Workplane("XY")
    .moveTo(0,0)
    .lineTo(0, {w})
    .spline(pts, includeCurrent=True)
    .close()
    .extrude({h})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_ex011_variations(count=100):
    # Ex011_Mirroring_Symmetric_Geometry.py
    exs = []
    for _ in range(count):
        l = random.randint(10, 50)
        h = random.randint(10, 50)
        
        prompt = f"Mirrored L-shape via union, block {l}x{h}"
        code = f"""import cadquery as cq
r = cq.Workplane("XY").rect({l}, {h}).extrude(10).edges("|Y").fillet(2)
result = r.union(r.mirror("XY"))""" # Simplified logic
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_ex022_variations(count=100):
    # Ex022_Revolution.py
    exs = []
    for _ in range(count):
        r = random.randint(5, 20)
        h = random.randint(10, 50)
        angle = random.choice([90, 180, 270, 360])
        
        prompt = f"Revolve a rectangle {r}x{h} around Y axis by {angle} degrees"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .rect({r}, {h}, centered=False)
    .revolve({angle}, (-1,0,0), (1,0,0)) 
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs


def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    generators = [
        generate_ex001_variations,
        generate_ex002_variations,
        generate_ex003_variations,
        generate_ex004_variations,
        generate_ex008_variations,
        generate_ex010_variations,
        generate_ex011_variations,
        generate_ex022_variations
    ]
    
    print(f"🚀 Generating variations for {len(generators)} official examples...")
    
    total_train = 0
    total_val = 0
    
    with open(train_file, 'a') as f_train, open(val_file, 'a') as f_val:
        for gen in generators:
            # 100 total -> 80 train, 20 val
            examples = gen(100)
            
            # Split
            random.shuffle(examples)
            train_ex = examples[:80]
            val_ex = examples[80:]
            
            for ex in train_ex:
                f_train.write(json.dumps(ex) + '\n')
            total_train += len(train_ex)
                
            for ex in val_ex:
                f_val.write(json.dumps(ex) + '\n')
            total_val += len(val_ex)
            
            print(f"  Processed {gen.__name__}: +{len(train_ex)} Train, +{len(val_ex)} Val")

    print(f"\n✅ Done! Added {total_train} training and {total_val} validation examples.")

if __name__ == "__main__":
    main()
