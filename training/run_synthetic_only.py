"""
Synthetic-Only Data Generation Pipeline
Generates high-quality training data using only GPT-4 synthetic generation.

This approach is actually BETTER than scraping GitHub because:
1. Higher quality - GPT-4 generates clean, working code
2. More consistent - All examples follow the same patterns
3. Better diversity - Can target specific categories
4. Faster - No need to scrape and validate GitHub code
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from synthetic_generator import SyntheticGenerator
from code_validator import CodeValidator
from dataset_manager import DatasetManager


def run_synthetic_pipeline(target_examples: int = 10000, batch_size: int = 100):
    """
    Run synthetic-only data generation pipeline.
    
    Args:
        target_examples: Number of examples to generate
        batch_size: Examples per batch
    """
    print("\n" + "="*70)
    print("🤖 SYNTHETIC CADQUERY TRAINING DATA GENERATION")
    print("="*70)
    print(f"\nTarget: {target_examples} examples")
    print(f"Batch size: {batch_size}")
    print(f"Estimated time: {target_examples / 100 * 3} minutes")
    print(f"Estimated cost: ${target_examples * 0.015:.2f}")
    print("\n" + "="*70 + "\n")
    
    # Step 1: Generate synthetic examples
    print("\n🤖 STEP 1: Generating synthetic examples...")
    print("-" * 70)
    generator = SyntheticGenerator()
    
    total_generated = 0
    batch_num = 0
    
    while total_generated < target_examples:
        remaining = target_examples - total_generated
        current_batch_size = min(batch_size, remaining)
        
        print(f"\n--- Batch {batch_num + 1} ---")
        examples = generator.generate_batch(
            count=current_batch_size,
            start_id=total_generated
        )
        
        total_generated += len(examples)
        batch_num += 1
        
        progress_pct = (total_generated / target_examples * 100)
        print(f"\nProgress: {total_generated}/{target_examples} ({progress_pct:.1f}%)")
        
        # Save checkpoint every 1000 examples
        if total_generated % 1000 == 0:
            print(f"✓ Checkpoint: {total_generated} examples generated")
    
    print(f"\n✓ Generation complete: {total_generated} examples")
    
    # Step 2: Validate examples
    print("\n\n🔍 STEP 2: Validating examples...")
    print("-" * 70)
    validator = CodeValidator()
    
    synthetic_dir = "/home/ubuntu/nexaai/training/data/synthetic"
    valid, invalid = validator.validate_dataset(synthetic_dir)
    
    print(f"\n✓ Validation complete:")
    print(f"  Valid: {len(valid)}")
    print(f"  Invalid: {len(invalid)}")
    print(f"  Success rate: {len(valid) / (len(valid) + len(invalid)) * 100:.1f}%")
    
    # Step 3: Merge and organize
    print("\n\n📦 STEP 3: Creating final dataset...")
    print("-" * 70)
    manager = DatasetManager()
    final_dataset = manager.merge_datasets(output_format='jsonl')
    
    # Step 4: Generate report
    print("\n\n📊 STEP 4: Generating report...")
    print("-" * 70)
    report = manager.generate_report()
    
    # Final summary
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE!")
    print("="*70)
    print(f"\n📈 Final Statistics:")
    print(f"  Generated: {total_generated}")
    print(f"  Validated: {report['summary']['validated']}")
    print(f"  Success rate: {report['summary']['validation_rate']}")
    print(f"  Final dataset: {report['summary']['final_dataset']} examples")
    print(f"\n📁 Dataset location: {manager.dirs['final']}")
    print(f"  - train.jsonl ({int(report['summary']['final_dataset'] * 0.8)} examples)")
    print(f"  - validation.jsonl ({int(report['summary']['final_dataset'] * 0.1)} examples)")
    print(f"  - test.jsonl ({int(report['summary']['final_dataset'] * 0.1)} examples)")
    print("\n" + "="*70 + "\n")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic CadQuery training data')
    parser.add_argument('--examples', type=int, default=10000, help='Number of examples to generate')
    parser.add_argument('--batch', type=int, default=100, help='Batch size')
    
    args = parser.parse_args()
    
    report = run_synthetic_pipeline(
        target_examples=args.examples,
        batch_size=args.batch
    )
