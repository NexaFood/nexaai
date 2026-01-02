
import json
from pathlib import Path

def restore_file(bak_file, target_file):
    print(f"Restoring from {bak_file} to {target_file}...")
    bak_path = Path(bak_file)
    target_path = Path(target_file)
    
    if not bak_path.exists():
        print(f"Backup file not found: {bak_file}")
        return

    restored_count = 0
    skipped_count = 0
    
    # Read existing target data to avoid duplicates (naive check)
    existing_instructions = set()
    if target_path.exists():
        with open(target_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "instruction" in data:
                        existing_instructions.add(data["instruction"])
                except:
                    pass

    restored_lines = []
    
    with open(bak_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                
                # NORMALIZE KEYS
                new_data = {}
                
                # Check for "prompt" -> "instruction"
                if "instruction" in data:
                    new_data["instruction"] = data["instruction"]
                elif "prompt" in data:
                    new_data["instruction"] = data["prompt"]
                else:
                    skipped_count += 1
                    continue # No instruction found
                    
                # Check for "output" -> "output" (or "code")
                if "output" in data:
                    new_data["output"] = data["output"]
                elif "code" in data:
                    new_data["output"] = data["code"]
                elif "completion" in data:
                    new_data["output"] = data["completion"]
                else:
                    skipped_count += 1
                    continue # No output found

                # Add empty input if missing
                if "input" not in data:
                    new_data["input"] = ""
                else:
                    new_data["input"] = data["input"]
                    
                # Deduplicate
                if new_data["instruction"] in existing_instructions:
                    skipped_count += 1
                    continue
                
                # Add to restore list
                restored_lines.append(json.dumps(new_data))
                existing_instructions.add(new_data["instruction"])
                restored_count += 1
                
            except Exception as e:
                print(f"Error parsing line: {e}")
                skipped_count += 1
    
    # Append to target
    with open(target_path, 'a') as f:
        for line in restored_lines:
            f.write(line + "\n")
            
    print(f"  Restored {restored_count} lines.")
    print(f"  Skipped {skipped_count} lines (duplicates or invalid).")

def main():
    # Restore Training Data
    restore_file(
        "training/data/final_dataset/train.bak.clean",
        "training/data/final_dataset/train.jsonl"
    )
    
    # Restore Validation Data
    restore_file(
        "training/data/final_dataset/validation.bak.clean",
        "training/data/final_dataset/validation.jsonl"
    )

if __name__ == "__main__":
    main()
