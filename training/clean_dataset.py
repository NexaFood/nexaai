import json
import ast
import shutil
from pathlib import Path

def validate_python_syntax(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def clean_file(file_path):
    print(f"\n🧹 Cleaning {file_path}...")
    
    if not file_path.exists():
        print(f"  ❌ File not found: {file_path}")
        return

    # Backup first
    backup_path = file_path.with_suffix(".bak.clean")
    shutil.copy(file_path, backup_path)
    print(f"  ✓ Backup created at {backup_path.name}")

    valid_entries = []
    removed_count = 0
    
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            try:
                entry = json.loads(line)
                code = entry.get('code', '')
                prompt = entry.get('prompt', '')
                
                # Validation checks
                if not isinstance(entry, dict) or \
                   not prompt or \
                   not code or \
                   "<generation_failed>" in code or \
                   not validate_python_syntax(code):
                    removed_count += 1
                    continue
                
                valid_entries.append(entry)
                
            except json.JSONDecodeError:
                removed_count += 1
                continue

    # Write back clean data
    with open(file_path, 'w') as f:
        for entry in valid_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"  ✓ Processed {i+1} lines")
    print(f"  ✓ Removed {removed_count} invalid entries")
    print(f"  ✓ Retained {len(valid_entries)} valid entries")

def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    clean_file(train_file)
    clean_file(val_file)
    
    print("\n✨ Dataset cleaning complete!")

if __name__ == "__main__":
    main()
