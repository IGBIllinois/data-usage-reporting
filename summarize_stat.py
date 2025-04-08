import pandas as pd
import os
from datetime import datetime
import time

# Start the timer
start_time = time.time()

# Define the base directory for results
base_dir = '/data/scan_output'  # on vm
# base_dir = 'data'  # on local machine

# Get all folders in the base directory
folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

# Get the latest folder based on modification time
folder_mod_times = [(folder, os.path.getmtime(os.path.join(base_dir, folder))) for folder in folders]
latest_folder = max(folder_mod_times, key=lambda x: x[1])[0]

# Print the latest folder being used
print(f"\nUsing the latest folder: {latest_folder}")

# Define the input folder dynamically
input_folder = os.path.join(base_dir, latest_folder)

# Initialize lists to store intermediate results
user_last_modified_list = []
inactive_file_count_list = []
small_file_count_list = []
largest_file_size_list = []
average_file_size_list = []
monthly_user_stats_list = []

# Read the entire 'files.csv' file into memory
files_df = pd.read_csv(
    f'{input_folder}/files.csv',
    usecols=['ID', 'NetID', 'LastModified', 'SizeBytes'],
    dtype={'ID': 'int32', 'NetID': 'object', 'SizeBytes': 'int64'},
    parse_dates=['LastModified']
)

# Calculate the most recent LastModified date for each user
user_last_modified_list.append(
    files_df.groupby(['ID', 'NetID'])['LastModified'].max().reset_index()
)

# Calculate Inactive Files (Files Not Modified in the Last 6 Months)
inactive_files = files_df[files_df['LastModified'] < pd.to_datetime('today') - pd.Timedelta(days=182)]
inactive_file_count_list.append(
    inactive_files.groupby(['ID', 'NetID']).size().reset_index(name='InactiveFileCount')
)

# Calculate Largest File Size Per User
largest_file_size_list.append(
    files_df.groupby(['ID', 'NetID'])['SizeBytes'].max().reset_index().rename(columns={'SizeBytes': 'LargestFileSize'})
)

# Calculate Small Files (Files Less Than 1KB)
small_files = files_df[files_df['SizeBytes'] < 1024]
small_file_count_list.append(
    small_files.groupby(['ID', 'NetID']).size().reset_index(name='SmallFileCount')
)

# Calculate Average File Size Per User
average_file_size_list.append(
    files_df.groupby(['ID', 'NetID'])['SizeBytes'].mean().reset_index().rename(columns={'SizeBytes': 'AverageFileSize'})
)

# Extract year and month from 'LastModified' for grouping
files_df['YearMonth'] = files_df['LastModified'].dt.to_period('M')

# Calculate total file size per user per year and month
monthly_total_storage_usage = files_df.groupby(['ID', 'NetID', 'YearMonth'])['SizeBytes'].sum().reset_index()
monthly_total_storage_usage = monthly_total_storage_usage.rename(columns={'SizeBytes': 'TotalStorageUsage'})

# Calculate the number of files per user per year and month
monthly_file_count = files_df.groupby(['ID', 'NetID', 'YearMonth']).size().reset_index(name='FileCount')

# Merge the monthly statistics together
monthly_user_stats_list.append(
    monthly_total_storage_usage.merge(monthly_file_count, on=['ID', 'NetID', 'YearMonth'], how='outer')
)

# Combine all intermediate results from lists into DataFrames
user_last_modified = pd.concat(user_last_modified_list, ignore_index=True)
inactive_file_count = pd.concat(inactive_file_count_list, ignore_index=True)
small_file_count = pd.concat(small_file_count_list, ignore_index=True)
largest_file_size = pd.concat(largest_file_size_list, ignore_index=True)
average_file_size = pd.concat(average_file_size_list, ignore_index=True)
monthly_user_stats = pd.concat(monthly_user_stats_list, ignore_index=True)

# Aggregate the monthly statistics
monthly_user_stats = monthly_user_stats.groupby(['ID', 'NetID', 'YearMonth']).sum().reset_index()

# Fill NaN values with 0 for file counts and total storage usage
monthly_user_stats.fillna(0, inplace=True)

# Ensure TotalStorageUsage and FileCount are integers in monthly_user_stats
monthly_user_stats['TotalStorageUsage'] = monthly_user_stats['TotalStorageUsage'].astype('int64')
monthly_user_stats['FileCount'] = monthly_user_stats['FileCount'].astype('int32')

# Load 'users.csv' with the required columns
users_df = pd.read_csv(
    f'{input_folder}/users.csv',
    usecols=['ID', 'NetID', 'Group', 'TotalFiles', 'TotalSizeBytes', 'LastModified'],
    parse_dates=['LastModified']
)

# Combine all user statistics into a single DataFrame
user_stats = user_last_modified.merge(inactive_file_count, on=['ID', 'NetID'], how='outer')
user_stats = user_stats.merge(small_file_count, on=['ID', 'NetID'], how='outer')
user_stats = user_stats.merge(largest_file_size, on=['ID', 'NetID'], how='outer')
user_stats = user_stats.merge(average_file_size, on=['ID', 'NetID'], how='outer')

# Fill NaN values with 0 for all statistics
user_stats.fillna(0, inplace=True)

# Merge the combined user statistics with users_df
all_users_stats = users_df.merge(user_stats, on=['ID', 'NetID'], how='left')

# Keep the latest (most recent) LastModified value for user_statistics.csv
all_users_stats['LastModified'] = all_users_stats[['LastModified_x', 'LastModified_y']].max(axis=1)

# Convert LastModified to date only (remove time)
all_users_stats['LastModified'] = all_users_stats['LastModified'].dt.date

# Drop the intermediate LastModified columns
all_users_stats.drop(columns=['LastModified_x', 'LastModified_y'], inplace=True)

# Fill NaN values with 0 for all columns in all_users_stats
all_users_stats.fillna(0, inplace=True)

# Ensure InactiveFileCount, SmallFileCount, and LargestFileSize are integers
all_users_stats['InactiveFileCount'] = all_users_stats['InactiveFileCount'].astype('int32')
all_users_stats['SmallFileCount'] = all_users_stats['SmallFileCount'].astype('int32')
all_users_stats['LargestFileSize'] = all_users_stats['LargestFileSize'].astype('int64')

# Save the results to a CSV file
output_folder = f'results/{latest_folder}'
os.makedirs(output_folder, exist_ok=True)
all_users_stats.to_csv(f'{output_folder}/user_statistics.csv', index=False)

# Save the monthly statistics to a CSV file
monthly_user_stats.to_csv(f'{output_folder}/monthly_user_statistics.csv', index=False)

print(f"\nResult statistics saved to {output_folder}")

# End the timer
end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
print(f"\nScript completed in {elapsed_time:.2f} seconds.")



