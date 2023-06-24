#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:A40:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=50G
#SBATCH --exclude=compute-0-11

# Setup RF2 environment
source /home/tsatler/RFdif/RoseTTAFold2/set_up_RF2.sh

rf2_path="/home/tsatler/RFdif/RoseTTAFold2"

while [ $# -gt 0 ]; do
    case "$1" in
        --help)
            echo "Usage: script.sh [OPTIONS]"
            echo "Options:"
            echo "    -h, --help: Display this help message"
            echo "    -i, --input FILE: fasta or a3m file"
            echo "    -o, --output FOLDER: Output folder"
            echo "    --prefix PREFIX: Prefix"
            echo "    --sym SYM: Symmetry"
            echo "    --order ORDER: Order"
            echo "    --msa_concat_mode MODE: MSA concatenation mode"
            echo "    --msa_mode MODE: MSA mode"
            echo "    --pair_mode MODE: Pair mode"
            echo "    --collapse_identical: Collapse identical"
            echo "    --num_recycles NUM: Number of recycles"
            echo "    --num_models NUM: Number of models"
            echo "    --model_params PARAMS: Model parameters"
            echo "    --use_mlm: Use MLM"
            echo "    --use_dropout: Use dropout"
            echo "    --random_seed SEED: Random seed"
            echo "    --max_msa MAX: Maximum MSA"
            echo "    --subcrop SUBCROP: Subcrop"
            exit 1
            ;;
        -i | --input)
            input_file="$2"
            shift 2
            ;;
        -o | --output)
            output_folder="$2"
            shift 2
            ;;
        --prefix)
            prefix="$2"
            shift 2
            ;;
        --sym)
            sym="$2"
            shift 2
            ;;
        --order)
            order="$2"
            shift 2
            ;;
        --msa_concat_mode)
            msa_concat_mode="$2"
            shift 2
            ;;
        --msa_mode)
            msa_mode="$2"
            shift 2
            ;;
        --pair_mode)
            pair_mode="$2"
            shift 2
            ;;
        --collapse_identical)
            collapse_identical="--collapse_identical"
            shift
            ;;
        --num_recycles)
            num_recycles="$2"
            shift 2
            ;;
        --num_models)
            num_models="$2"
            shift 2
            ;;
        --model_params)
            model_params="$2"
            shift 2
            ;;
        --use_mlm)
            use_mlm="--use_mlm"
            shift
            ;;
        --use_dropout)
            use_dropout="--use_dropout"
            shift
            ;;
        --random_seed)
            random_seed="$2"
            shift 2
            ;;
        --max_msa)
            max_msa="$2"
            shift 2
            ;;
        --subcrop)
            subcrop="$2"
            shift 2
            ;;
        *)
            echo "Invalid option: $1"
            exit 1
            ;;
    esac
done

# Check if input and output folders are provided
if [ -z "$input_file" ] || [ -z "$output_folder" ]; then
    echo "Input file and output folder must be provided."
    exit 1
fi

# Set model_params if not provided
if [ -z "$model_params" ]; then
    model_params="$rf2_path/network/weights/RF2_apr23.pt"
fi

# Print the python command
cmd="python ${rf2_path}/network/predict_mmseq.py "${input_file}" "${output_folder}" \
    ${prefix:+--prefix "${prefix}"} \
    ${sym:+--sym "${sym}"} \
    ${order:+--order "${order}"} \
    ${msa_concat_mode:+--msa_concat_mode "${msa_concat_mode}"} \
    ${msa_mode:+--msa_mode "${msa_mode}"} \
    ${pair_mode:+--pair_mode "${pair_mode}"} \
    ${collapse_identical} \
    ${num_recycles:+--num_recycles "${num_recycles}"} \
    ${num_models:+--num_models "${num_models}"} \
    ${model_params:+--model_params "${model_params}"} \
    ${use_mlm} \
    ${use_dropout} \
    ${random_seed:+--random_seed "${random_seed}"} \
    ${max_msa:+--max_msa "${max_msa}"} \
    ${subcrop:+--subcrop "${subcrop}"}"

echo $cmd

# Run the Python script
$cmd