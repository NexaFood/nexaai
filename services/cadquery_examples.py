"""
High-quality CadQuery examples for AI training and prompting.
Collected from official CadQuery documentation.
"""

CADQUERY_EXAMPLES = [
    {
        "name": "Simple Box",
        "description": "Basic rectangular box",
        "code": """import cadquery as cq

result = cq.Workplane("XY").box(50, 50, 10)"""
    },
    {
        "name": "Box with Hole",
        "description": "Box with centered hole through top face",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(80, 60, 10)
    .faces(">Z")
    .workplane()
    .hole(22)
)"""
    },
    {
        "name": "Cylinder",
        "description": "Simple cylinder",
        "code": """import cadquery as cq

result = cq.Workplane("XY").circle(10).extrude(50)"""
    },
    {
        "name": "Cylinder with Hole",
        "description": "Hollow cylinder",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle(20)
    .circle(15)
    .extrude(50)
)"""
    },
    {
        "name": "Plate with Multiple Holes",
        "description": "Plate with holes at specific positions",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(100, 100, 5)
    .faces(">Z")
    .workplane()
    .pushPoints([(25, 25), (-25, 25), (25, -25), (-25, -25)])
    .hole(10)
)"""
    },
    {
        "name": "L-Bracket",
        "description": "L-shaped bracket using polyline",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .polyline([(0, 0), (50, 0), (50, 10), (10, 10), (10, 50), (0, 50)])
    .close()
    .extrude(5)
)"""
    },
    {
        "name": "Rounded Box",
        "description": "Box with filleted edges",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(60, 40, 20)
    .edges("|Z")
    .fillet(2)
)"""
    },
    {
        "name": "Tube",
        "description": "Tube with specific wall thickness",
        "code": """import cadquery as cq

outer_radius = 20
wall_thickness = 2
height = 50

result = (
    cq.Workplane("XY")
    .circle(outer_radius)
    .circle(outer_radius - wall_thickness)
    .extrude(height)
)"""
    },
    {
        "name": "Mounting Plate",
        "description": "Plate with corner mounting holes",
        "code": """import cadquery as cq

width = 100
height = 80
thickness = 5
hole_diameter = 5
corner_offset = 10

result = (
    cq.Workplane("XY")
    .box(width, height, thickness)
    .faces(">Z")
    .workplane()
    .pushPoints([
        (width/2 - corner_offset, height/2 - corner_offset),
        (-width/2 + corner_offset, height/2 - corner_offset),
        (width/2 - corner_offset, -height/2 + corner_offset),
        (-width/2 + corner_offset, -height/2 + corner_offset)
    ])
    .hole(hole_diameter)
)"""
    },
    {
        "name": "Hexagonal Prism",
        "description": "Six-sided prism",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .polygon(6, 20)
    .extrude(30)
)"""
    },
    {
        "name": "Cone",
        "description": "Conical shape using loft",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle(20)
    .workplane(offset=50)
    .circle(5)
    .loft()
)"""
    },
    {
        "name": "Sphere",
        "description": "Spherical shape",
        "code": """import cadquery as cq

result = cq.Workplane("XY").sphere(15)"""
    },
    {
        "name": "Countersunk Hole",
        "description": "Hole with countersink for screw head",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(50, 50, 10)
    .faces(">Z")
    .workplane()
    .cskHole(5, 10, 82)
)"""
    },
    {
        "name": "Counterbored Hole",
        "description": "Hole with counterbore for bolt head",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(50, 50, 10)
    .faces(">Z")
    .workplane()
    .cboreHole(5, 10, 5)
)"""
    },
    {
        "name": "Shell",
        "description": "Hollow box with open top",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(60, 40, 30)
    .faces(">Z")
    .shell(-2)
)"""
    },
    {
        "name": "T-Slot Profile",
        "description": "T-slot extrusion profile",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .rect(20, 20)
    .extrude(100)
    .faces(">Z")
    .workplane()
    .rect(8, 20)
    .cutBlind(-10)
    .faces(">Z")
    .workplane(offset=-10)
    .rect(16, 8)
    .cutBlind(-10)
)"""
    },
    {
        "name": "Mirrored Part",
        "description": "Create symmetric part using mirror",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .rect(30, 20)
    .extrude(5)
    .faces(">Z")
    .workplane()
    .center(10, 0)
    .rect(10, 10)
    .extrude(10)
    .mirrorY()
)"""
    },
    {
        "name": "Chamfered Box",
        "description": "Box with chamfered edges",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(50, 50, 20)
    .edges("|Z")
    .chamfer(2)
)"""
    },
    {
        "name": "Slot",
        "description": "Rectangular slot in a plate",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(100, 60, 10)
    .faces(">Z")
    .workplane()
    .slot2D(40, 10)
    .cutThruAll()
)"""
    },
    {
        "name": "Gear Blank",
        "description": "Basic gear blank with center hole",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle(30)
    .extrude(10)
    .faces(">Z")
    .workplane()
    .hole(10)
)"""
    },
    {
        "name": "Standoff",
        "description": "Cylindrical standoff with threaded holes",
        "code": """import cadquery as cq

