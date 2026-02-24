#!/usr/bin/env python3
"""
SLAM Runner Script
Choose to run the original version (MonoGS) or the RTGS version (MonoGS_RTGS) of the SLAM program.

This script dynamically patches configuration files if override paths are provided, 
ensuring the original repository files remain completely pristine.

Usage Examples:
    # Basic run with an absolute config path
    python run_slam.py RTGS --config /full/path/to/config.yaml
    
    # Run with dynamically overridden dataset and output directories
    python run_slam.py original --config configs/rgbd/tum/fr3_office.yaml \
        --input_path /custom/dataset/path/ \
        --output_path /custom/output/dir/
"""

import sys
import os
import subprocess
import argparse
import yaml
from pathlib import Path


def run_slam(version, config_path, input_path=None, output_path=None):
    """
    Executes the SLAM program.
    
    Args:
        version (str): 'original' (MonoGS) or 'RTGS' (MonoGS_RTGS).
        config_path (str): The exact file path (absolute or relative) to the .yaml config file.
        input_path (str, optional): If provided, overrides the 'Dataset: dataset_path' key in the config.
        output_path (str, optional): If provided, overrides the 'Results: save_dir' key in the config.
        
    Returns:
        bool: True if execution succeeded, False otherwise.
    """
    # Determine working directory
    if version.lower() == 'original':
        work_dir = Path('MonoGS').resolve()
        print(f"Running original version (MonoGS)")
    elif version.upper() == 'RTGS':
        work_dir = Path('MonoGS_RTGS').resolve()
        print(f"Running RTGS version (MonoGS_RTGS)")
    else:
        print(f"Error: Unsupported version '{version}'. Please use 'original' or 'RTGS'")
        return False
    
    if not work_dir.exists():
        print(f"Error: Directory '{work_dir}' does not exist. Ensure you are running this from the repo root.")
        return False
    
    # Resolve the explicit config path
    config_file = Path(config_path).resolve()
    
    if not config_file.exists():
        print(f"Error: Config file '{config_file}' does not exist")
        return False
    
    run_config_path = str(config_file)
    temp_config_file = None
    
    if input_path or output_path:
        print("Applying config overrides...")
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
            
        if input_path:
            if 'Dataset' not in config_data:
                config_data['Dataset'] = {}
            config_data['Dataset']['dataset_path'] = input_path
            print(f"  -> Override input path: {input_path}")
            
        if output_path:
            if 'Results' not in config_data:
                config_data['Results'] = {}
            config_data['Results']['save_dir'] = output_path
            print(f"  -> Override output path: {output_path}")
            
        # Create temp config precisely next to the original config
        # This ensures parent 'inherit_from' relative paths still work
        temp_config_file = config_file.with_name(config_file.stem + "_temp" + config_file.suffix)
        
        with open(temp_config_file, 'w') as f:
            yaml.dump(config_data, f)
            
        run_config_path = str(temp_config_file)
    
    cmd = [
        sys.executable,
        'slam.py',
        '--config',
        run_config_path,
        '--eval'
    ]
    
    print(f"Working directory: {work_dir}")
    print(f"Config file used: {run_config_path}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            check=True,
            capture_output=False
        )
        print(f"\nSLAM program execution completed, exit code: {result.returncode}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nSLAM program execution failed, exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"\nUser interrupted execution")
        return False
    except Exception as e:
        print(f"\nError occurred during execution: {e}")
        return False
    finally:
        # Guarantee the temporary configuration file is removed
        if temp_config_file and temp_config_file.exists():
            temp_config_file.unlink()
            print(f"Cleaned up temporary config file: {temp_config_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the SLAM program with optional dynamic config overrides.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard execution with a specific config file
  python run_slam.py original --config /kaggle/working/MonoRTGS-fork/MonoGS/configs/rgbd/tum/fr3_office.yaml

  # Execution with overridden dataset and output paths (ideal for Kaggle/Colab)
  python run_slam.py RTGS \\
      --config /kaggle/working/MonoRTGS-fork/MonoGS_RTGS/configs/rgbd/replica/room0.yaml \\
      --input_path /kaggle/input/datasets/nice-slam-replica/room0/ \\
      --output_path /kaggle/working/Output_Results/
        """
    )
    
    parser.add_argument(
        'version',
        choices=['original', 'RTGS'],
        help="Choose the SLAM version to run: 'original' (MonoGS) or 'RTGS' (MonoGS_RTGS)."
    )
    
    parser.add_argument(
        '--config',
        required=True,
        help="The exact path (absolute or relative) to the .yaml config file."
    )
    
    parser.add_argument(
        '--input_path',
        type=str,
        default=None,
        help="Override the 'dataset_path' specified in the config file. Useful for pointing to external data mounts."
    )
    
    parser.add_argument(
        '--output_path',
        type=str,
        default=None,
        help="Override the 'save_dir' specified in the config file. Determines where logs/metrics are saved."
    )
    
    args = parser.parse_args()
    
    success = run_slam(args.version, args.config, args.input_path, args.output_path)
    
    if success:
        print("Program execution successful!")
    else:
        print("Program execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()