import os, re
import torch
import numpy as np
from collections import OrderedDict, Counter
from string import ascii_uppercase, ascii_lowercase
import hashlib
import random
import shutil
import argparse

from predict import Predictor
from mmseq_api import parse_fasta, get_hash, get_unique_sequences, get_msa, run_mmseqs2

parser = argparse.ArgumentParser(description='Argument Parser')

parser.add_argument('input_file', type=str, help='input fasta file or a3m file path')
parser.add_argument('output_folder', type=str, help='output folder path')

parser.add_argument('--prefix', type=str, default="rf2_seed", help='out pdb prefix')
parser.add_argument('--sym', type=str, default="X", help='Type of symmetry (default:X))')
parser.add_argument('--order', type=str, default=1, help='Number of symmetry mates (default: 1)')
parser.add_argument('--msa_concat_mode', type=str, default="diag", help='MSA concatenation mode')

parser.add_argument('--msa_mode', type=str, default="mmseqs2", help='msa mode: mmseqs2 or single_sequence')
parser.add_argument('--pair_mode', type=str, default="unpaired_paired", help='msa pair mode: unpaired_paired, paired or unpaired')
parser.add_argument('--collapse_identical', action='store_true', help='collapse identical sequences')

parser.add_argument('--num_recycles', type=int, default=6, help='Number of recycles')
parser.add_argument('--num_models', type=int, default=1, help='Number of models to generate')

parser.add_argument('--model_params', type=str, default='weights/RF2_apr23.pt', help='RoseTTAfold2 model weights')
parser.add_argument('--use_mlm', action='store_true', help='Use MLM')
parser.add_argument('--use_dropout', action='store_true', help='Use dropout')
parser.add_argument('--random_seed', type=int, default=0, help='Random seed')
parser.add_argument('--max_msa', type=int, default=256, help='Maximum number of MSA sequences')
parser.add_argument('--subcrop', type=int, default=-1, help='Subcrop value (not working atm)')

args = parser.parse_args()


input_file = args.input_file
output_folder = args.output_folder
prefix = args.prefix
sym = args.sym
order = args.order
msa_concat_mode = args.msa_concat_mode
msa_mode = args.msa_mode
pair_mode = args.pair_mode
collapse_identical = args.collapse_identical
num_recycles = args.num_recycles
num_models = args.num_models
model_params = args.model_params
use_mlm = args.use_mlm
use_dropout = args.use_dropout
random_seed = args.random_seed
max_msa = args.max_msa
subcrop = args.subcrop
max_extra_msa = max_msa * 8

# GPU check
if (torch.cuda.is_available()):
    print ("Running on GPU")
    pred = Predictor(model_params, torch.device("cuda:0"))
else:
    print ("Running on CPU")
    pred = Predictor(model_params, torch.device("cpu"))


### Prepare inputs ###

# Symmetry 
if sym in ["X","C"]:
  copies = order
elif sym in ["D"]:
  copies = order * 2
else:
  copies = {"T":12,"O":24,"I":60}[sym]
  order = ""
symm = sym + str(order)

# Make output folder
try:
    os.makedirs(output_folder, exist_ok=False)
    print("Directory created successfully.")
except FileExistsError:
    print("Directory already exists.")

if input_file.endswith('.fasta') or input_file.endswith('.fa'):

    with open(input_file, 'r') as file:
        fasta_string = file.read()

    sequences, descriptions = parse_fasta(fasta_string)
    # generate MSA and predict all sequences
    for sequence, description in zip(sequences, descriptions):

        description=description.split("|")[0]

        sequence = re.sub("[^A-Z:]", "", sequence.replace("/",":").upper())
        sequence = re.sub(":+",":",sequence)
        sequence = re.sub("^[:]+","",sequence)
        sequence = re.sub("[:]+$","",sequence)

        sequences = sequence.replace(":","/").split("/")
        if collapse_identical:
            u_sequences = get_unique_sequences(sequences)
        else:
            u_sequences = sequences
            sequences = sum([u_sequences] * copies,[])
            lengths = [len(s) for s in sequences]

        sequence = "/".join(sequences)
        #jobname = prefix+"_"+symm+"_"+get_hash(sequence)[:5]


        ### Generate MSA ###
        if msa_mode == "mmseqs2":
            get_msa(u_sequences, output_folder, mode=pair_mode, max_msa=max_extra_msa)
            os.rename(f"{output_folder}/msa.a3m", f"{output_folder}/{description}.a3m")

        elif msa_mode == "single_sequence":
            u_sequence = "/".join(u_sequences)
            with open(f"{output_folder}/{description}.a3m","w") as a3m:
                a3m.write(f">{description}\n{u_sequence}\n")


        ### Prediction ###

        best_plddt = None
        best_seed = None

        for seed in range(random_seed,random_seed+num_models):
            torch.manual_seed(seed)
            random.seed(seed)
            np.random.seed(seed)
            npz = f"{output_folder}/{description}_{prefix}{seed}_00.npz"
            pred.predict(inputs=[f"{output_folder}/{description}.a3m"],
                        out_prefix=f"{output_folder}/{description}_{prefix}{seed}",
                        symm=symm,
                        ffdb=None,
                        n_recycles=num_recycles,
                        msa_mask=0.15 if use_mlm else 0.0,
                        msa_concat_mode=msa_concat_mode,
                        nseqs=max_msa,
                        nseqs_full=max_extra_msa,
                        subcrop=subcrop,
                        is_training=use_dropout)
            plddt = np.load(npz)["lddt"].mean()
            if best_plddt is None or plddt > best_plddt:
                best_plddt = plddt
                best_seed = seed

elif input_file.endswith('.a3m'):

    description = input_file.split("/")[-1].split(".")[0]
    a3m_file_path = f"{output_folder}/{description}.a3m"
    shutil.copy(input_file, a3m_file_path)

    ### Prediction ###

    best_plddt = None
    best_seed = None

    for seed in range(random_seed,random_seed+num_models):
        torch.manual_seed(seed)
        random.seed(seed)
        np.random.seed(seed)
        npz = f"{output_folder}/{description}_{prefix}{seed}_00.npz"
        pred.predict(inputs=[a3m_file_path],
                    out_prefix=f"{output_folder}/{description}_{prefix}{seed}",
                    symm=symm,
                    ffdb=None,
                    n_recycles=num_recycles,
                    msa_mask=0.15 if use_mlm else 0.0,
                    msa_concat_mode=msa_concat_mode,
                    nseqs=max_msa,
                    nseqs_full=max_extra_msa,
                    subcrop=subcrop,
                    is_training=use_dropout)
        plddt = np.load(npz)["lddt"].mean()
        if best_plddt is None or plddt > best_plddt:
            best_plddt = plddt
            best_seed = seed
    
else:
    print("Unsupported file format. Only fasta (.fasta, .fa) and a3m (.a3m) files are supported.")