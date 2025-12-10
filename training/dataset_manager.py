"""
Dataset Manager for CadQuery Training Data
Manages, organizes, and tracks all training data from various sources.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class DatasetManager:
    """Manages the complete training dataset."""
    
    def __init__(self, base_dir: str = "/home/ubuntu/nexaai/training/data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Directory structure
        self.dirs = {
            'github': self.base_dir / 'github_examples',
            'synthetic': self.base_dir / 'synthetic',
            'validated': self.base_dir / 'validated',
            'final': self.base_dir / 'final_dataset',
            'reports': self.base_dir / 'reports'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self) -> Dict:
        """Get statistics about the current dataset."""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'total_examples': 0,
            'validated_examples': 0,
            'final_dataset_size': 0
        }
        
        # Count GitHub examples
        github_files = list(self.dirs['github'].glob("example_*.json"))
        stats['sources']['github'] = len(github_files)
        
        # Count synthetic examples
        synthetic_files = list(self.dirs['synthetic'].glob("synthetic_*.json"))
        stats['sources']['synthetic'] = len(synthetic_files)
        
        # Count validated examples
        validated_files = list(self.dirs['validated'].glob("valid_*.json"))
        stats['validated_examples'] = len(validated_files)
        
        # Count final dataset
        final_files = list(self.dirs['final'].glob("*.json"))
        stats['final_dataset_size'] = len(final_files)
        
        stats['total_examples'] = stats['sources']['github'] + stats['sources']['synthetic']
        
        return stats
    
    def merge_datasets(self, output_format: str = 'jsonl'):
        """
        Merge all validated examples into a single final dataset.
        
        Args:
            output_format: 'jsonl' (one JSON per line) or 'json' (single array)
        """
        print(f"\n{'='*60}")
        print(f"📦 Merging Datasets")
        print(f"{'='*60}\n")
        
        # Collect all validated examples
        validated_files = list(self.dirs['validated'].glob("valid_*.json"))
        print(f"Found {len(validated_files)} validated examples")
        
        all_examples = []
        
        for i, file_path in enumerate(validated_files):
            with open(file_path, 'r') as f:
                example = json.load(f)
                all_examples.append(example)
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(validated_files)}")
        
        # Save in requested format
        if output_format == 'jsonl':
            output_file = self.dirs['final'] / 'training_data.jsonl'
            with open(output_file, 'w') as f:
                for example in all_examples:
                    # Create training format: {"prompt": "...", "code": "..."}
                    training_example = {
                        'prompt': example.get('prompt', example.get('description', '')),
                        'code': example.get('code', ''),
                        'metadata': {
                            'id': example.get('id'),
                            'source': example.get('source'),
                            'category': example.get('category', 'unknown')
                        }
                    }
                    f.write(json.dumps(training_example) + '\n')
        else:
            output_file = self.dirs['final'] / 'training_data.json'
            with open(output_file, 'w') as f:
                json.dump(all_examples, f, indent=2)
        
        print(f"\n✓ Merged {len(all_examples)} examples")
        print(f"  Saved to: {output_file}")
        
        # Create dataset split (train/val/test)
        self.create_splits(all_examples)
        
        return output_file
    
    def create_splits(self, examples: List[Dict], train_ratio: float = 0.8, val_ratio: float = 0.1):
        """
        Split dataset into train/validation/test sets.
        
        Args:
            examples: List of all examples
            train_ratio: Proportion for training (default 80%)
            val_ratio: Proportion for validation (default 10%, remaining 10% for test)
        """
        import random
        random.shuffle(examples)
        
        n = len(examples)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        splits = {
            'train': examples[:train_end],
            'validation': examples[train_end:val_end],
            'test': examples[val_end:]
        }
        
        print(f"\n📊 Dataset Splits:")
        for split_name, split_data in splits.items():
            output_file = self.dirs['final'] / f'{split_name}.jsonl'
            
            with open(output_file, 'w') as f:
                for example in split_data:
                    training_example = {
                        'prompt': example.get('prompt', example.get('description', '')),
                        'code': example.get('code', '')
                    }
                    f.write(json.dumps(training_example) + '\n')
            
            print(f"  {split_name}: {len(split_data)} examples → {output_file.name}")
    
    def generate_report(self):
        """Generate a comprehensive report about the dataset."""
        stats = self.get_stats()
        
        report = {
            'generated_at': stats['timestamp'],
            'summary': {
                'total_collected': stats['total_examples'],
                'validated': stats['validated_examples'],
                'final_dataset': stats['final_dataset_size'],
                'validation_rate': f"{(stats['validated_examples'] / max(stats['total_examples'], 1) * 100):.1f}%"
            },
            'sources': stats['sources'],
            'directories': {k: str(v) for k, v in self.dirs.items()}
        }
        
        # Save report
        report_file = self.dirs['reports'] / f"dataset_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print report
        print(f"\n{'='*60}")
        print(f"📊 Dataset Report")
        print(f"{'='*60}")
        print(f"\nSummary:")
        print(f"  Total collected: {report['summary']['total_collected']}")
        print(f"  Validated: {report['summary']['validated']}")
        print(f"  Final dataset: {report['summary']['final_dataset']}")
        print(f"  Validation rate: {report['summary']['validation_rate']}")
        print(f"\nSources:")
        for source, count in report['sources'].items():
            print(f"  {source}: {count}")
        print(f"\nReport saved to: {report_file}")
        print(f"{'='*60}\n")
        
        return report


if __name__ == "__main__":
    manager = DatasetManager()
    
    # Generate report
    report = manager.generate_report()
    
    # If we have validated examples, merge them
    if report['summary']['validated'] > 0:
        print("\nMerging validated examples into final dataset...")
        manager.merge_datasets(output_format='jsonl')
    else:
        print("\n⚠️  No validated examples found yet.")
        print("Run the pipeline:")
        print("  1. python github_scraper.py")
        print("  2. python synthetic_generator.py")
        print("  3. python code_validator.py")
        print("  4. python dataset_manager.py")
