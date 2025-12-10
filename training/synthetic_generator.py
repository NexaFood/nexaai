"""
Synthetic Data Generator for CadQuery Training
Generates (text description, CadQuery code) pairs using GPT-4.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class SyntheticGenerator:
    """Generates synthetic CadQuery training examples using GPT-4."""
    
    def __init__(self, output_dir: str = "/home/ubuntu/nexaai/training/data/synthetic"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = OpenAI()  # Uses environment variable OPENAI_API_KEY
        self.examples = []
        
        # Object categories to generate
        self.categories = [
            "mechanical parts", "brackets", "mounts", "enclosures",
            "connectors", "fasteners", "gears", "pulleys",
            "tubes", "pipes", "flanges", "adapters",
            "plates", "panels", "frames", "chassis",
            "housings", "covers", "caps", "spacers"
        ]
    
    def create_generation_prompt(self, category: str, example_num: int) -> str:
        """Create a prompt for GPT-4 to generate a training example."""
        return f"""Generate a CadQuery training example for a {category}.

Create a JSON object with exactly these two fields:
1. "description": A clear, concise text description of what to create (1-2 sentences)
2. "code": Complete, executable Python code using CadQuery

REQUIREMENTS:
- Code MUST start with "import cadquery as cq"
- Code MUST create a variable called "result" with the final shape
- Code MUST be complete and executable (not pseudo-code)
- Use realistic dimensions in millimeters
- Keep it simple but functional
- Follow CadQuery best practices

EXAMPLE OUTPUT:
{{
  "description": "A rectangular mounting plate with four corner holes, dimensions 100x80x5mm with 5mm diameter holes",
  "code": "import cadquery as cq\\n\\nresult = (\\n    cq.Workplane(\\"XY\\")\\n    .box(100, 80, 5)\\n    .faces(\\">Z\\")\\n    .workplane()\\n    .rect(90, 70, forConstruction=True)\\n    .vertices()\\n    .hole(5)\\n)"
}}

Now generate example #{example_num} for category: {category}

Return ONLY the JSON object, no other text."""
    
    def generate_example(self, category: str, example_num: int) -> Dict:
        """Generate a single training example."""
        prompt = self.create_generation_prompt(category, example_num)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert CadQuery programmer. Generate high-quality, executable CadQuery code examples."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher temperature for diversity
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            example = json.loads(content)
            
            # Add metadata
            example['id'] = f"synthetic_{example_num}"
            example['source'] = 'synthetic'
            example['category'] = category
            example['prompt'] = example.get('description', '')
            
            return example
            
        except Exception as e:
            print(f"✗ Error generating example: {e}")
            return None
    
    def generate_batch(self, count: int = 100, start_id: int = 0):
        """Generate a batch of synthetic examples."""
        print(f"\n{'='*60}")
        print(f"🤖 Starting Synthetic Data Generation")
        print(f"  Target: {count} examples")
        print(f"  Model: gpt-4.1-mini")
        print(f"{'='*60}\n")
        
        generated = 0
        failed = 0
        
        for i in range(count):
            example_id = start_id + i
            category = self.categories[i % len(self.categories)]
            
            print(f"[{i+1}/{count}] Generating {category} example...", end=' ')
            
            example = self.generate_example(category, example_id)
            
            if example:
                self.examples.append(example)
                generated += 1
                
                # Save example to file
                example_file = self.output_dir / f"synthetic_{example_id}.json"
                with open(example_file, 'w') as f:
                    json.dump(example, f, indent=2)
                
                print(f"✓ Generated")
            else:
                failed += 1
                print(f"✗ Failed")
        
        # Save summary
        summary = {
            'total_generated': generated,
            'failed': failed,
            'success_rate': f"{(generated / count * 100):.1f}%",
            'categories': self.categories,
            'examples': self.examples
        }
        
        summary_file = self.output_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ Generation Complete!")
        print(f"  Generated: {generated}")
        print(f"  Failed: {failed}")
        print(f"  Success rate: {summary['success_rate']}")
        print(f"  Saved to: {self.output_dir}")
        print(f"{'='*60}\n")
        
        return self.examples
    
    def generate_large_dataset(self, target_count: int = 10000, batch_size: int = 100):
        """Generate a large dataset in batches."""
        print(f"\n🚀 Starting Large-Scale Synthetic Data Generation")
        print(f"  Target: {target_count} examples")
        print(f"  Batch size: {batch_size}\n")
        
        total_generated = 0
        batch_num = 0
        
        while total_generated < target_count:
            remaining = target_count - total_generated
            current_batch_size = min(batch_size, remaining)
            
            print(f"\n--- Batch {batch_num + 1} ---")
            examples = self.generate_batch(
                count=current_batch_size,
                start_id=total_generated
            )
            
            total_generated += len(examples)
            batch_num += 1
            
            print(f"\nProgress: {total_generated}/{target_count} ({total_generated/target_count*100:.1f}%)")
        
        print(f"\n✓ Large-scale generation complete!")
        print(f"  Total examples: {total_generated}")
        
        return total_generated


if __name__ == "__main__":
    generator = SyntheticGenerator()
    
    # Generate initial batch of 100 examples
    examples = generator.generate_batch(count=100)
    print(f"\n✓ Generated {len(examples)} synthetic examples")
    print(f"\nTo generate more, use:")
    print(f"  generator.generate_large_dataset(target_count=10000)")
