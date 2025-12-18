import json
import random
from pathlib import Path

def generate_rect_plate_variations(count=100):
    # Simple Rectangular Plate
    exs = []
    for _ in range(count):
        w = random.randint(10, 50)
        h = random.randint(10, 50)
        t = random.randint(1, 10)
        prompt = f"Simple rectangular plate {w}x{h}, thickness {t}"
        code = f"""import cadquery as cq
result = cq.Workplane("front").box({w}, {h}, {t})"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_plate_hole_variations(count=100):
    # Plate with Hole
    exs = []
    for _ in range(count):
        l = random.randint(30, 100)
        h = random.randint(20, 80)
        t = random.randint(5, 20)
        dia = random.randint(5, min(l, h) - 10)
        
        prompt = f"Rectangular plate {l}x{h}x{t} with {dia}mm center hole"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({l}, {h}, {t})
    .faces(">Z")
    .workplane()
    .hole({dia})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_prismatic_variations(count=100):
    # An extruded prismatic solid
    exs = []
    for _ in range(count):
        d = random.randint(20, 60)
        w = random.randint(5, 20)
        h = random.randint(5, 20)
        ext = random.randint(5, 30)
        
        prompt = f"Extruded prismatic solid: circle dia {d}, rect {w}x{h}, extruded {ext}"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("front")
    .circle({d/2})
    .rect({w}, {h})
    .extrude({ext})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_profile_variations(count=100):
    # Building Profiles using lines and arcs
    exs = []
    for _ in range(count):
        l1 = random.randint(10, 50)
        h1 = random.randint(5, 20)
        ext = random.randint(2, 10)
        # Randomize arc point slightly
        arc_x = l1/2
        arc_y = h1 * 1.5
        
        prompt = f"Profile with lines and arc, L={l1} H={h1}, extruded {ext}"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("front")
    .lineTo({l1}, 0)
    .lineTo({l1}, {h1})
    .threePointArc(({arc_x}, {arc_y}), (0.0, {h1}))
    .close()
    .extrude({ext})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_pillow_block_variations(count=100):
    # Parametric Bearing Pillow Block
    exs = []
    for _ in range(count):
        l = random.randint(40, 100)
        h = random.randint(30, 80)
        t = random.randint(10, 30)
        bearing_dia = random.randint(10, 30)
        padding = random.randint(5, 10)
        
        prompt = f"Bearing pillow block {l}x{h}x{t}, bearing dia {bearing_dia}"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({l}, {h}, {t})
    .faces(">Z")
    .workplane()
    .hole({bearing_dia})
    .faces(">Z")
    .workplane()
    .rect({l-padding}, {h-padding}, forConstruction=True)
    .vertices()
    .cboreHole(2.4, 4.4, 2.1)
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_bottle_variations(count=100):
    # The Classic OCC Bottle
    exs = []
    for _ in range(count):
        l = random.randint(20, 50)
        w = random.randint(5, 15)
        t = random.randint(2, 5)
        height = random.randint(20, 60)
        neck_r = random.randint(2, 5)
        
        prompt = f"Classic OCC Bottle L={l} W={w} T={t} Height={height}"
        code = f"""import cadquery as cq
s = cq.Workplane("XY")
p = (
    s.center(-{l}/2.0, 0)
    .vLine({w}/2.0)
    .threePointArc(({l}/2.0, {w}/2.0 + {t}), ({l}, {w}/2.0))
    .vLine(-{w}/2.0)
    .mirrorX()
    .extrude({height}, True)
)
p.faces(">Z").workplane().circle({neck_r}).extrude(2.0, True)
result = p.faces(">Z").shell(0.3)"""
        exs.append({"prompt": prompt, "code": code})
    return exs


def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    generators = [
        generate_rect_plate_variations,
        generate_plate_hole_variations,
        generate_prismatic_variations,
        generate_profile_variations,
        generate_pillow_block_variations,
        generate_bottle_variations
    ]
    
    print(f"🚀 Generating variations for {len(generators)} documentation examples...")
    
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
