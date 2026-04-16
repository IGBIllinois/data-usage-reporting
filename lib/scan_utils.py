#!/usr/bin/env python3
import os
import time
import csv
from datetime import datetime

def format_time(seconds):
    if seconds < 3600:
        return time.strftime("%M:%S", time.gmtime(seconds))
    else:
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

def scan_user(directory, user_id, netid, center_name, skip_hidden, skip_folder_names, file_writer):
    start_time = time.time()
    print(f"Scanning user {user_id}: {netid}")

    # Append center_name to netid if the user is dropboxes
    if netid == 'dropboxes':
        netid = f"{netid}_{center_name}"

    total_files = 0
    total_file_size = 0

    # Get metadata for the user folder itself
    user_stat = os.lstat(directory)
    user_last_modified_date = datetime.fromtimestamp(user_stat.st_mtime).strftime('%Y-%m-%d')
    user_access_date = datetime.fromtimestamp(user_stat.st_atime).strftime('%Y-%m-%d')
    user_creation_date = datetime.fromtimestamp(user_stat.st_ctime).strftime('%Y-%m-%d')

    skip_folder_set = {name.lower() for name in skip_folder_names}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [
            d for d in dirs
            if (not skip_hidden or not d.startswith('.')) and d.lower() not in skip_folder_set
        ]
        if skip_hidden:
            files = [f for f in files if not f.startswith('.')]

        for file in files:
            file_path = os.path.join(root, file)
            file_stat = os.lstat(file_path)
            file_size = file_stat.st_size
            last_modified_date = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d')
            access_date = datetime.fromtimestamp(file_stat.st_atime).strftime('%Y-%m-%d')
            creation_date = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d')
            
            # Write to the file_writer with the updated netid
            file_writer.writerow([user_id, netid, file_path, file, file_size, last_modified_date, access_date, creation_date])
            
            total_files += 1
            total_file_size += file_size

    end_time = time.time()
    scan_time = round(end_time - start_time)
    user_data = [
        user_id, netid, center_name, scan_time, total_files, total_file_size,
        user_last_modified_date, user_access_date, user_creation_date  # Add folder times here
    ]
    print(f"{netid} completed in {scan_time} s, total files: {total_files}; total size: {total_file_size / (1024 ** 3):.2f} GB")

    return user_data


def scan_all_users(center_directory, user_id, skip_hidden, skip_folder_names, skip_user_prefixes, skip_user_names, user_writer, file_writer):
    start_time = time.time()
    start_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Scan started at: {start_datetime}, Directory: {center_directory} (Skip hidden files: {skip_hidden})")

    center_name = os.path.basename(center_directory.rstrip(os.sep))  # Get the center directory name (e.g., 'a-m')

    # Sort users alphabetically
    users = sorted(os.listdir(center_directory))

    skip_folder_set = {name.lower() for name in skip_folder_names}
    skip_user_name_set = {name.lower() for name in skip_user_names}
    skip_user_prefixes = [prefix for prefix in skip_user_prefixes if prefix]

    for user in users:
        if user.lower() in skip_user_name_set or any(user.startswith(prefix) for prefix in skip_user_prefixes):
            continue
        if user.lower() in skip_folder_set:
            continue

        user_directory = os.path.join(center_directory, user)
        if os.path.isdir(user_directory):
            # Pass the user and center_name to scan_user
            user_data = scan_user(user_directory, user_id, user, center_name, skip_hidden, skip_folder_names, file_writer)
            user_writer.writerow(user_data)  # Write user data (including folder times) to the users table
            user_id += 1

    end_time = time.time()
    end_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_time = round(end_time - start_time)
    formatted_total_time = format_time(total_time)
    print(f"Scan ended at: {end_datetime}")
    print(f"Total time taken: {formatted_total_time}")
    return user_id
        
        
def scan_dirs_and_write_csv(output_folder, group_directories, skip_hidden, skip_folder_names, skip_user_prefixes, skip_user_names, start_user_id):
    user_header = ['ID', 'NetID', 'Group', 'ScanTime', 'TotalFiles', 'TotalSizeBytes', 'LastModified', 'AccessDate', 'CreationDate']
    file_header = ['ID', 'NetID', 'Path', 'Name', 'SizeBytes', 'LastModified', 'AccessDate', 'CreationDate']
    with open(os.path.join(output_folder, 'users.csv'), 'w', newline='', errors='ignore') as user_csv, \
         open(os.path.join(output_folder, 'files.csv'), 'w', newline='', errors='ignore') as file_csv:
        user_writer = csv.writer(user_csv)
        file_writer = csv.writer(file_csv)
        user_writer.writerow(user_header)
        file_writer.writerow(file_header)
        user_id = start_user_id
        for directory in group_directories:
            user_id = scan_all_users(directory, user_id, skip_hidden, skip_folder_names, skip_user_prefixes, skip_user_names, user_writer, file_writer)
    return user_id


def run_scan(output_folder, directories, skip_hidden, skip_folder_names, skip_user_prefixes, skip_user_names, start_id):
    from scan_utils import format_time, scan_dirs_and_write_csv
    import os, time

    os.makedirs(output_folder, exist_ok=True)
    overall_start_time = time.time()
    scan_dirs_and_write_csv(output_folder, directories, skip_hidden, skip_folder_names, skip_user_prefixes, skip_user_names, start_id)
    overall_end_time = time.time()
    overall_total_time = round(overall_end_time - overall_start_time)
    formatted_overall_total_time = format_time(overall_total_time)
    print(f"Overall total time taken: {formatted_overall_total_time}")