# CadQuery AI Training Pipeline

Complete data collection and training pipeline for building a custom CadQuery code generation AI model.

## Overview

This pipeline collects, validates, and organizes training data from two sources:

1. **GitHub**: Real-world CadQuery examples from public repositories
2. **Synthetic**: AI-generated examples using GPT-4

All examples are validated by executing them with CadQueryExecutor to ensure they produce valid 3D models.

## Directory Structure

```
training/
├── data/
│   ├── github_examples/     # Raw examples from GitHub
│   ├── synthetic/           # Generated synthetic examples
│   ├── validated/           # Validated examples only
│   ├── final_dataset/       # Final merged dataset (train/val/test splits)
│   └── reports/             # Dataset statistics and reports
├── github_scraper.py        # Scrapes GitHub for CadQuery code
├── synthetic_generator.py   # Generates synthetic examples with GPT-4
├── code_validator.py        # Validates code by executing it
├── dataset_manager.py       # Manages and organizes the dataset
├── run_pipeline.py          # Main pipeline orchestrator
└── README.md                # This file
```

## Quick Start

### 1. Run a Quick Test (10 examples)

```bash
cd /home/ubuntu/nexaai/training
python run_pipeline.py --mode test
```

This will:
- Collect 5 examples from GitHub
- Generate 5 synthetic examples
- Validate all examples
- Create train/val/test splits

**Time:** ~2-3 minutes  
**Cost:** ~$0.10

### 2. Generate a Small Dataset (1,000 examples)

```bash
python run_pipeline.py --mode small
```

**Time:** ~30-45 minutes  
**Cost:** ~$10-15

### 3. Generate a Medium Dataset (10,000 examples)

```bash
python run_pipeline.py --mode medium
```

**Time:** ~4-6 hours  
**Cost:** ~$100-150

### 4. Generate a Large Dataset (50,000 examples)

```bash
python run_pipeline.py --mode large
```

**Time:** ~1-2 days  
**Cost:** ~$500-750

### 5. Custom Configuration

```bash
python run_pipeline.py --mode custom --github 300 --synthetic 700
```

## Individual Components

You can also run each component separately:

### GitHub Scraper

```python
from github_scraper import GitHubScraper

scraper = GitHubScraper()
examples = scraper.collect_examples(max_examples=500)
```

### Synthetic Generator

```python
from synthetic_generator import SyntheticGenerator

generator = SyntheticGenerator()
examples = generator.generate_batch(count=100)

# For large-scale generation
generator.generate_large_dataset(target_count=10000)
```

### Code Validator

```python
from code_validator import CodeValidator

validator = CodeValidator()
valid, invalid = validator.validate_dataset("/path/to/examples")
```

### Dataset Manager

```python
from dataset_manager import DatasetManager

manager = DatasetManager()
report = manager.generate_report()
manager.merge_datasets(output_format='jsonl')
```

## Output Format

The final dataset is saved in JSONL format (one JSON object per line):

```json
{"prompt": "A rectangular plate with four corner holes", "code": "import cadquery as cq\nresult = cq.Workplane..."}
{"prompt": "A hollow cylinder with flanges", "code": "import cadquery as cq\nresult = cq.Workplane..."}
```

Three files are created:
- `train.jsonl` (80% of data)
- `validation.jsonl` (10% of data)
- `test.jsonl` (10% of data)

## Expected Results

Based on our testing:

- **GitHub Examples:** ~60-70% validation success rate
- **Synthetic Examples:** ~50-60% validation success rate
- **Overall:** ~55-65% of collected examples are valid

For a target of 50,000 valid examples, you'll need to generate ~80,000-90,000 total examples.

## Cost Estimates

Costs are primarily from GPT-4 API calls for synthetic generation:

| Dataset Size | GitHub | Synthetic | Total Cost | Time      |
| ------------ | ------ | --------- | ---------- | --------- |
| Test (10)    | 5      | 5         | $0.10      | 2-3 min   |
| Small (1K)   | 200    | 800       | $10-15     | 30-45 min |
| Medium (10K) | 2,000  | 8,000     | $100-150   | 4-6 hours |
| Large (50K)  | 2,000  | 48,000    | $500-750   | 1-2 days  |

## Requirements

- Python 3.10+
- GitHub CLI (`gh`) installed and authenticated
- OpenAI API key in environment variables
- CadQuery installed in your Python environment
- Sufficient disk space (~1GB for 50K examples)

## Next Steps

After collecting the dataset:

1. **Phase 2:** Train the Transformer model
2. **Phase 3:** Evaluate and deploy
3. **Phase 4:** Continuous improvement

See `CUSTOM_AI_ROADMAP.md` for the complete training plan.

## Troubleshooting

### GitHub CLI not authenticated

```bash
gh auth login
```

### CadQuery not found

```bash
conda install -c conda-forge cadquery
```

### OpenAI API key not set

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Low validation success rate

- Check that CadQuery is properly installed
- Review `validation_report.json` for common errors
- Adjust synthetic generation prompts to avoid common mistakes

## Monitoring Progress

The pipeline provides detailed progress output:

```
🚀 CADQUERY TRAINING DATA COLLECTION PIPELINE
==================================================================

📥 STEP 1: Collecting examples from GitHub...
------------------------------------------------------------------
🔍 Searching GitHub for CadQuery repositories...
✓ Found 150 repositories
...

📊 STEP 5: Generating final report...
------------------------------------------------------------------
✓ Final dataset created
```

All reports are saved to `data/reports/` for later analysis.
