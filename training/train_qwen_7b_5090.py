import torch
from dataclasses import dataclass, field
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig
import os
import inspect

@dataclass
class ModelConfig:
    model_name: str = "Qwen/Qwen2.5-7B-Instruct" 
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16" 
    bnb_4bit_quant_type: str = "nf4"
    use_nested_quant: bool = True

@dataclass
class MyLoRAConfig:
    lora_r: int = 128 
    lora_alpha: int = 256
    lora_dropout: float = 0.05
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])

@dataclass
class TrainConfig:
    output_dir: str = "./cadquery_qwen_7b"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 10
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4 
    learning_rate: float = 2e-4
    max_grad_norm: float = 0.3
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    logging_steps: int = 5
    save_steps: int = 200
    eval_steps: int = 200
    save_total_limit: int = 3
    bf16: bool = True 
    optim: str = "paged_adamw_8bit"
    max_seq_length: int = 2048 
    report_to: str = "tensorboard"

lora_config_inst = MyLoRAConfig()
train_config_inst = TrainConfig()
model_config_inst = ModelConfig()

def train():
    print("🚀 Initializing UNGATED High-Performance Training (Qwen 2.5)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=model_config_inst.use_4bit,
        bnb_4bit_compute_dtype=getattr(torch, model_config_inst.bnb_4bit_compute_dtype),
        bnb_4bit_quant_type=model_config_inst.bnb_4bit_quant_type,
        bnb_4bit_use_double_quant=model_config_inst.use_nested_quant,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_config_inst.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_config_inst.model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    model = prepare_model_for_kbit_training(model)
    peft_config = LoraConfig(
        r=lora_config_inst.lora_r,
        lora_alpha=lora_config_inst.lora_alpha,
        target_modules=lora_config_inst.target_modules,
        lora_dropout=lora_config_inst.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    
    # 📊 Load and Pre-format Dataset manually
    dataset = load_dataset("json", data_files={
        "train": "training/data/final_dataset/train.jsonl", 
        "test": "training/data/final_dataset/validation.jsonl"
    })
    
    def format_row(example):
        # Map 'instruction' -> Prompt, 'output' -> Code to match inference format
        example["text"] = f"### Prompt: {example['instruction']}\n### Code:\n{example['output']}{tokenizer.eos_token}"
        return example
    
    print("📊 Stripping dataset of all columns except 'text' for maximum stability...")
    original_columns = dataset["train"].column_names
    dataset = dataset.map(format_row, remove_columns=original_columns)

    # 🛰️ AUTO-DETECT SFTConfig Arguments
    config_sig = inspect.signature(SFTConfig.__init__)
    sft_args = {
        "output_dir": train_config_inst.output_dir,
        "num_train_epochs": train_config_inst.num_train_epochs,
        "per_device_train_batch_size": train_config_inst.per_device_train_batch_size,
        "gradient_accumulation_steps": train_config_inst.gradient_accumulation_steps,
        "optim": train_config_inst.optim,
        "save_steps": train_config_inst.save_steps,
        "logging_steps": train_config_inst.logging_steps,
        "learning_rate": train_config_inst.learning_rate,
        "weight_decay": 0.001,
        "bf16": train_config_inst.bf16,
        "max_grad_norm": train_config_inst.max_grad_norm,
        "warmup_ratio": train_config_inst.warmup_ratio,
        "group_by_length": True,
        "lr_scheduler_type": train_config_inst.lr_scheduler_type,
        "report_to": train_config_inst.report_to,
        "eval_steps": train_config_inst.eval_steps,
        "packing": False,
        "dataset_text_field": "text", 
    }

    if "eval_strategy" in config_sig.parameters:
        sft_args["eval_strategy"] = "steps"
    elif "evaluation_strategy" in config_sig.parameters:
        sft_args["evaluation_strategy"] = "steps"

    if "max_length" in config_sig.parameters:
        sft_args["max_length"] = train_config_inst.max_seq_length
    elif "max_seq_length" in config_sig.parameters:
        sft_args["max_seq_length"] = train_config_inst.max_seq_length

    sft_config = SFTConfig(**sft_args)

    # 🛰️ AUTO-DETECT SFTTrainer Arguments
    trainer_sig = inspect.signature(SFTTrainer.__init__)
    trainer_args = {
        "model": model,
        "train_dataset": dataset["train"],
        "eval_dataset": dataset["test"],
        "peft_config": peft_config,
        "args": sft_config,
    }

    if "tokenizer" in trainer_sig.parameters:
        trainer_args["tokenizer"] = tokenizer
    elif "processing_class" in trainer_sig.parameters:
        trainer_args["processing_class"] = tokenizer

    trainer = SFTTrainer(**trainer_args)
    print("🔥 Starting Qwen 2.5 Training...")
    trainer.train()
    trainer.model.save_pretrained(os.path.join(train_config_inst.output_dir, "final_lora"))
    print(f"✅ Training Complete! Model saved to {train_config_inst.output_dir}")

if __name__ == "__main__":
    train()
