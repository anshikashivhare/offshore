#!/bin/bash
#SBATCH --job-name=offshore_train
#SBATCH --output=logs/train_%j.log
#SBATCH --error=logs/train_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --mem=32G

# Exit on error
set -e

# Make sure we're in the project root
# Run this script from the project root using: sbatch scripts/slurm_train.sh ml.training.seaice_train
echo "Running in $(pwd)"

# Create logs directory for SLURM output if it doesn't exist
mkdir -p logs

# Activate the virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
else
    echo "Warning: No virtual environment found at .venv or venv"
    # If using conda, uncomment below:
    # module load anaconda3
    # source activate offshore_env
fi

# Determine the training script from the first argument (default to seaice_train)
TRAIN_MODULE=${1:-"ml.training.seaice_train"}

echo "Starting training for module: $TRAIN_MODULE"
python -m $TRAIN_MODULE

echo "Training completed."
