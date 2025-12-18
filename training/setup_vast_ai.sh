#!/bin/bash
# setup_vast_ai.sh - Automated environment setup for RTX 5090 Training

echo "🚀 Starting Vast.ai Environment Setup..."

# 1. Update and install basic dependencies
sudo apt-get update
sudo apt-get install -y wget git htop nvtop tar

# 2. Install Python dependencies
echo "📦 Installing Python libraries (Transformers, PEFT, BitsAndBytes)..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers peft datasets bitsandbytes accelerate trl tensorboard

# 3. Unpack dataset
if [ -f "nexa_dataset_backup.tar.gz" ]; then
    echo "📂 Unpacking dataset..."
    tar -xzvf nexa_dataset_backup.tar.gz
else
    echo "⚠️ Warning: nexa_dataset_backup.tar.gz not found. Please upload it to this directory."
fi

# 4. Hardware Verification
echo "🔍 Verifying GPU..."
nvidia-smi

echo "✅ Setup complete! You can now run training with:"
echo "python3 training/train_llama3_8b_5090.py"
