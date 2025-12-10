"""
CadQuery Model Evaluation Script

Evaluates the trained model on the test set and generates detailed metrics.
"""

import os
import json
import torch
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from tqdm import tqdm
from datasets import load_dataset
import sys
sys.path.append(os.path.dirname(__file__))
from code_validator import CodeValidator


def load_model(model_path):
    """Load trained model and tokenizer"""
    print(f"\n📥 Loading model from: {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    
    return model, tokenizer


def generate_code(model, tokenizer, prompt, max_length=2048):
    """Generate CadQuery code from prompt"""
    
    # Format prompt
    formatted_prompt = f"### Prompt: {prompt}\n### Code:\n"
    
    # Tokenize
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            temperature=0.1,
            top_p=0.95,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    # Decode
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract code (everything after "### Code:\n")
    if "### Code:\n" in generated_text:
        code = generated_text.split("### Code:\n")[1].strip()
    else:
        code = generated_text.strip()
    
    return code


def calculate_metrics(predictions, references):
    """Calculate evaluation metrics"""
    
    metrics = {
        'exact_match': 0,
        'bleu': 0,
        'execution_success': 0,
        'total': len(predictions)
    }
    
    validator = CodeValidator()
    
    for pred, ref in zip(predictions, references):
        # Exact match
        if pred.strip() == ref.strip():
            metrics['exact_match'] += 1
        
        # Execution success
        result = validator.validate_code(pred)
        if result['valid']:
            metrics['execution_success'] += 1
    
    # Convert to percentages
    metrics['exact_match'] = (metrics['exact_match'] / metrics['total']) * 100
    metrics['execution_success'] = (metrics['execution_success'] / metrics['total']) * 100
    
    return metrics


def evaluate(model_path, test_data_path, output_file=None, num_samples=None):
    """Run full evaluation"""
    
    print("\n" + "="*70)
    print("🔍 CADQUERY MODEL EVALUATION")
    print("="*70)
    
    # Load model
    model, tokenizer = load_model(model_path)
    
    # Load test data
    print(f"\n📥 Loading test data from: {test_data_path}")
    with open(test_data_path, 'r') as f:
        test_data = [json.loads(line) for line in f]
    
    if num_samples:
        test_data = test_data[:num_samples]
    
    print(f"  Test examples: {len(test_data)}")
    
    # Generate predictions
    print("\n🤖 Generating predictions...")
    predictions = []
    references = []
    
    for example in tqdm(test_data, desc="Evaluating"):
        prompt = example['prompt']
        reference_code = example['code']
        
        # Generate
        predicted_code = generate_code(model, tokenizer, prompt)
        
        predictions.append(predicted_code)
        references.append(reference_code)
    
    # Calculate metrics
    print("\n📊 Calculating metrics...")
    metrics = calculate_metrics(predictions, references)
    
    # Print results
    print("\n" + "="*70)
    print("📊 EVALUATION RESULTS")
    print("="*70)
    print(f"  Test Examples: {metrics['total']}")
    print(f"  Exact Match: {metrics['exact_match']:.2f}%")
    print(f"  Execution Success Rate: {metrics['execution_success']:.2f}%")
    print("="*70 + "\n")
    
    # Save results
    if output_file:
        results = {
            'metrics': metrics,
            'examples': [
                {
                    'prompt': test_data[i]['prompt'],
                    'reference': references[i],
                    'prediction': predictions[i]
                }
                for i in range(min(10, len(test_data)))  # Save first 10 examples
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Evaluate CadQuery model')
    parser.add_argument('--model_path', type=str, required=True, help='Path to trained model')
    parser.add_argument('--test_data', type=str, required=True, help='Path to test data (JSONL)')
    parser.add_argument('--output', type=str, default='evaluation_results.json', help='Output file for results')
    parser.add_argument('--num_samples', type=int, default=None, help='Number of samples to evaluate (default: all)')
    
    args = parser.parse_args()
    
    evaluate(
        model_path=args.model_path,
        test_data_path=args.test_data,
        output_file=args.output,
        num_samples=args.num_samples
    )


if __name__ == "__main__":
    main()
