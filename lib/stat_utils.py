import json
import os
import pandas as pd


def get_latest_folder(base_dir):
    """
    Returns the name of the latest modified folder in the given base directory.
    """
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    if not folders:
        return None
    folder_mod_times = [(folder, os.path.getmtime(os.path.join(base_dir, folder))) for folder in folders]
    latest_folder = max(folder_mod_times, key=lambda x: x[1])[0]
    return latest_folder

def summarize_stats(subfolder_path, summary_type='yearly'):
    """
    Summarizes user and statistics for a single subfolder and returns DataFrames.
    summary_type: 'monthly' or 'yearly'
    """
    # Read files.csv
    files_csv_path = os.path.join(subfolder_path, 'files.csv')
    files_df = pd.read_csv(
        files_csv_path,
        usecols=['ID', 'NetID', 'LastModified', 'SizeBytes'],
        dtype={'ID': 'int32', 'NetID': 'object', 'SizeBytes': 'int64'},
    )
    # Force datetime conversion
    files_df['LastModified'] = pd.to_datetime(
        files_df['LastModified'],
        errors='coerce'
    )
    files_df = files_df.dropna(subset=['LastModified'])

    # Calculate statistics
    user_last_modified = files_df.groupby(['ID', 'NetID'])['LastModified'].max().reset_index()
    # Clean day-based cutoff
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=182)
    inactive_files = files_df[files_df['LastModified'] < cutoff]
    inactive_file_count = inactive_files.groupby(['ID', 'NetID']).size().reset_index(name='InactiveFileCount')
    largest_file_size = files_df.groupby(['ID', 'NetID'])['SizeBytes'].max().reset_index().rename(columns={'SizeBytes': 'LargestFileSize'})
    small_files = files_df[files_df['SizeBytes'] < 1024]
    small_file_count = small_files.groupby(['ID', 'NetID']).size().reset_index(name='SmallFileCount')
    average_file_size = files_df.groupby(['ID', 'NetID'])['SizeBytes'].mean().reset_index().rename(columns={'SizeBytes': 'AvgFileSize'})

    # Monthly or Yearly statistics
    if summary_type == 'monthly':
        files_df['Period'] = files_df['LastModified'].dt.to_period('M')
    elif summary_type == 'yearly':
        files_df['Period'] = files_df['LastModified'].dt.year
    else:
        raise ValueError("summary_type must be 'monthly' or 'yearly'")

    total_storage_usage = files_df.groupby(['ID', 'NetID', 'Period'])['SizeBytes'].sum().reset_index().rename(columns={'SizeBytes': 'FileSizeBytes'})
    file_count = files_df.groupby(['ID', 'NetID', 'Period']).size().reset_index(name='FileCount')
    user_stats_period = total_storage_usage.merge(file_count, on=['ID', 'NetID', 'Period'], how='outer')
    user_stats_period.fillna(0, inplace=True)
    user_stats_period['FileSizeBytes'] = user_stats_period['FileSizeBytes'].astype('int64')
    user_stats_period['FileCount'] = user_stats_period['FileCount'].astype('int32')

    # Read users.csv
    users_csv_path = os.path.join(subfolder_path, 'users.csv')
    users_df = pd.read_csv(
        users_csv_path,
        usecols=['ID', 'NetID', 'Group', 'TotalFiles', 'TotalSizeBytes', 'LastModified'],
        parse_dates=['LastModified']
    )
    user_stats = user_last_modified.merge(inactive_file_count, on=['ID', 'NetID'], how='outer')
    user_stats = user_stats.merge(small_file_count, on=['ID', 'NetID'], how='outer')
    user_stats = user_stats.merge(largest_file_size, on=['ID', 'NetID'], how='outer')
    user_stats = user_stats.merge(average_file_size, on=['ID', 'NetID'], how='outer')
    user_stats.fillna(0, inplace=True)

    # Merge with users.csv
    all_users_stats = users_df.merge(user_stats, on=['ID', 'NetID'], how='left')
    all_users_stats['LastModified'] = all_users_stats[['LastModified_x', 'LastModified_y']].max(axis=1)
    all_users_stats['LastModified'] = all_users_stats['LastModified'].dt.date
    all_users_stats.drop(columns=['LastModified_x', 'LastModified_y'], inplace=True)
    all_users_stats.fillna(0, inplace=True)
    all_users_stats['InactiveFileCount'] = all_users_stats['InactiveFileCount'].astype('int32')
    all_users_stats['SmallFileCount'] = all_users_stats['SmallFileCount'].astype('int32')
    all_users_stats['LargestFileSize'] = all_users_stats['LargestFileSize'].astype('int64')

    return all_users_stats, user_stats_period

