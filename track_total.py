import pandas as pd
import os
from datetime import datetime

# Define the base directory for results
base_dir = 'results/'

# Get all folders in the base directory (ignore files)
folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

# Print the modification time for each folder
print("Folders and their modification times:")
folder_mod_times = []
for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    mod_time = os.path.getmtime(folder_path)
    folder_mod_times.append((folder, mod_time))
    print(f"{folder}: {datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')}")

# Get the latest folder based on modification time
latest_folder, latest_mod_time = max(folder_mod_times, key=lambda x: x[1])

# Print the latest folder being used
print(f"\nUsing the latest folder: {latest_folder}")

# Convert the latest folder's modification time to a date string
folder_date = datetime.fromtimestamp(latest_mod_time).strftime('%Y-%m-%d')

# Define the input and output file paths
input_file = os.path.join(base_dir, latest_folder, 'user_statistics.csv')
output_file = os.path.join(base_dir, 'running_summary.csv')

# Read the user statistics CSV file
all_users_stats = pd.read_csv(input_file)

# Summarize TotalSizeBytes for each Group
group_summary = all_users_stats.groupby('Group')['TotalSizeBytes'].sum().reset_index()

# Define a mapping for group renaming
group_mapping = {
    'a-m': 'Users',
    'n-z': 'Users',
    'labs': 'Labs',
    'groups': 'Groups'
}

# Apply the mapping to the Group column
group_summary['Group'] = group_summary['Group'].map(group_mapping)

# Recalculate the total size for combined groups
group_summary = group_summary.groupby('Group')['TotalSizeBytes'].sum().reset_index()

# Add the folder's modification date and timestamp to the summary
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
group_summary['Date'] = folder_date
group_summary['Timestamp'] = timestamp

# Calculate the total size across all groups and add it as a new row
total_size = group_summary['TotalSizeBytes'].sum()
total_row = pd.DataFrame({'Group': ['Total'], 'TotalSizeBytes': [total_size], 'Date': [folder_date], 'Timestamp': [timestamp]})
group_summary = pd.concat([group_summary, total_row], ignore_index=True)

# Check if the output file exists
if os.path.exists(output_file):
    # If it exists, read the existing data
    existing_summary = pd.read_csv(output_file)
    
    # Concatenate the new data with the existing data
    group_summary = pd.concat([existing_summary, group_summary], ignore_index=True)

# Save the updated summary to the output file
group_summary.to_csv(output_file, index=False)

print(f"Summary saved to {output_file}")