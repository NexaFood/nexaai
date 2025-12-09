"""
CadQuery Code Executor

Safely executes generated CadQuery code and exports models to STEP/STL.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CadQueryExecutor:
    """Executes CadQuery code and exports 3D models."""
    
    def __init__(self, python_path=None, output_dir=None):
        """
        Initialize the CadQuery executor.
        
        Args:
            python_path: Path to Python interpreter with CadQuery installed
                        If None, will try Django settings, then sys.executable
            output_dir: Directory to save exported models (auto-detected if None)
        """
        # Determine Python path
        if python_path is None:
            # Try to get from Django settings
            try:
                from django.conf import settings
                python_path = getattr(settings, 'CADQUERY_PYTHON_PATH', None)
            except:
                pass
        
        if python_path is None:
            # Use current Python interpreter (works for Conda envs)
            python_path = sys.executable
            logger.info("Using current Python interpreter (sys.executable)")
        
        self.python_path = Path(python_path)
        
        # Verify Python exists
        if not self.python_path.exists():
            logger.error(f"Python interpreter not found: {self.python_path}")
            raise FileNotFoundError(f"Python interpreter not found: {self.python_path}")
        
        # Set output directory
        if output_dir is None:
            # Default to media/cadquery_models in project root
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            output_dir = project_root / "media" / "cadquery_models"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CadQuery Executor initialized")
        logger.info(f"  Platform: {sys.platform}")
        logger.info(f"  Python: {self.python_path}")
        logger.info(f"  Output: {self.output_dir}")
        
        # Test if CadQuery is available
        try:
            test_result = subprocess.run(
                [str(self.python_path), "-c", "import cadquery; print(cadquery.__version__)"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if test_result.returncode == 0:
                version = test_result.stdout.strip()
                logger.info(f"  CadQuery version: {version}")
            else:
                logger.warning(f"  CadQuery not found in Python environment!")
                logger.warning(f"  Error: {test_result.stderr}")
        except Exception as e:
            logger.warning(f"  Could not verify CadQuery installation: {e}")
    
    def execute_code(self, code: str, model_id: str, export_formats: list = ["step", "stl"]) -> Dict[str, Any]:
        """
        Execute CadQuery code and export the model.
        
        Args:
            code: CadQuery Python code to execute
            model_id: Unique ID for this model (for file naming)
            export_formats: List of formats to export ("step", "stl", "dxf")
            
        Returns:
            Dict with:
                - success: Boolean
                - files: Dict of format -> file path
                - error: Error message if failed
        """
        logger.info(f"Executing CadQuery code for model {model_id}")
        
        # Create a complete script that executes the code and exports
        # Indent the user code properly
        indented_code = "\n".join("    " + line if line.strip() else "" for line in code.split("\n"))
        
        # Use forward slashes for paths (works on both Windows and Linux)
        output_dir_str = str(self.output_dir).replace("\\", "/")
        
        script = f"""
import cadquery as cq
import sys
import traceback
from pathlib import Path

try:
    # Execute the generated code
{indented_code}
    
    # Verify result exists
    if 'result' not in locals():
        print("ERROR: Code did not create 'result' variable", file=sys.stderr)
        sys.exit(1)
    
    # Export to requested formats
    output_dir = Path(r"{output_dir_str}")
    model_id = "{model_id}"
    
    files = {{}}
"""
        
        # Add export code for each format
        if "step" in export_formats:
            script += f"""
    step_file = output_dir / f"{{model_id}}.step"
    cq.exporters.export(result, str(step_file))
    files['step'] = str(step_file)
    print(f"Exported STEP: {{step_file}}")
"""
        
        if "stl" in export_formats:
            script += f"""
    stl_file = output_dir / f"{{model_id}}.stl"
    cq.exporters.export(result, str(stl_file))
    files['stl'] = str(stl_file)
    print(f"Exported STL: {{stl_file}}")
"""
        
        if "dxf" in export_formats:
            script += f"""
    dxf_file = output_dir / f"{{model_id}}.dxf"
    cq.exporters.export(result, str(dxf_file))
    files['dxf'] = str(dxf_file)
    print(f"Exported DXF: {{dxf_file}}")
"""
        
        script += """
    # Print success
    print("SUCCESS")
    for fmt, path in files.items():
        print(f"{fmt}:{path}")
        
except Exception as e:
    print(f"ERROR: {str(e)}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
"""
        
        # Write script to temp file
        script_file = self.output_dir / f"{model_id}_script.py"
        script_file.write_text(script)
        
        try:
            # Execute the script in the CadQuery venv
            result = subprocess.run(
                [str(self.python_path), str(script_file)],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                # Parse output to get file paths
                files = {}
                for line in result.stdout.split("\n"):
                    if ":" in line and not line.startswith("Exported"):
                        fmt, path = line.split(":", 1)
                        files[fmt.strip()] = path.strip()
                
                logger.info(f"✓ Successfully executed and exported {len(files)} files")
                
                # Clean up script file
                script_file.unlink()
                
                return {
                    "success": True,
                    "files": files,
                    "stdout": result.stdout
                }
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"✗ Execution failed: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            logger.error("✗ Execution timed out (60s)")
            return {
                "success": False,
                "error": "Code execution timed out after 60 seconds"
            }
        except Exception as e:
            logger.error(f"✗ Execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_multi_part(self, parts: list, project_id: str) -> Dict[str, Any]:
        """
        Execute code for multiple parts and export all models.
        
        Args:
            parts: List of part dicts with 'name' and 'code'
            project_id: Unique ID for this project
            
        Returns:
            Dict with results for each part
        """
        logger.info(f"Executing multi-part project {project_id} with {len(parts)} parts")
        
        results = {}
        for i, part in enumerate(parts, 1):
            part_name = part.get('name', f'Part {i}')
            part_code = part.get('code', '')
            model_id = f"{project_id}_part{i}"
            
            logger.info(f"  Executing part {i}/{len(parts)}: {part_name}")
            
            result = self.execute_code(part_code, model_id)
            results[part_name] = result
        
        # Count successes
        success_count = sum(1 for r in results.values() if r.get('success'))
        logger.info(f"✓ Completed: {success_count}/{len(parts)} parts successful")
        
        return {
            "success": success_count == len(parts),
            "parts": results,
            "total": len(parts),
            "successful": success_count
        }
