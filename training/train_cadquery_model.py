"""
CadQuery Model Training Script
Optimized for RTX 3080 Ti (12 GB VRAM)

This script fine-tunes CodeLlama 7B on CadQuery code generation using QLoRA.
"""

import os
import json
import torch
from dataclasses import dataclass, field
from typing import Optional
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
import wandb
from tqdm import tqdm


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ModelConfig:
    """Model configuration"""
    model_name: str = "codellama/CodeLlama-7b-hf"
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    use_nested_quant: bool = True


@dataclass
class LoRAConfig:
    """LoRA configuration"""
    lora_r: int = 16  # Reduced from 64 to fit in 12GB VRAM
    lora_alpha: int = 32  # Alpha = 2 * rank is recommended
    lora_dropout: float = 0.1
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])


@dataclass
class TrainConfig:
    """Training configuration"""
    output_dir: str = "./cadquery_model"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1  # Reduced from 4 to fit in 12GB
    per_device_eval_batch_size: int = 1  # Reduced from 4
    gradient_accumulation_steps: int = 16  # Increased to maintain effective batch size
    learning_rate: float = 2e-4
    max_grad_norm: float = 0.3
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    save_total_limit: int = 3
    fp16: bool = True
    optim: str = "paged_adamw_32bit"
    group_by_length: bool = True
    report_to: str = "tensorboard"
    max_seq_length: int = 1024  # Reduced from 2048 to save memory


@dataclass
class DataConfig:
    """Data configuration"""
    train_data: str = "./data/final_dataset/train.jsonl"
    val_data: str = "./data/final_dataset/validation.jsonl"
    test_data: str = "./data/final_dataset/test.jsonl"


# ============================================================================
# DATA LOADING
# ============================================================================

def load_cadquery_dataset(train_path, val_path, tokenizer, max_length=2048):
    """Load and tokenize CadQuery dataset"""
    
    print("\n📥 Loading dataset...")
    
    # Load JSONL files
    dataset = load_dataset('json', data_files={
        'train': train_path,
        'validation': val_path
    })
    
    print(f"  Train examples: {len(dataset['train'])}")
    print(f"  Validation examples: {len(dataset['validation'])}")
    
    # Tokenization function
    def tokenize_function(examples):
        # Format: "### Prompt: {prompt}\n### Code:\n{code}"
        texts = []
        for prompt, code in zip(examples['prompt'], examples['code']):
            text = f"### Prompt: {prompt}\n### Code:\n{code}"
            texts.append(text)
        
        # Tokenize
        tokenized = tokenizer(
            texts,
            truncation=True,
            max_length=max_length,
            padding="max_length",
            return_tensors="pt"
        )
        
        # Create labels (same as input_ids for causal LM)
        tokenized["labels"] = tokenized["input_ids"].clone()
        
        return tokenized
    
    # Tokenize datasets
    print("\n🔤 Tokenizing dataset...")
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["train"].column_names,
        desc="Tokenizing"
    )
    
    return tokenized_dataset


# ============================================================================
# MODEL SETUP
# ============================================================================

