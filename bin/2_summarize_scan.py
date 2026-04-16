"""
Script to summarize user and file statistics for a specified or latest results folder.

Workflow:
1. Loads configuration from scan_config.json, including data_dir, results_dir, and optional target_folder.
2. Determines which folder to process (target_folder if set, otherwise the latest).
3. Summarizes statistics and writes results using stat_utils functions.
4. Combines all subfolder statistics into a single combined output.

Usage:
Edit scan_config.json to set 'target_folder' for a specific folder, or leave it blank to use the latest.
Results are saved in the configured results_dir.
"""
#!/usr/bin/env python3
import pandas as pd
import os
from datetime import datetime
import time
import sys
import json
import argparse

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(root_dir + "/lib")
from stat_utils import get_latest_folder, summarize_and_write_stats, combine_stats

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Summarize scan results.")
    parser.add_argument("--config-dir", type=str, default="config",
                        help="Config folder path, relative to project root or absolute (default: config)")
    args = parser.parse_args()

    # Load scan profile
    if os.path.isabs(args.config_dir):
        config_dir = args.config_dir
    else:
        config_dir = os.path.join(root_dir, args.config_dir)
    config_path = os.path.join(config_dir, "scan_config.json")
    with open(config_path) as f:
        profile = json.load(f)

    # Start the timer
    start_time = time.time()

    # Define the base directory for results from config file
    data_dir = profile.get('data_dir', '/data/scan_output')

    # Determine which folder to use: target_folder from config or latest_folder
    target_folder = profile.get('target_folder', '').strip()
    if target_folder:
        folder_to_use = target_folder
        print(f"\nUsing the specified folder from config: {folder_to_use}")
    else:
        folder_to_use = get_latest_folder(data_dir)
        print(f"\nUsing the latest folder: {folder_to_use}")

    # Define the input and output folders
    input_folder = os.path.join(data_dir, folder_to_use)
    results_dir = profile.get('results_dir', 'results')
    output_folder = os.path.join(results_dir, folder_to_use)
    os.makedirs(output_folder, exist_ok=True)

    # Use summary_type from scan_config.json
    summary_type = profile.get('summary_type', 'yearly')
    # Pass summary_type directly to summarize_and_write_stats
    summarize_and_write_stats(input_folder, output_folder, summary_type)

    # Combine all stats in the output folder, matching summary_type
    combine_stats(output_folder, summary_type)

    # End the timer
    end_time = time.time()

    # Calculate and print the elapsed time
    elapsed_time = end_time - start_time
    print(f"\nScript completed in {elapsed_time:.2f} seconds.")

if __name__ == '__main__':
    main()



