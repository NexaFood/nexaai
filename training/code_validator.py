"""
Code Validator for CadQuery Examples
Validates that CadQuery code executes successfully using CadQueryExecutor.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path to import CadQueryExecutor
sys.path.append(str(Path(__file__).parent.parent))
from services.cadquery_executor import CadQueryExecutor


class CodeValidator:
    """Validates CadQuery code by attempting to execute it."""
    
    def __init__(self, output_dir: str = "/home/ubuntu/nexaai/training/data/validated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.executor = CadQueryExecutor()
        self.stats = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'errors': {}
        }
    
    def validate_code(self, code: str, example_id: str) -> Tuple[bool, str]:
        """
        Validate a single piece of CadQuery code.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Execute the code
            result = self.executor.execute_code(code, model_id=f"validation_{example_id}")
            
            # Check if execution was successful
            if result.get('success'):
                return True, None
            else:
                error = result.get('error', 'Unknown error')
                return False, error
                
        except Exception as e:
            return False, str(e)
    
    def validate_example(self, example: Dict) -> Dict:
        """
        Validate a single example and return updated example with validation results.
        """
        example_id = example.get('id', 'unknown')
        code = example.get('code', '')
        
        print(f"  Validating: {example_id}...", end=' ')
        
        is_valid, error = self.validate_code(code, example_id)
        
        # Update example with validation results
        example['validated'] = True
        example['is_valid'] = is_valid
        
        if is_valid:
            print("✓ VALID")
            self.stats['valid'] += 1
        else:
            print(f"✗ INVALID: {error[:50]}...")
            example['validation_error'] = error
            self.stats['invalid'] += 1
            
            # Track error types
            error_type = error.split(':')[0] if ':' in error else error[:30]
            self.stats['errors'][error_type] = self.stats['errors'].get(error_type, 0) + 1
        
        self.stats['total'] += 1
        
        return example
    
    def validate_dataset(self, input_dir: str, save_valid_only: bool = True):
        """
        Validate all examples in a directory.
        
        Args:
            input_dir: Directory containing example JSON files
            save_valid_only: If True, only save valid examples to output
        """
        input_path = Path(input_dir)
        
        print(f"\n{'='*60}")
        print(f"🔍 Starting Code Validation")
        print(f"  Input: {input_path}")
        print(f"  Output: {self.output_dir}")
        print(f"{'='*60}\n")
        
        # Find all example files
        example_files = list(input_path.glob("example_*.json"))
        print(f"Found {len(example_files)} examples to validate\n")
        
        valid_examples = []
        invalid_examples = []
        
        for i, example_file in enumerate(example_files):
            print(f"[{i+1}/{len(example_files)}]", end=' ')
            
            # Load example
            with open(example_file, 'r') as f:
                example = json.load(f)
            
            # Validate
            validated_example = self.validate_example(example)
            
            if validated_example['is_valid']:
                valid_examples.append(validated_example)
                
                if save_valid_only:
                    # Save valid example
                    output_file = self.output_dir / f"valid_{validated_example['id']}.json"
                    with open(output_file, 'w') as f:
                        json.dump(validated_example, f, indent=2)
            else:
                invalid_examples.append(validated_example)
        
        # Save validation report
        success_rate = 0.0 if self.stats['total'] == 0 else (self.stats['valid'] / self.stats['total'] * 100)
        report = {
            'stats': self.stats,
            'success_rate': f"{success_rate:.1f}%",
            'error_breakdown': self.stats['errors']
        }
        
        report_file = self.output_dir / "validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save invalid examples for analysis
        if invalid_examples:
            invalid_file = self.output_dir / "invalid_examples.json"
            with open(invalid_file, 'w') as f:
                json.dump(invalid_examples, f, indent=2)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"✓ Validation Complete!")
        print(f"  Total examples: {self.stats['total']}")
        print(f"  Valid: {self.stats['valid']} ({report['success_rate']})")
        print(f"  Invalid: {self.stats['invalid']}")
        print(f"\n  Top Errors:")
        for error_type, count in sorted(self.stats['errors'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {error_type}: {count}")
        print(f"\n  Report saved to: {report_file}")
        print(f"{'='*60}\n")
        
        return valid_examples, invalid_examples


if __name__ == "__main__":
    validator = CodeValidator()
    
    # Validate GitHub examples
    github_dir = "/home/ubuntu/nexaai/training/data/github_examples"
    if Path(github_dir).exists():
        valid, invalid = validator.validate_dataset(github_dir)
        print(f"\n✓ Validated {len(valid)} valid examples from GitHub")
    else:
        print(f"✗ GitHub examples directory not found: {github_dir}")
        print(f"  Run github_scraper.py first to collect examples")
