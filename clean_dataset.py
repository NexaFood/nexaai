
import json
import sys
from pathlib import Path

def validate_line(line_num, line, filename):
    try:
        data = json.loads(line)
        
        # Check required fields
        if "instruction" not in data or "output" not in data:
            return False, f"Missing fields at line {line_num}"
            
        # Check types
        if not isinstance(data["instruction"], str):
            return False, f"Instruction is not string at line {line_num}"
        if not isinstance(data["output"], str):
            return False, f"Output is not string at line {line_num}"
            
        # Check empty content
        if not data["instruction"].strip():
            return False, f"Empty instruction at line {line_num}"
        if not data["output"].strip():
            return False, f"Empty output at line {line_num}"
            
        # Check reasonable length tokens (approx)
        # > 16k chars might be dangerous for some tokenizers/configs if not truncated
        if len(data["output"]) > 50000:
            return False, f"Output too long ({len(data['output'])} chars) at line {line_num}"
            
        return True, None
    except json.JSONDecodeError:
        return False, f"Invalid JSON at line {line_num}"
    except Exception as e:
        return False, f"Unknown error at line {line_num}: {e}"

def clean_file(filepath):
    print(f"Scanning {filepath}...")
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return

    valid_lines = []
    errors = []
    
    with open(path, 'r') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            is_valid, error = validate_line(i, line, filepath)
            if is_valid:
                valid_lines.append(line)
            else:
                errors.append(error)

    # Report
    print(f"  Total lines: {len(valid_lines) + len(errors)}")
    print(f"  Valid lines: {len(valid_lines)}")
    print(f"  Corrupt lines: {len(errors)}")
    
    if errors:
        print("\n  Sample Errors:")
        for e in errors[:5]:
            print(f"    - {e}")
            
        # Backup and Save
        backup_path = path.with_suffix(".bak.clean")
        path.rename(backup_path)
        print(f"  Backed up original to {backup_path}")
        
        with open(path, 'w') as f:
            for line in valid_lines:
                f.write(line + "\n")
        print(f"  Saved clean version to {path}")
    else:
        print("  File is clean. No changes made.")

def main():
    clean_file("train_v17.jsonl")
    clean_file("validation_v17.jsonl")

if __name__ == "__main__":
    main()