def write_stats_to_csv(user_stats_df, summary_stats_df, output_path, summary_type='yearly'):
    """
    Writes user and summary statistics DataFrames to CSV files in the output path.
    summary_type: 'monthly' or 'yearly' determines the filename for the summary stats.
    """
    os.makedirs(output_path, exist_ok=True)
    user_stats_df.to_csv(os.path.join(output_path, 'user_statistics.csv'), index=False)
    if summary_type == 'monthly':
        summary_stats_df.to_csv(os.path.join(output_path, 'monthly_statistics.csv'), index=False)
    elif summary_type == 'yearly':
        summary_stats_df.to_csv(os.path.join(output_path, 'yearly_statistics.csv'), index=False)
    else:
        raise ValueError("summary_type must be 'monthly' or 'yearly'")

def summarize_and_write_stats(input_folder, output_folder, summary_type):
    """
    Iterates over subfolders, summarizes statistics, and writes results to output_folder.
    summary_type: 'monthly', 'yearly', or 'both' (direct input, no config file)
    """
    subfolders = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]
    for subfolder in subfolders:
        subfolder_path = os.path.join(input_folder, subfolder)
        subfolder_output_path = os.path.join(output_folder, subfolder)
        if summary_type == 'monthly':
            user_stats_df, summary_stats_df = summarize_stats(subfolder_path, summary_type='monthly')
            write_stats_to_csv(user_stats_df, summary_stats_df, subfolder_output_path, summary_type='monthly')
        elif summary_type == 'yearly':
            user_stats_df, summary_stats_df = summarize_stats(subfolder_path, summary_type='yearly')
            write_stats_to_csv(user_stats_df, summary_stats_df, subfolder_output_path, summary_type='yearly')
        elif summary_type == 'both':
            user_stats_df, monthly_stats_df = summarize_stats(subfolder_path, summary_type='monthly')
            _, yearly_stats_df = summarize_stats(subfolder_path, summary_type='yearly')
            write_stats_to_csv(user_stats_df, monthly_stats_df, subfolder_output_path, summary_type='monthly')
            write_stats_to_csv(user_stats_df, yearly_stats_df, subfolder_output_path, summary_type='yearly')
        else:
            raise ValueError("summary_type must be 'monthly', 'yearly', or 'both'")