def setup_model_and_tokenizer(model_config, lora_config):
    """Set up model and tokenizer with 4-bit quantization and LoRA"""
    
    print("\n🤖 Loading base model...")
    print(f"  Model: {model_config.model_name}")
    
    # BitsAndBytes config for 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=model_config.use_4bit,
        bnb_4bit_quant_type=model_config.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=getattr(torch, model_config.bnb_4bit_compute_dtype),
        bnb_4bit_use_double_quant=model_config.use_nested_quant,
    )
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_config.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Configure LoRA
    peft_config = LoraConfig(
        r=lora_config.lora_r,
        lora_alpha=lora_config.lora_alpha,
        lora_dropout=lora_config.lora_dropout,
        target_modules=lora_config.target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    # Add LoRA adapters
    model = get_peft_model(model, peft_config)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_config.model_name,
        trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Print trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    all_params = sum(p.numel() for p in model.parameters())
    print(f"\n📊 Model Statistics:")
    print(f"  Trainable params: {trainable_params:,}")
    print(f"  All params: {all_params:,}")
    print(f"  Trainable %: {100 * trainable_params / all_params:.2f}%")
    
    return model, tokenizer


# ============================================================================
# TRAINING
# ============================================================================

def train_model(model, tokenizer, dataset, train_config):
    """Train the model"""
    
    print("\n🏋️ Starting training...")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=train_config.output_dir,
        num_train_epochs=train_config.num_train_epochs,
        per_device_train_batch_size=train_config.per_device_train_batch_size,
        per_device_eval_batch_size=train_config.per_device_eval_batch_size,
        gradient_accumulation_steps=train_config.gradient_accumulation_steps,
        learning_rate=train_config.learning_rate,
        max_grad_norm=train_config.max_grad_norm,
        warmup_ratio=train_config.warmup_ratio,
        lr_scheduler_type=train_config.lr_scheduler_type,
        logging_steps=train_config.logging_steps,
        save_steps=train_config.save_steps,
        eval_steps=train_config.eval_steps,
        eval_strategy="steps",
        save_total_limit=train_config.save_total_limit,
        fp16=train_config.fp16,
        optim=train_config.optim,
        group_by_length=train_config.group_by_length,
        report_to=train_config.report_to,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        gradient_checkpointing=True,  # Enable to save memory
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        data_collator=data_collator,
    )
    
    # Train
    print("\n" + "="*70)
    print("🚀 Training started!")
    print("="*70 + "\n")
    
    trainer.train()
    
    print("\n" + "="*70)
    print("✅ Training complete!")
    print("="*70 + "\n")
    
    # Save final model
    final_model_path = os.path.join(train_config.output_dir, "final_model")
    trainer.save_model(final_model_path)
    tokenizer.save_pretrained(final_model_path)
    
    print(f"💾 Model saved to: {final_model_path}")
    
    return trainer


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main training function"""
    
    print("\n" + "="*70)
    print("🚀 CADQUERY MODEL TRAINING")
    print("="*70)
    
    # Initialize configs
    model_config = ModelConfig()
    lora_config = LoRAConfig()
    train_config = TrainConfig()
    data_config = DataConfig()
    
    # Print configuration
    print("\n📋 Configuration:")
    print(f"  Base model: {model_config.model_name}")
    print(f"  4-bit quantization: {model_config.use_4bit}")
    print(f"  LoRA rank: {lora_config.lora_r}")
    print(f"  Epochs: {train_config.num_train_epochs}")
    print(f"  Batch size: {train_config.per_device_train_batch_size}")
    print(f"  Gradient accumulation: {train_config.gradient_accumulation_steps}")
    print(f"  Learning rate: {train_config.learning_rate}")
    print(f"  Output dir: {train_config.output_dir}")
    
    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"\n🎮 GPU: {gpu_name} ({gpu_memory:.1f} GB)")
    else:
        print("\n⚠️  WARNING: No GPU detected! Training will be very slow.")
    
    # Set up model and tokenizer
    model, tokenizer = setup_model_and_tokenizer(model_config, lora_config)
    
    # Load dataset
    dataset = load_cadquery_dataset(
        data_config.train_data,
        data_config.val_data,
        tokenizer,
        train_config.max_seq_length
    )
    
    # Train
    trainer = train_model(model, tokenizer, dataset, train_config)
    
    # Print final stats
    print("\n" + "="*70)
    print("📊 TRAINING SUMMARY")
    print("="*70)
    print(f"  Total steps: {trainer.state.global_step}")
    print(f"  Best eval loss: {trainer.state.best_metric:.4f}")
    print(f"  Final model: {train_config.output_dir}/final_model")
    print("\n✅ All done! Your custom CadQuery AI is ready!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
