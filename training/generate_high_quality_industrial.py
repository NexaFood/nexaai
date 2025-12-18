import json
import random
import math
from pathlib import Path

def generate_industrial_data(count=500):
    exs = []
    
    # 1. Tanks (Storage, Pressurized)
    for _ in range(count // 4):
        r = random.randint(100, 1000)
        h = random.randint(500, 3000)
        t = random.randint(5, 20)
        
        prompt = f"Industrial storage tank with radius {r}mm and height {h}mm, wall thickness {t}mm"
        # Using double braces {{ }} for literal braces in f-string
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .circle({r})
    .extrude({h})
    .faces(">Z")
    .sphere({r})
    .shell({t})
)"""
        exs.append({"prompt": prompt, "code": code})

    # 2. Piping/Manifolds
    for _ in range(count // 4):
        dia = random.randint(50, 150)
        spacing = random.randint(200, 600)
        num_branches = random.randint(2, 6)
        
        prompt = f"Piping manifold with a central pipe (dia {dia}mm) and {num_branches} branch pipes spaced {spacing}mm apart"
        center_expr = f"(i+1)*{spacing} - ({num_branches}+1)*{spacing}/2"
        code = f"""import cadquery as cq
result = cq.Workplane("XY").circle({dia/2}).extrude({(num_branches + 1) * spacing})
for i in range({num_branches}):
    result = result.faces(">X").workplane(offset=0).center({center_expr}, 0).circle({dia/4}).extrude(50)
result = result.faces("|Z").shell(2)"""
        exs.append({"prompt": prompt, "code": code})

    # 3. Precision Plates / CNC
    for _ in range(count // 4):
        l = random.randint(100, 400)
        grid = random.randint(4, 9)
        h_dia = random.randint(5, 15)
        
        prompt = f"CNC mounting plate {l}x{l}x20mm with a {grid}x{grid} grid of {h_dia}mm holes"
        code = f"""import cadquery as cq
result = (
    cq.Workplane("XY")
    .box({l}, {l}, 20)
    .faces(">Z")
    .workplane()
    .rect({l-40}, {l-40}, forConstruction=True)
    .vertices()
    .hole({h_dia})
    .edges("|Z")
    .fillet(5)
)"""
        exs.append({"prompt": prompt, "code": code})

    # 4. Heat Sinks
    for _ in range(count // 4):
        base = random.randint(50, 150)
        num_fins = random.randint(10, 25)
        fin_h = random.randint(15, 40)
        
        prompt = f"Parametric heat sink with {base}mm square base and {num_fins} cooling fins {fin_h}mm high"
        center_expr = f"(i * ({base}/{num_fins})) - ({base}/2)"
        code = f"""import cadquery as cq
result = cq.Workplane("XY").box({base}, {base}, 5)
for i in range({num_fins}):
    offset = {center_expr}
    result = result.faces(">Z").workplane().center(offset, 0).rect(2, {base}).extrude({fin_h})
"""
        exs.append({"prompt": prompt, "code": code})

    return exs

def main():
    exs = generate_industrial_data(500)
    random.shuffle(exs)
    
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    
    print(f"Adding {len(exs)} high-quality industrial examples to {train_file}...")
    
    with open(train_file, 'a') as f:
        for ex in exs:
            f.write(json.dumps(ex) + '\n')
            
    print("Optimization complete.")

if __name__ == "__main__":
    main()