height = 20
diameter = 10
hole_diameter = 4

result = (
    cq.Workplane("XY")
    .circle(diameter/2)
    .extrude(height)
    .faces(">Z or <Z")
    .workplane()
    .hole(hole_diameter)
)"""
    },
    {
        "name": "Washer",
        "description": "Simple washer",
        "code": """import cadquery as cq

outer_diameter = 20
inner_diameter = 10
thickness = 2

result = (
    cq.Workplane("XY")
    .circle(outer_diameter/2)
    .circle(inner_diameter/2)
    .extrude(thickness)
)"""
    },
    {
        "name": "U-Channel",
        "description": "U-shaped channel profile",
        "code": """import cadquery as cq

width = 40
height = 30
thickness = 3
length = 100

result = (
    cq.Workplane("XY")
    .rect(width, height)
    .extrude(length)
    .faces(">Z")
    .shell(-thickness)
    .faces("<Y")
    .workplane()
    .split(keepTop=True)
)"""
    },
    {
        "name": "Angled Bracket",
        "description": "90-degree bracket with mounting holes",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .rect(50, 50)
    .extrude(5)
    .faces(">Z")
    .workplane()
    .transformed(rotate=(90, 0, 0))
    .rect(50, 50)
    .extrude(5)
    .faces(">Z or >Y")
    .workplane()
    .pushPoints([(15, 15), (-15, 15), (15, -15), (-15, -15)])
    .hole(5)
)"""
    },
    {
        "name": "Knob",
        "description": "Cylindrical knob with grip grooves",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle(15)
    .extrude(20)
    .faces(">Z")
    .workplane()
    .circle(5)
    .cutBlind(-10)
    .faces("<Z")
    .workplane()
    .pushPoints([(0, 12), (0, -12), (12, 0), (-12, 0)])
    .circle(2)
    .cutThruAll()
)"""
    },
    {
        "name": "Bushing",
        "description": "Cylindrical bushing with flange",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle(20)
    .extrude(5)
    .faces(">Z")
    .workplane()
    .circle(15)
    .extrude(20)
    .faces(">Z or <Z")
    .workplane()
    .hole(10)
)"""
    },
    {
        "name": "Spacer Ring",
        "description": "Ring spacer with specific dimensions",
        "code": """import cadquery as cq

outer_d = 30
inner_d = 20
height = 10

result = (
    cq.Workplane("XY")
    .circle(outer_d/2)
    .circle(inner_d/2)
    .extrude(height)
)"""
    },
    {
        "name": "Rectangular Tube",
        "description": "Hollow rectangular tube",
        "code": """import cadquery as cq

outer_width = 40
outer_height = 30
wall_thickness = 3
length = 100

result = (
    cq.Workplane("XY")
    .rect(outer_width, outer_height)
    .extrude(length)
    .faces(">Z")
    .shell(-wall_thickness)
)"""
    },
    {
        "name": "Cap",
        "description": "End cap with lip",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle(25)
    .extrude(3)
    .faces(">Z")
    .workplane()
    .circle(20)
    .extrude(15)
)"""
    },
    {
        "name": "Pulley",
        "description": "Simple pulley with groove",
        "code": """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle(30)
    .extrude(20)
    .faces(">Z")
    .workplane()
    .hole(10)
    .faces(">Z")
    .workplane(offset=-10)
    .circle(25)
    .cutBlind(-5)
)"""
    }
]


def get_examples_for_prompt(max_examples=15):
    """Get formatted examples for AI prompt."""
    examples_text = "\n\n".join([
        f"### Example: {ex['name']}\n"
        f"Description: {ex['description']}\n"
        f"```python\n{ex['code']}\n```"
        for ex in CADQUERY_EXAMPLES[:max_examples]
    ])
    return examples_text
