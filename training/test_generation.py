"""
Interactive CadQuery Code Generation Tester

Test your trained model with custom prompts and see the generated code.
"""

import os
import torch
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def load_model(model_path):
    """Load trained model"""
    print(f"Loading model from: {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    
    print("✓ Model loaded successfully!\n")
    return model, tokenizer


def generate_code(model, tokenizer, prompt, max_length=2048, temperature=0.1):
    """Generate CadQuery code"""
    
    # Format prompt
    formatted_prompt = f"### Prompt: {prompt}\n### Code:\n"
    
    # Tokenize
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
    
    # Generate
    print("Generating...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            temperature=temperature,
            top_p=0.95,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    # Decode
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract code
    if "### Code:\n" in generated_text:
        code = generated_text.split("### Code:\n")[1].strip()
    else:
        code = generated_text.strip()
    
    return code


def interactive_mode(model, tokenizer):
    """Interactive testing mode"""
    
    print("\n" + "="*70)
    print("🤖 INTERACTIVE CADQUERY CODE GENERATION")
    print("="*70)
    print("\nType your prompts below. Type 'quit' to exit.\n")
    
    while True:
        # Get prompt
        prompt = input("Prompt: ").strip()
        
        if prompt.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if not prompt:
            continue
        
        # Generate
        print()
        code = generate_code(model, tokenizer, prompt)
        
        # Display
        print("\n" + "-"*70)
        print("Generated Code:")
        print("-"*70)
        print(code)
        print("-"*70 + "\n")


def single_prompt_mode(model, tokenizer, prompt):
    """Single prompt mode"""
    
    print("\n" + "="*70)
    print("🤖 CADQUERY CODE GENERATION")
    print("="*70)
    print(f"\nPrompt: {prompt}\n")
    
    # Generate
    code = generate_code(model, tokenizer, prompt)
    
    # Display
    print("\n" + "-"*70)
    print("Generated Code:")
    print("-"*70)
    print(code)
    print("-"*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Test CadQuery code generation')
    parser.add_argument('--model_path', type=str, required=True, help='Path to trained model')
    parser.add_argument('--prompt', type=str, default=None, help='Single prompt to test')
    parser.add_argument('--temperature', type=float, default=0.1, help='Generation temperature')
    
    args = parser.parse_args()
    
    # Load model
    model, tokenizer = load_model(args.model_path)
    
    # Run mode
    if args.prompt:
        single_prompt_mode(model, tokenizer, args.prompt)
    else:
        interactive_mode(model, tokenizer)


if __name__ == "__main__":
    main()
