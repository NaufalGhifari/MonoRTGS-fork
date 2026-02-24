#!/usr/bin/env python3
"""
SLAM Runner Script
Dynamically handles dataset overrides and flattens 'inherit_from' hierarchies 
to bypass relative pathing issues in Kaggle/Colab environments.
"""

import sys
import subprocess
import argparse
import yaml
import copy
from pathlib import Path


def merge_dicts(base, override):
    """Recursively merge dict 'override' into dict 'base'."""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            merge_dicts(base[k], v)
        else:
            base[k] = copy.deepcopy(v)
    return base


def flatten_config(config_path, work_dir):
    """Recursively loads inherited configs and flattens them into a single dictionary."""
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
        
    if 'inherit_from' in cfg:
        inherit_rel_path = cfg['inherit_from']
        
        # MonoGS expects inherit_from paths to be relative to the repo root
        parent_config_path = work_dir / inherit_rel_path
        
        if not parent_config_path.exists():
            print(f"Error: Could not find inherited config at {parent_config_path}")
            sys.exit(1)
            
        # Load the parent config recursively
        parent_cfg = flatten_config(parent_config_path, work_dir)
        
        # Merge current into parent (child overwrites parent)
        cfg = merge_dicts(parent_cfg, cfg)
        
        # Remove the inherit_from key so the underlying SLAM code doesn't try to parse it
        if 'inherit_from' in cfg:
            del cfg['inherit_from']
            
    return cfg


def run_slam(version, config_path, input_path=None, output_path=None):
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
        print(f"Error: Directory '{work_dir}' does not exist.")
        return False
    
    # Resolve the explicit config path
    config_file = Path(config_path).resolve()
    
    if not config_file.exists():
        print(f"Error: Config file '{config_file}' does not exist")
        return False
    
    temp_config_file = None
    
    print("Flattening config file to bypass relative path errors...")
    config_data = flatten_config(config_file, work_dir)
        
    # Apply user overrides
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
        
    # Save the fully flattened config
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
        # Guarantee cleanup
        if temp_config_file and temp_config_file.exists():
            temp_config_file.unlink()
            print(f"Cleaned up temporary config file: {temp_config_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the SLAM program with dynamic config flattening."
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
        help="Override the 'dataset_path' specified in the config file."
    )
    
    parser.add_argument(
        '--output_path',
        type=str,
        default=None,
        help="Override the 'save_dir' specified in the config file."
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