"""
Complete Data Collection Pipeline
Runs the entire data collection, validation, and merging process.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from github_scraper import GitHubScraper
from synthetic_generator import SyntheticGenerator
from code_validator import CodeValidator
from dataset_manager import DatasetManager


def run_complete_pipeline(
    github_examples: int = 500,
    synthetic_examples: int = 100,
    skip_github: bool = False,
    skip_synthetic: bool = False
):
    """
    Run the complete data collection pipeline.
    
    Args:
        github_examples: Number of examples to collect from GitHub
        synthetic_examples: Number of synthetic examples to generate
        skip_github: Skip GitHub scraping (use existing data)
        skip_synthetic: Skip synthetic generation (use existing data)
    """
    print("\n" + "="*70)
    print("🚀 CADQUERY TRAINING DATA COLLECTION PIPELINE")
    print("="*70 + "\n")
    
    # Step 1: Collect from GitHub
    if not skip_github and github_examples > 0:
        print("\n📥 STEP 1: Collecting examples from GitHub...")
        print("-" * 70)
        scraper = GitHubScraper()
        github_data = scraper.collect_examples(max_examples=github_examples)
        print(f"✓ Collected {len(github_data)} examples from GitHub\n")
    else:
        print("\n⏭️  STEP 1: Skipping GitHub collection (using existing data)\n")
    
    # Step 2: Generate synthetic data
    if not skip_synthetic and synthetic_examples > 0:
        print("\n🤖 STEP 2: Generating synthetic examples...")
        print("-" * 70)
        generator = SyntheticGenerator()
        synthetic_data = generator.generate_batch(count=synthetic_examples)
        print(f"✓ Generated {len(synthetic_data)} synthetic examples\n")
    else:
        print("\n⏭️  STEP 2: Skipping synthetic generation (using existing data)\n")
    
    # Step 3: Validate all examples
    print("\n🔍 STEP 3: Validating all examples...")
    print("-" * 70)
    validator = CodeValidator()
    
    # Validate GitHub examples
    github_dir = Path(__file__).parent / "data" / "github_examples"
    if github_dir.exists():
        print("\nValidating GitHub examples...")
        github_valid, github_invalid = validator.validate_dataset(str(github_dir))
        print(f"✓ GitHub: {len(github_valid)} valid, {len(github_invalid)} invalid")
    
    # Validate synthetic examples
    synthetic_dir = Path(__file__).parent / "data" / "synthetic"
    if synthetic_dir.exists():
        print("\nValidating synthetic examples...")
        synthetic_valid, synthetic_invalid = validator.validate_dataset(str(synthetic_dir))
        print(f"✓ Synthetic: {len(synthetic_valid)} valid, {len(synthetic_invalid)} invalid")
    
    # Step 4: Merge and organize dataset
    print("\n\n📦 STEP 4: Merging and organizing dataset...")
    print("-" * 70)
    manager = DatasetManager()
    final_dataset = manager.merge_datasets(output_format='jsonl')
    print(f"✓ Final dataset created: {final_dataset}")
    
    # Step 5: Generate report
    print("\n\n📊 STEP 5: Generating final report...")
    print("-" * 70)
    report = manager.generate_report()
    
    # Final summary
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE!")
    print("="*70)
    print(f"\n📈 Final Statistics:")
    print(f"  Total collected: {report['summary']['total_collected']}")
    print(f"  Successfully validated: {report['summary']['validated']}")
    print(f"  Validation rate: {report['summary']['validation_rate']}")
    print(f"  Final training dataset: {report['summary']['final_dataset']} examples")
    print(f"\n📁 Dataset location: {manager.dirs['final']}")
    print(f"  - train.jsonl")
    print(f"  - validation.jsonl")
    print(f"  - test.jsonl")
    print("\n" + "="*70 + "\n")
    
    return report


def run_quick_test():
    """Run a quick test with minimal examples to verify the pipeline works."""
    print("\n🧪 Running Quick Test Pipeline (10 examples)...\n")
    return run_complete_pipeline(
        github_examples=5,
        synthetic_examples=5
    )


def run_small_dataset():
    """Generate a small dataset for initial training experiments."""
    print("\n📦 Generating Small Dataset (1000 examples)...\n")
    return run_complete_pipeline(
        github_examples=200,
        synthetic_examples=800
    )


def run_medium_dataset():
    """Generate a medium-sized dataset for serious training."""
    print("\n📦 Generating Medium Dataset (10,000 examples)...\n")
    return run_complete_pipeline(
        github_examples=2000,
        synthetic_examples=8000
    )


def run_large_dataset():
    """Generate a large dataset for production-quality training."""
    print("\n📦 Generating Large Dataset (50,000 examples)...\n")
    
    # For large datasets, generate synthetic data in batches
    print("Note: This will take several hours and cost ~$500 in API fees.")
    response = input("Continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Collect GitHub examples once
    print("\n📥 Collecting from GitHub...")
    scraper = GitHubScraper()
    github_data = scraper.collect_examples(max_examples=2000)
    
    # Generate synthetic data in large batches
    print("\n🤖 Generating synthetic data (this will take a while)...")
    generator = SyntheticGenerator()
    generator.generate_large_dataset(target_count=48000, batch_size=1000)
    
    # Continue with validation and merging
    return run_complete_pipeline(
        github_examples=0,
        synthetic_examples=0,
        skip_github=True,
        skip_synthetic=True
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run CadQuery training data collection pipeline')
    parser.add_argument('--mode', choices=['test', 'small', 'medium', 'large', 'custom'], 
                        default='test', help='Pipeline mode')
    parser.add_argument('--github', type=int, default=500, help='Number of GitHub examples')
    parser.add_argument('--synthetic', type=int, default=100, help='Number of synthetic examples')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        run_quick_test()
    elif args.mode == 'small':
        run_small_dataset()
    elif args.mode == 'medium':
        run_medium_dataset()
    elif args.mode == 'large':
        run_large_dataset()
    else:  # custom
        run_complete_pipeline(
            github_examples=args.github,
            synthetic_examples=args.synthetic
        )
