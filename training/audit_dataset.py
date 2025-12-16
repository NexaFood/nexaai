import json
import ast
from pathlib import Path

def validate_python_syntax(code):
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def audit_file(file_path):
    print(f"\n🔍 Auditing {file_path}...")
    
    if not file_path.exists():
        print(f"  ❌ File not found: {file_path}")
        return

    issues = []
    total_count = 0
    valid_count = 0
    
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            total_count += 1
            line_num = i + 1
            
            try:
                entry = json.loads(line)
                
                # Check 1: JSON Structure
                if not isinstance(entry, dict):
                    issues.append(f"Line {line_num}: Not a JSON object")
                    continue
                    
                # Check 2: Required Fields
                if 'prompt' not in entry or 'code' not in entry:
                    issues.append(f"Line {line_num}: Missing 'prompt' or 'code'")
                    continue
                
                prompt = entry['prompt']
                code = entry['code']
                
                # Check 3: Content Quality
                if not prompt or not code:
                    issues.append(f"Line {line_num}: Empty prompt or code")
                    continue
                    
                if "<generation_failed>" in code:
                    issues.append(f"Line {line_num}: Contains <generation_failed> marker")
                    continue
                
                # Check 4: Python Syntax
                is_valid_syntax, syntax_error = validate_python_syntax(code)
                if not is_valid_syntax:
                    # Truncate error for brevity
                    issues.append(f"Line {line_num}: Syntax Error: {syntax_error}")
                    continue
                
                valid_count += 1
                
            except json.JSONDecodeError:
                issues.append(f"Line {line_num}: Invalid JSON")
                continue

    # Report results for this file
    print(f"  Total Rows: {total_count}")
    print(f"  Valid Rows: {valid_count}")
    print(f"  Issues Found: {len(issues)}")
    
    if issues:
        print("  ⚠️ Top 10 Issues:")
        for issue in issues[:10]:
            print(f"    - {issue}")
            
    return len(issues) == 0

def main():
    base_dir = Path("/home/dobbeltop/ai_pathfinding/nexaai/training/data/final_dataset")
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "validation.jsonl"
    
    all_good = True
    all_good &= audit_file(train_file)
    all_good &= audit_file(val_file)
    
    if all_good:
        print("\n✅ All datasets passed the audit!")
    else:
        print("\n❌ Issues found in datasets. See details above.")

if __name__ == "__main__":
    main()
