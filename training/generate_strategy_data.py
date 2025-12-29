
import os
import json
import random
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load env for OPENAI_API_KEY
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

OUTPUT_FILE = Path("training/data/strategy_finetune.jsonl")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

DOMAINS = [
    "Aerospace (Drones, Satellites)",
    "Automotive (Gearboxes, Chassis)",
    "Consumer Electronics (Wearables, IoT)",
    "Industrial (Piping, Conveyors)",
    "Robotics (Arms, Grippers)",
    "Medical (Prosthetics, Instruments)",
    "Architecture (Facades, Structures)"
]

SYSTEM_PROMPT = """You are an expert Senior Mechanical Engineer.
Your goal is to generate training data to teach a Junior AI how to plan 3D models.
You will be given a specific domain.
1. INVALIDATE "simple" requests.
2. GENERATE a complex, realistic "User Request".
3. GENERATE the perfect "Engineering Concept" (Stage 1 Response) for that request.

The "Engineering Concept" must include:
- Dimensions (variables like length, width, radius)
- Key Features (what parts make it up)
- Geometric Logic (e.g. "Use a loft for the body", "Fillet all outer edges 3mm")
- Manufacturing Constraints
"""

def generate_example(domain):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate a training example for the domain: {domain}. Output JSON with keys 'user_request' and 'engineering_concept'."}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Format for Fine-tuning
        # User message: The raw request
        # Assistant message: The thinking process + concept
        
        finetune_entry = {
            "messages": [
                {"role": "system", "content": "You are NexaAI, an expert CAD engineer. specificy the design parameters first."},
                {"role": "user", "content": data['user_request']},
                # Content MUST be a string for fine-tuning, not a dict
                {"role": "assistant", "content": json.dumps(data['engineering_concept'])}
            ]
        }
        return finetune_entry
    except Exception as e:
        print(f"Error generating for {domain}: {e}")
        return None

def main():
    print("Starting Strategy Data Generation...")
    
    examples = []
    # detailed generation
    for domain in DOMAINS:
        print(f"Processing Domain: {domain}")
        # Generate 10 examples per domain
        for i in range(10): 
            ex = generate_example(domain)
            if ex:
                examples.append(ex)
                print(f"  - Generated example {i+1}/10")
    
    # Save to JSONL
    with open(OUTPUT_FILE, 'w') as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")
            
    print(f"Saved {len(examples)} strategy examples to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
