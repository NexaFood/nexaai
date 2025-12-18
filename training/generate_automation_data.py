import json
import random
from pathlib import Path

def generate_tank_variations(count=100):
    exs = []
    for _ in range(count):
        radius = random.randint(500, 2000) # mm
        height = random.randint(1000, 5000)
        wall = random.randint(5, 20)
        dome_h = radius / 4
        
        prompt = f"Storage tank radius {radius}mm, height {height}mm, wall thickness {wall}mm with domed top"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .circle({radius})
    .extrude({height})
    .faces(">Z")
    .sphere({radius})
    .shell({wall})
)"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def generate_pipe_variations(count=100):
    exs = []
    for _ in range(count):
        dia = random.randint(50, 200)
        l1 = random.randint(200, 1000)
        l2 = random.randint(200, 1000)
        t = random.randint(2, 10)
        
        prompt = f"90-degree pipe elbow dia {dia}mm, segments {l1}mm and {l2}mm, thickness {t}mm"
        code = f"""import cadquery as cq
path = cq.Workplane("XZ").lineTo(0, {l1}).threePointArc(({l1/2}, {l1+l1/2}), ({l1}, {l1+l1/2})).lineTo({l1+l2}, {l1+l1/2})
result = cq.Workplane("XY").circle({dia/2}).sweep(path, makeSolid=True).faces(">X").shell({t})
"""
        exs.append({"prompt": prompt, "code": code})
    return exs

def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    all_exs = []
    all_exs.extend(generate_tank_variations(100))
    all_exs.extend(generate_pipe_variations(100))
    
    random.shuffle(all_exs)
    train_count = int(len(all_exs) * 0.8)
    
    print(f"Adding {len(all_exs)} automation examples...")
    
    with open(train_file, 'a') as f_train, open(val_file, 'a') as f_val:
        for i, ex in enumerate(all_exs):
            if i < train_count:
                f_train.write(json.dumps(ex) + '\n')
            else:
                f_val.write(json.dumps(ex) + '\n')
                
    print("Done.")

if __name__ == "__main__":
    main()
