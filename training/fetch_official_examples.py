import urllib.request
import urllib.error
import time
from pathlib import Path

# Base URL for raw content
BASE_URL = "https://raw.githubusercontent.com/CadQuery/cadquery/master/examples/"

# Valid filenames typically found in CadQuery examples
# I am listing common ones based on naming conventions and search results.
# If I miss some, the script will just report 404.
FILENAMES = [
    "Ex001_Simple_Block.py",
    "Ex002_Block_With_Bored_Center_Hole.py",
    "Ex003_Pillow_Block_With_Counterbored_Holes.py",
    "Ex004_Extruded_Cylindrical_Plate.py",
    "Ex005_Extruded_Rectangle.py",
    "Ex006_Moving_Workplanes.py",
    "Ex007_Using_Points.py",
    "Ex008_Polygon_Creation.py",
    "Ex009_Polygons_With_Workplanes.py",
    "Ex010_Defining_an_Edge_with_a_Spline.py",
    "Ex011_Mirroring_Symmetric_Geometry.py",
    "Ex012_Offsetting_Workplanes.py",
    "Ex013_Rotated_Workplanes.py",
    "Ex014_Using_Local_Workplane_Coordinates.py",
    "Ex015_Moving_A_Workplane.py",
    "Ex016_Dictionaries_With_Parameters.py",
    "Ex017_Tagged_Blocks_Tutorial.py",
    "Ex018_Assy_Tutorial.py",
    "Ex019_Workplanes_Tutorial.py",
    "Ex020_Sweep.py",
    "Ex021_Spline.py",
    "Ex022_Revolution.py",
    "Ex023_Loft.py",
    "Ex024_Sweep_With_Graph_Generator.py",
    "Ex025_Sweep_With_Multiple_Profiles.py",
    "Ex026_Cycloidal_Gear.py", 
    "Classic_OCC_Bottle.py",
    "Lego_Brick.py",
    "Parametric_Enclosure.py"
]

def fetch_examples():
    output_dir = Path("training/data/official_examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Fetching {len(FILENAMES)} examples from GitHub...")
    success_count = 0
    
    for filename in FILENAMES:
        url = BASE_URL + filename
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                
                # Save locally
                with open(output_dir / filename, 'w') as f:
                    f.write(content)
                
                print(f"  ✓ Fetched: {filename}")
                success_count += 1
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  ✗ Not Found: {filename}")
            else:
                print(f"  ✗ Error {e.code}: {filename}")
        except Exception as e:
            print(f"  ✗ Failed: {filename} ({e})")
            
        time.sleep(0.5) # Be nice to GitHub
        
    print(f"\nSuccessfully fetched {success_count} examples.")

if __name__ == "__main__":
    fetch_examples()