def combine_stats(output_folder, summary_type='yearly'):
    """
    Combines user_statistics.csv and summary statistics (monthly or yearly) from all subfolders in output_folder into a 'combined' subfolder.

    Args:
        output_folder (str): Path to the folder containing subfolders with statistics CSVs.
        summary_type (str): 'monthly' or 'yearly' (default: 'yearly')
    """

    combined_folder = os.path.join(output_folder, 'combined')
    os.makedirs(combined_folder, exist_ok=True)

    combined_user_statistics = pd.DataFrame()
    combined_summary_statistics = pd.DataFrame()

    subfolders = [f for f in os.listdir(output_folder) if os.path.isdir(os.path.join(output_folder, f))]

    for subfolder in subfolders:
        subfolder_path = os.path.join(output_folder, subfolder)
        if subfolder == 'combined':
            continue

        user_statistics_path = os.path.join(subfolder_path, 'user_statistics.csv')
        if summary_type == 'monthly':
            summary_statistics_path = os.path.join(subfolder_path, 'monthly_statistics.csv')
        elif summary_type == 'yearly':
            summary_statistics_path = os.path.join(subfolder_path, 'yearly_statistics.csv')
        else:
            raise ValueError("summary_type must be 'monthly' or 'yearly'")

        if os.path.exists(user_statistics_path):
            user_statistics_df = pd.read_csv(user_statistics_path)
            combined_user_statistics = pd.concat([combined_user_statistics, user_statistics_df], ignore_index=True)

        if os.path.exists(summary_statistics_path):
            summary_statistics_df = pd.read_csv(summary_statistics_path)
            combined_summary_statistics = pd.concat([combined_summary_statistics, summary_statistics_df], ignore_index=True)

    combined_user_statistics_path = os.path.join(combined_folder, 'user_statistics.csv')
    combined_summary_statistics_path = os.path.join(combined_folder, f'{summary_type}_statistics.csv')

    combined_user_statistics.to_csv(combined_user_statistics_path, index=False)
    combined_summary_statistics.to_csv(combined_summary_statistics_path, index=False)

    print(f"Combined statistics saved to {combined_folder}")
    

def summarize_mysql_bill(csv_path, output_summary_path=None):
    """
    Summarizes the mysql_recent_12_bill.csv file:
    1. Formats the 'time' column to year-month (YYYY-MM).
    2. Extracts the middle part (e.g., a-m) from 'data_dir_path' into a new column 'Category'.
    3. Sums 'data_bill_avg_bytes' for each Category and converts to TB.
    Saves summary to output_summary_path if provided.
    Returns the summary DataFrame.
    """
    df = pd.read_csv(csv_path)
    # (1) Format time column to year-month only
    df['year_month'] = pd.to_datetime(df['data_bill_date']).dt.strftime('%Y-%m')

    # (2) Extract category from data_dir_path
    df['Category'] = df['data_dir_path'].apply(lambda x: str(x).split('/')[-2] if isinstance(x, str) and len(x.split('/')) > 2 else '')
    # Rename Category to 'user' if it is 'a-m' or 'n-z'
    df['Category'] = df['Category'].replace({'a-m': 'users', 'n-z': 'users'})

    # (3) Sum data_bill_avg_bytes for each year_month and Category and convert to TB
    summary = df.groupby(['year_month', 'Category'])['data_bill_avg_bytes'].sum().reset_index()
    summary['data_bill_avg_TB'] = summary['data_bill_avg_bytes'] / (1024**4)
    summary = summary[['year_month', 'Category', 'data_bill_avg_TB']]

    # Only keep Users, Labs, Groups before calculating 'Other'
    allowed = ['users', 'labs', 'groups']
    filtered = summary[summary['Category'].isin(allowed)].copy()

    # Add 'Other' category: 1.2PB minus sum of allowed categories for each year_month
    total_pb = 1.2
    total_tb = total_pb * 1024  # Convert PB to TB
    other_rows = []
    for ym in filtered['year_month'].unique():
        tb_sum = filtered.loc[filtered['year_month'] == ym, 'data_bill_avg_TB'].sum()
        other_tb = total_tb - tb_sum
        other_rows.append({'year_month': ym, 'Category': 'other', 'data_bill_avg_TB': other_tb})
    summary = pd.concat([filtered, pd.DataFrame(other_rows)], ignore_index=True)
    # Capitalize first letter of each category in summary (do only once at the end)
    summary['Category'] = summary['Category'].str.capitalize()

    if output_summary_path:
        summary.to_csv(output_summary_path, index=False)
    return summary

def get_input_folder(config_file):
    with open(config_file) as f:
        profile = json.load(f)
    results_dir = profile.get('results_dir', 'results')
    target_folder = profile.get('target_folder', '').strip()
    plot_dir = profile.get('plot_dir', 'combined')
    if target_folder:
        folder_to_use = target_folder
    else:
        folder_to_use = get_latest_folder(results_dir)
    input_folder = os.path.join(results_dir, folder_to_use, plot_dir)
    return input_folder