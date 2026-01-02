
import json
from clean_dataset import validate_line

# A line taken directly from validation.bak.clean (which was rejected)
corrupt_line = '{"instruction": "Create a cylindrical device r=52 h=107 with a screen 40x52 on the front.", "input": "", "output": "import cadquery as cq\\nresult = (\\n    cq.Workplane(\\"XY\\")\\n    .circle(52).extrude(107)\\n    # GEOMETRY LESSON: Do not sketch on curved face. Use separate plane.\\n    .Workplane(\\"XZ\\").transformed(offset=cq.Vector(0, 52, 107/2), rotate=cq.Vector(0, 0, 0))\\n    .rect(40, 52)\\n    .cutThruAll()\\n)"}'

print(f"Testing line: {corrupt_line[:50]}...")
is_valid, error = validate_line(1, corrupt_line, "debug_file")
print(f"Valid: {is_valid}")
print(f"Error: {error}")

if not is_valid:
    data = json.loads(corrupt_line)
    print(f"Keys found: {list(data.keys())}")
    if "instruction" in data:
        print(f"Instruction type: {type(data['instruction'])}")
    if "output" in data:
        print(f"Output type: {type(data['output'])}")
