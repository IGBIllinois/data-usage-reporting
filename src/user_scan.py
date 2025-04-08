import os
import csv
from datetime import datetime
from scan_utils import scan_all_users, format_time

def scan_multiple_directories(directories, skip_hidden=True, user_writer=None, file_writer=None):
    user_id = 1

    for directory in directories:
        if os.path.basename(directory).startswith('.'):
            continue
        user_id = scan_all_users(directory, user_id, skip_hidden, user_writer, file_writer)

if __name__ == "__main__":
    overall_start_time = time.time()
    
    directories_to_scan = ["/gpfs/a-m/", "/gpfs/n-z/"]
    skip_hidden = True

    date_str = datetime.now().strftime('%Y%m%d')
    hidden_suffix = "_includeHidden" if not skip_hidden else ""
    output_folder = f"/data/scan_output/a-z{hidden_suffix}_{date_str}"
    os.makedirs(output_folder, exist_ok=True)

    with open(os.path.join(output_folder, 'users.csv'), 'w', newline='', errors='ignore') as user_csv, \
         open(os.path.join(output_folder, 'files.csv'), 'w', newline='', errors='ignore') as file_csv:

        user_writer = csv.writer(user_csv)
        file_writer = csv.writer(file_csv)

        user_writer.writerow(['ID', 'NetID', 'Group', 'ScanTime', 'SkipHidden', 'TotalFiles', 'TotalSizeBytes', 'LastModified', 'AccessDate', 'CreationDate'])
        file_writer.writerow(['ID', 'NetID', 'Path', 'Name', 'SizeBytes', 'LastModified', 'AccessDate', 'CreationDate'])

        scan_multiple_directories(directories_to_scan, skip_hidden=skip_hidden, user_writer=user_writer, file_writer=file_writer)
    
    overall_end_time = time.time()
    overall_total_time = round(overall_end_time - overall_start_time)
    formatted_overall_total_time = format_time(overall_total_time)
    print(f"Overall total time taken: {formatted_overall_total_time}")