import os
import csv
from datetime import datetime
from scan_utils import scan_all_users, format_time

def main():
    overall_start_time = time.time()

    # Define directories to scan for groups
    group_directories = ["/gpfs/groups/"]  # Adjust as necessary
    skip_hidden = True

    # Create an output folder with the current date
    date_str = datetime.now().strftime('%Y%m%d')
    output_folder = f"/data/scan_output/group_{date_str}"
    os.makedirs(output_folder, exist_ok=True)

    # Open unified CSV files for writing
    with open(os.path.join(output_folder, 'users.csv'), 'w', newline='', errors='ignore') as user_csv, \
         open(os.path.join(output_folder, 'files.csv'), 'w', newline='', errors='ignore') as file_csv:

        user_writer = csv.writer(user_csv)
        file_writer = csv.writer(file_csv)

        # Write headers for the CSV files
        user_writer.writerow(['ID', 'NetID', 'Group', 'ScanTime', 'SkipHidden', 'TotalFiles', 'TotalSizeBytes', 'LastModified', 'AccessDate', 'CreationDate'])
        file_writer.writerow(['ID', 'NetID', 'Path', 'Name', 'SizeBytes', 'LastModified', 'AccessDate', 'CreationDate'])

        # Scan group directories and append results to the CSV files
        print("Starting group directory scans...")
        user_id = 701  # Groups ID starts at 701
        for directory in group_directories:
            user_id = scan_all_users(directory, user_id, skip_hidden, user_writer, file_writer)

    overall_end_time = time.time()
    overall_total_time = round(overall_end_time - overall_start_time)
    formatted_overall_total_time = format_time(overall_total_time)
    print(f"Overall total time taken: {formatted_overall_total_time}")

if __name__ == "__main__":
    main()