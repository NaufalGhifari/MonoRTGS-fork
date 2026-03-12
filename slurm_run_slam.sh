#!/bin/bash
#SBATCH --job-name=monortgs_replica
#SBATCH --output=monortgs-out-%j.txt
#SBATCH --error=monortgs-err-%j.txt
#SBATCH --ntasks=1
#SBATCH --qos=1gpu
#SBATCH --partition=dgx1 
#SBATCH --gpus=1

singularity exec --nv /srv/images/nvhpc_25.1-devel-cuda_multi-ubuntu24.04.sif bash -c "
        source /home/cluster-dgx1/naufalal/miniforge/etc/profile.d/conda.sh
        conda activate MonoRTGS
        cd /home/cluster-dgx1/naufalal/GitHub/MonoRTGS-fork

        export LD_LIBRARY_PATH=/home/cluster-dgx1/naufalal/miniforge/envs/MonoRTGS/lib:\$LD_LIBRARY_PATH
        
        # Shut off cloud logging so it doesn't ask for a password
        export WANDB_MODE=disabled

        # Run the tracker
        python run_slam.py RTGS --config configs/rgbd/replica/room0.yaml
"
