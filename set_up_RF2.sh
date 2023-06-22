#!/bin/bash
echo SETTING UP RF2 RUNNING AS ${USER}@${HOSTNAME}

#activate RF2 enviorment
source "/home/tsatler/anaconda3/etc/profile.d/conda.sh"
conda activate /home/tsatler/anaconda3/envs/RF2

if [ $HOSTNAME != hpc.ki.si ]
then
    echo SETTING UP PROXY
    #Enable internet access on compute nodes
    source /home/tsatler/RFdif/RoseTTAFold2/setup_proxy_settings.sh
fi

echo RUNNING IN:
pwd

export NVIDIA_VISIBLE_DEVICES=$GPU_DEVICE_ORDINAL
export CUDA_VISIBLE_DEVICES=$GPU_DEVICE_ORDINAL
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib/:$LD_LIBRARY_PATH
echo Free device is $CUDA_VISIBLE_DEVICES