# 🔄 Retraining Guide

This guide explains how to retrain the CadQuery AI model using production logs.

## 1. Prepare Logs
We have a script `prepare_logs.py` that ingests `data/production_logs/`, validates the code (if CadQuery is installed), and appends valid examples to the training dataset.

```bash
# Process new logs and add to dataset
python prepare_logs.py
```
*Note: This script automatically backs up your existing `train.jsonl` and `validation.jsonl` before modifying them.*

## 2. Start Training
Once the dataset is updated, run the standard training script.

```bash
# Start training (make sure you are in the conda environment with GPU support)
# NEW: Resume from previous model (MUCH FASTER)
python train_cadquery_model.py --resume_from_model ./cadquery_model/final_model

# OR: Train from scratch (if you want a clean slate)
# python train_cadquery_model.py
```

## 3. Evaluate and Deploy
After training finishes:

```bash
# Evaluate the new model
python evaluate_model.py --model_path ./cadquery_model/final_model --test_data ./data/final_dataset/test.jsonl

# Export to GGUF (if needed for deployment)
python export_model.py --model_path ./cadquery_model/final_model
```
