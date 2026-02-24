#!/usr/bin/env python3
"""
SLAM Runner Script
Choose to run original version (MonoGS) or RTGS version (MonoGS_RTGS) SLAM program based on input parameters

Usage:
    python run_slam.py original tum/fr3_office
    python run_slam.py RTGS tum/fr3_office
    python run_slam.py RTGS tum/fr3_office --input_path /kaggle/input/dataset --output_path /kaggle/working/output
"""

import sys
import os
import subprocess
import argparse
import yaml
from pathlib import Path


def run_slam(version, config_path, input_path=None, output_path=None):
    """
    Run SLAM program
    
    Args:
        version (str): 'original' or 'RTGS'
        config_path (str): config file path, e.g. 'tum/fr3_office'
        input_path (str, optional): override dataset path
        output_path (str, optional): override save output directory
    """
    # Determine working directory
    if version.lower() == 'original':
        work_dir = Path('MonoGS')
        print(f"Running original version (MonoGS)")
    elif version.upper() == 'RTGS':
        work_dir = Path('MonoGS_RTGS')
        print(f"Running RTGS version (MonoGS_RTGS)")
    else:
        print(f"Error: Unsupported version '{version}'. Please use 'original' or 'RTGS'")
        return False
    
    # Check if directory exists
    if not work_dir.exists():
        print(f"Error: Directory '{work_dir}' does not exist")
        return False
    
    # Build complete config file path
    full_config_path = f"configs/rgbd/{config_path}.yaml"
    config_file = work_dir / full_config_path
    
    # Check if config file exists
    if not config_file.exists():
        print(f"Error: Config file '{config_file}' does not exist")
        return False
    
    # Handle overrides by writing to a temporary config
    run_config_path = full_config_path
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
            
        # Create temp config
        temp_config_name = f"{config_path}_temp.yaml"
        temp_config_rel_path = f"configs/rgbd/{temp_config_name}"
        temp_config_file = work_dir / temp_config_rel_path
        
        with open(temp_config_file, 'w') as f:
            yaml.dump(config_data, f)
            
        run_config_path = temp_config_rel_path
    
    # Build command
    cmd = [
        sys.executable,  # Use current Python interpreter
        'slam.py',
        '--config',
        run_config_path,
        '--eval'
    ]
    
    print(f"Working directory: {work_dir.absolute()}")
    print(f"Config file used: {run_config_path}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        # Switch to working directory and execute command
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            check=True,
            capture_output=False  # Show output in real-time
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
        # Cleanup temp config if it was created so the directory stays pristine
        if temp_config_file and temp_config_file.exists():
            temp_config_file.unlink()
            print(f"Cleaned up temporary config file: {temp_config_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run SLAM program - supports original and RTGS versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_slam.py original tum/fr3_office
  python run_slam.py RTGS tum/fr3_office
  python run_slam.py RTGS replica/office0 --input_path /kaggle/input/replica/office0 --output_path /kaggle/working/output
        """
    )
    
    parser.add_argument(
        'version',
        choices=['original', 'RTGS'],
        help='Choose version: original (MonoGS) or RTGS (MonoGS_RTGS)'
    )
    
    parser.add_argument(
        'config',
        help='Config file path (without .yaml extension), e.g.: tum/fr3_office, replica/office0'
    )
    
    # New Arguments
    parser.add_argument(
        '--input_path',
        type=str,
        default=None,
        help='Override the Dataset path in the config'
    )
    
    parser.add_argument(
        '--output_path',
        type=str,
        default=None,
        help='Override the Results save directory in the config'
    )
    
    args = parser.parse_args()
    
    # Run SLAM
    success = run_slam(args.version, args.config, args.input_path, args.output_path)
    
    if success:
        print("Program execution successful!")
    else:
        print("Program execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()