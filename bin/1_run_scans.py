#!/usr/bin/env python3
import json
import sys
import os
import time
from datetime import datetime
import argparse

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(root_dir + "/lib")
from scan_utils import run_scan,format_time# Load scan profile
with open(os.path.join(root_dir, "config", "scan_config.json")) as f:
    profile = json.load(f)

def main():
    overall_start_time = time.time()

    parser = argparse.ArgumentParser(description="Run scans for users, labs, or groups.")
    parser.add_argument("--scan-type", nargs="+", choices=["all", "users", "labs", "groups"], default=["all"],
                        help="Type of scan to run: users, labs, groups, or all (default: all)")
    args = parser.parse_args()

    data_dir = profile["data_dir"]
    skip_hidden = profile.get("skip_hidden", True)
    date_str = datetime.now().strftime('%Y%m%d')
    base_output_folder = os.path.join(data_dir, date_str)
    os.makedirs(base_output_folder, exist_ok=True)

    # Prepare log file
    log_file_path = os.path.join(base_output_folder, "scan.log")
    with open(log_file_path, "a") as log_file:
        overall_start_dt = datetime.now()
        log_file.write(f"Scan started at {overall_start_dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"skip_hidden: {skip_hidden}\n")

    scan_type_times = {}

    for scan_type in profile["scan_types"]:
        if "all" in args.scan_type or scan_type in args.scan_type:
            scan_start_dt = datetime.now()
            print(f"Starting {scan_type} directory scans...")
            info = profile[scan_type]
            run_scan(
                os.path.join(base_output_folder, scan_type),
                info["directories"],
                skip_hidden,
                info["start_id"]
            )
            scan_end_dt = datetime.now()
            scan_total_time = round((scan_end_dt - scan_start_dt).total_seconds())
            scan_time_str = format_time(scan_total_time)
            scan_type_times[scan_type] = {
                "start": scan_start_dt,
                "end": scan_end_dt,
                "total": scan_total_time
            }
            with open(log_file_path, "a") as log_file:
                log_file.write(f"{scan_type} scan started at {scan_start_dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"{scan_type} scan ended at {scan_end_dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"{scan_type} total scan time: {scan_time_str}\n")

    overall_end_time = time.time()
    overall_end_dt = datetime.now()
    overall_total_time = round(overall_end_time - overall_start_time)
    
    time_str = format_time(overall_total_time)
    with open(log_file_path, "a") as log_file:
        log_file.write(f"Overall scan ended at {overall_end_dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Overall total scan time: {time_str}\n")
    print(f"Overall total time taken: {time_str}")

if __name__ == "__main__":
    main()