#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:A40:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=50G
#SBATCH --exclude=compute-0-11

# Setup RF2 environment
source /home/tsatler/RFdif/RoseTTAFold2/set_up_RF2.sh

python network/predict_mmseq.py /home/tsatler/RFdif/RoseTTAFold2/examples/7LAW.fasta /home/tsatler/RFdif/testing/rf_out/7LAW-dim --num_models 5 --model_params network/weights/RF2_apr23.pt