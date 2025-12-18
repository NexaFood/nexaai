#!/usr/bin/env python3
"""
Prepare Production Logs for Training
1. Reads production logs.
2. Filters for 'good' or 'corrected' examples.
3. Validates code.
4. Appends to existing training data.
"""

import json
import shutil
import random
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to handle internal imports in code_validator
sys.path.append(str(Path(__file__).parent.parent))
from code_validator import CodeValidator

def main():
    print("\n" + "="*70)
    print("📋 Processing Production Logs")
    print("="*70 + "\n")
    
    # Configuration
    log_file = Path("training/data/production_logs/production_202512.jsonl")
    train_file = Path("training/data/final_dataset/train.jsonl")
    val_file = Path("training/data/final_dataset/validation.jsonl")
    
    if not log_file.exists():
        print(f"✗ Log file not found: {log_file}")
        return

    # Backup existing datasets
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(train_file, train_file.with_suffix(f".{timestamp}.bak"))
    shutil.copy(val_file, val_file.with_suffix(f".{timestamp}.bak"))
    print(f"✓ Backed up datasets directly to {train_file}.{timestamp}.bak")

    # Initialize validator
    validator = CodeValidator()
    
    # Check if CadQuery is available
    try:
        import cadquery
        has_cadquery = True
        print("✓ CadQuery available - will validate code")
    except ImportError:
        has_cadquery = False
        print("⚠️  CadQuery not found - skipping validation (trusting logs)")

    # Load logs
    valid_examples = []
    print(f"Reading {log_file}...")
    
    # NEW: Load existing data to check for duplicates
    seen_ids = set()
    seen_content = set() # (prompt, code) hash
    
    for existing_file in [train_file, val_file]:
        if existing_file.exists():
            print(f"  Indexing {existing_file.name} for deduplication...")
            with open(existing_file, 'r') as f:
                for line in f:
                    try:
                        ex = json.loads(line)
                        # Check metadata for ID
                        if 'metadata' in ex and 'project_id' in ex['metadata']:
                            seen_ids.add(ex['metadata']['project_id'])
                        
                        # Also track content in case ID is missing
                        if 'prompt' in ex and 'code' in ex:
                            seen_content.add( (ex['prompt'], ex['code']) )
                    except json.JSONDecodeError:
                        pass
    
    print(f"  ✓ Indexed {len(seen_ids)} existing IDs and {len(seen_content)} content pairs")
    
    duplicates_count = 0
    
    with open(log_file, 'r') as f:
        for i, line in enumerate(f):
            try:
                entry = json.loads(line)
                project_id = entry.get('project_id')
                
                # Deduplication Check 1: ID
                if project_id and project_id in seen_ids:
                    duplicates_count += 1
                    continue
                
                # Determine if we should use this entry
                should_use = False
                code_to_use = None
                
                if entry.get('corrected_code'):
                    # User corrected the code - definitely use this
                    should_use = True
                    code_to_use = entry['corrected_code']
                    print(f"  Line {i+1}: Found optimization/correction")
                elif entry.get('rating') == 'good' and entry.get('success'):
                    # User rated it good and it ran
                    should_use = True
                    code_to_use = entry['generated_code']
                
                if should_use and code_to_use:
                    prompt = entry.get('prompt', '')
                    
                    # Deduplication Check 2: Content
                    if (prompt, code_to_use) in seen_content:
                         duplicates_count += 1
                         continue
                        
                    if has_cadquery:
                        # Validate
                        is_valid, error = validator.validate_code(code_to_use, f"log_{i}")
                        
                        if is_valid:
                            valid_examples.append({
                                'prompt': prompt,
                                'code': code_to_use,
                                'metadata': {'project_id': project_id} if project_id else {}
                            })
                            # Add to seen sets to handle duplicates within the same log file
                            if project_id: seen_ids.add(project_id)
                            seen_content.add((prompt, code_to_use))
                        else:
                            print(f"  Line {i+1}: Skipped (Invalid code: {error})")
                    else:
                        # Trust the log without validation
                        valid_examples.append({
                            'prompt': prompt,
                            'code': code_to_use,
                             'metadata': {'project_id': project_id} if project_id else {}
                        })
                        if project_id: seen_ids.add(project_id)
                        seen_content.add((prompt, code_to_use))
                        
            except json.JSONDecodeError:
                continue
    
    if duplicates_count > 0:
        print(f"  ✓ Skipped {duplicates_count} duplicate entries")
    
    print(f"\n✓ Found {len(valid_examples)} new valid examples from logs")
    
    if len(valid_examples) == 0:
        print("No new examples to add.")
        return

    # Split into train/val
    random.shuffle(valid_examples)
    split_idx = int(len(valid_examples) * 0.8)
    new_train = valid_examples[:split_idx]
    new_val = valid_examples[split_idx:]
    
    # Append to files
    print("\nAppending to datasets...")
    
    with open(train_file, 'a') as f:
        for ex in new_train:
            f.write(json.dumps(ex) + '\n')
            
    with open(val_file, 'a') as f:
        for ex in new_val:
            f.write(json.dumps(ex) + '\n')
            
    print(f"  + Added {len(new_train)} examples to train.jsonl")
    print(f"  + Added {len(new_val)} examples to validation.jsonl")
    
    print("\n" + "="*70)
    print("✅ Ready for training!")
    print("Run: python train_cadquery_model.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
