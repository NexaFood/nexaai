#!/usr/bin/env python3
"""
Process existing synthetic examples into train/val/test splits.
No generation, no validation - just split what we have.
"""

from pathlib import Path
import json
import random

def main():
    print("\n" + "="*70)
    print("📦 Processing Existing Synthetic Examples")
    print("="*70 + "\n")
    
    # Load all synthetic examples
    synthetic_dir = Path("data/synthetic")
    examples = []
    
    print("Loading synthetic examples...")
    for i in range(8000):
        file_path = synthetic_dir / f"synthetic_{i}.json"
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
                examples.append({
                    'prompt': data.get('description', ''),
                    'code': data.get('code', '')
                })
            if (i + 1) % 1000 == 0:
                print(f"  Loaded {i + 1}/8000...")
    
    print(f"\n✓ Loaded {len(examples)} examples\n")
    
    # Shuffle and split
    random.shuffle(examples)
    
    n = len(examples)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    splits = {
        'train': examples[:train_end],
        'validation': examples[train_end:val_end],
        'test': examples[val_end:]
    }
    
    # Save splits
    output_dir = Path("data/final_dataset")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating train/val/test splits...")
    for split_name, split_data in splits.items():
        output_file = output_dir / f"{split_name}.jsonl"
        
        with open(output_file, 'w') as f:
            for example in split_data:
                f.write(json.dumps(example) + '\n')
        
        print(f"  ✓ {split_name}: {len(split_data)} examples → {output_file}")
    
    print("\n" + "="*70)
    print("✅ DATASET READY FOR TRAINING!")
    print("="*70)
    print(f"\n📊 Statistics:")
    print(f"  Total: {len(examples)} examples")
    print(f"  Train: {len(splits['train'])} (80%)")
    print(f"  Validation: {len(splits['validation'])} (10%)")
    print(f"  Test: {len(splits['test'])} (10%)")
    print(f"\n📁 Location: {output_dir.absolute()}")
    print("\n🚀 Next step: Run training with train_cadquery_model.py\n")

if __name__ == "__main__":
    main()
