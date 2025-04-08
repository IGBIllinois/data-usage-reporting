import os
import time
import csv
from datetime import datetime
from user_scan import scan_multiple_directories as scan_users
from scan_utils import format_time
from scan_utils import scan_all_users  # Reuse for labs and groups

def main():
    overall_start_time = time.time()

    # Define directories to scan for users, labs, and groups
    user_directories = ["/gpfs/a-m/", "/gpfs/n-z/"]
    lab_directories = ["/gpfs/labs/"]
    group_directories = ["/gpfs/groups/"]

    # Create a unified output folder with the current date
    date_str = datetime.now().strftime('%Y%m%d')
    output_folder = f"/data/scan_output/gpfs_{date_str}"
    os.makedirs(output_folder, exist_ok=True)

    # Open unified CSV files for writing
    with open(os.path.join(output_folder, 'users.csv'), 'w', newline='', errors='ignore') as user_csv, \
         open(os.path.join(output_folder, 'files.csv'), 'w', newline='', errors='ignore') as file_csv:

        user_writer = csv.writer(user_csv)
        file_writer = csv.writer(file_csv)

        # Write headers for the unified CSV files
        user_writer.writerow(['ID', 'NetID', 'Group', 'ScanTime', 'SkipHidden', 'TotalFiles', 'TotalSizeBytes', 'LastModified', 'AccessDate', 'CreationDate'])
        file_writer.writerow(['ID', 'NetID', 'Path', 'Name', 'SizeBytes', 'LastModified', 'AccessDate', 'CreationDate'])

        # Scan user directories and append results to the unified CSV files
        print("Starting user directory scans...")
        scan_users(user_directories, skip_hidden=True, user_writer=user_writer, file_writer=file_writer)

        # Scan lab directories and append results to the unified CSV files
        print("Starting lab directory scans...")
        user_id = 501  # Labs ID starts at 501
        for directory in lab_directories:
            user_id = scan_all_users(directory, user_id, skip_hidden=True, user_writer=user_writer, file_writer=file_writer)

        # Scan group directories and append results to the unified CSV files
        print("Starting group directory scans...")
        user_id = 701  # Groups ID starts at 701
        for directory in group_directories:
            user_id = scan_all_users(directory, user_id, skip_hidden=True, user_writer=user_writer, file_writer=file_writer)

    overall_end_time = time.time()
    overall_total_time = round(overall_end_time - overall_start_time)
    formatted_overall_total_time = format_time(overall_total_time)
    print(f"Overall total time taken: {formatted_overall_total_time}")

if __name__ == "__main__":
    main()