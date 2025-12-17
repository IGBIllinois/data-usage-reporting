#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import sys
import json 

def main():
    # root_dir = os.path.abspath(os.getcwd())
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(root_dir + "/lib")
    from stat_utils import get_input_folder
    
    
    config_path = os.path.join(root_dir, "config", "scan_config.json")
    input_folder = get_input_folder(config_path)
    print(f"Input folder: {input_folder}")

    folder_to_use = os.path.basename(os.path.dirname(input_folder))
    current_year = int(folder_to_use[:4])
    current_date = f"{folder_to_use[:4]}-{folder_to_use[4:6]}-{folder_to_use[6:8]}"

    df = pd.read_csv(os.path.join(input_folder, 'yearly_statistics.csv'))
    user_stats = pd.read_csv(os.path.join(input_folder, 'user_statistics.csv'))
    bill_df = pd.read_csv(os.path.join(input_folder, 'current_user_project_bill.csv'))
    bill_df['data_name'] = bill_df['data_dir_path'].apply(lambda x: os.path.basename(str(x)))
    merged_df = user_stats.merge(bill_df, left_on='NetID', right_on='data_name', how='inner')
    # Format billed date to only keep the date part (YYYY-MM-DD)
    merged_df['data_bill_date'] = merged_df['data_bill_date'].astype(str).str[:10]
    # Check matching between user_stats.NetID and bill_df.data_name
    netids_set = set(user_stats['NetID'].unique())

    data_names_set = set(bill_df['data_name'].unique())
    not_in_bill = sorted(netids_set - data_names_set)
    not_in_users = sorted(data_names_set - netids_set)

    merged_df.to_csv(os.path.join(input_folder, 'merged_user_bill.csv'), index=False)
    pd.Series(not_in_users).to_csv(os.path.join(input_folder, 'not_in_users.csv'), index=False, header=False)
    pd.Series(not_in_bill).to_csv(os.path.join(input_folder, 'not_in_bill.csv'), index=False, header=False)

    # Rename Period to Year for plotting
    if 'Period' in df.columns:
        df = df.rename(columns={'Period': 'Year'})

    netids = merged_df['NetID'].unique()[:]
    output_dir = os.path.join(input_folder, 'plots')
    os.makedirs(output_dir, exist_ok=True)
    plot_map_path = os.path.join(input_folder, 'plot_map_all.csv')
    with open(plot_map_path, 'w') as f:
        f.write('plot_name,project,user_id,user_name,user_firstname,user_lastname,email\n')

    for netid in netids:
        # Get user statistics table for this NetID
        info = merged_df[merged_df['data_name'] == netid][[
            'NetID','data_name','data_dir_path','LastModified','TotalFiles','TotalSizeBytes','InactiveFileCount',
            'SmallFileCount','LargestFileSize','AvgFileSize','data_bill_avg_bytes','data_bill_total_cost','data_bill_billed_cost','data_bill_date',
            'user_id','user_name','user_firstname','user_lastname'
        ]]
        # Prepare user info text for annotation
        if not info.empty:
            user_info = info.iloc[0]
            table_data = [
                        ["Project", user_info['data_name']],
                        ["Path", user_info['data_dir_path']],
                        ["Last Modified", user_info['LastModified']],
                        ["Total Files", f"{int(user_info['TotalFiles']):,}"],
                        ["Inactive Files (> 6 months)", f"{int(user_info['InactiveFileCount']):,}"],
                        ["Small Files (< 1KB)", f"{int(user_info['SmallFileCount']):,}"],
                        ["Largest File (GB)", f"{user_info['LargestFileSize']/1024**3:.2f} GB"],
                        ["Average File (GB)", f"{user_info['AvgFileSize']/1024**3:.2f} GB"],
                        ["Total Size (TB)", f"{user_info['TotalSizeBytes']/1024**4:.4f} TB"],
                        ["Billed Date", user_info['data_bill_date']],
                        ["Bill Data (TB)", f"{user_info['data_bill_avg_bytes']/1024**4:.4f} TB"],
                        ["Storage Cost ($)", f"${user_info['data_bill_total_cost']:.2f}"],
                        ["Billed ($)", f"${user_info['data_bill_billed_cost']:.2f}"],
            ]
        else:
            table_data = [["No billing information available for NetID", netid]]

        yearly = df[df['NetID'] == netid].copy()
        
        # Convert bytes to GB
        yearly['TotalStorageUsageGB'] = yearly['FileSizeBytes'] / (1024 ** 3)

        # Only keep years with actual data (don't fill in empty years)
        # Filter out years with zero values if desired, or keep all years with data
        yearly = yearly[yearly['FileCount'] > 0]  # Only show years with files
        
        # Smart padding: only add padding if we have fewer than 5 data years
        if len(yearly) > 0:
            if len(yearly) >= 5:
                # If 5 or more data years, show only actual data years
                pass  # Keep yearly as is - only data years
            else:
                # If fewer than 5 data years, add padding for better visualization
                data_years = sorted([int(year) for year in yearly['Year']])
                min_year = min(data_years)
                max_year = max(data_years)
                
                # Extend range to have at least 5 years total
                years_needed = 5 - len(yearly)
                
                # Try to extend forward first, then backward if needed
                while years_needed > 0 and max_year < current_year:
                    max_year += 1
                    years_needed -= 1
                
                while years_needed > 0 and min_year > 1970:
                    min_year -= 1
                    years_needed -= 1
                
                # Create the padded year range
                yearly['Year'] = yearly['Year'].astype(int)
                all_years = list(range(min_year, max_year + 1))
                yearly = yearly.set_index('Year').reindex(all_years, fill_value=0).reset_index()

        # Create a figure with three subplots stacked vertically (info table at top, then two graphs)
        fig, axes = plt.subplots(3, 1, figsize=(8.27, 11.69), gridspec_kw={'height_ratios': [3, 4, 4]})


        total_gb = yearly['TotalStorageUsageGB'].sum()
        fig.suptitle(
            f'Biocluster Data Usage ({current_date}) \n Project: {netid}',
            fontsize=14, 
            fontweight='bold', 
            ha='center', 
            y=0.95, 
            linespacing=1.5
        )

        # Add the info table at the top
        axes[0].axis('off')
        table = axes[0].table(cellText=table_data, cellLoc='left', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.5)
        
        # Set background color for odd rows only (alternating rows)
        for i in range(len(table_data)):
            if i % 2 == 0:  # Odd rows (1st, 3rd, 5th... in 1-based counting)
                for j in range(len(table_data[0])):
                    table[(i, j)].set_facecolor('#C8C6C7')
        
        # Plot total storage usage in GB (top, fill #FF5F05, edge #13294B)
        axes[1].set_title(
            f'Total Storage Usage (GB) by Last Modified Year for {netid} (Total: {total_gb:.2f} GB)',
            loc='left', fontsize=12, fontstyle='italic', pad=8
        )
        bars = axes[1].bar(yearly['Year'], yearly['TotalStorageUsageGB'], color='#FF5F05', edgecolor='#13294B')
        axes[1].set_ylabel('Total Storage Usage (GB)')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        axes[1].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x)}'))
        axes[1].spines['top'].set_visible(False)
        axes[1].spines['right'].set_visible(False)
        axes[1].margins(y=0.15)
        for bar, value in zip(bars, yearly['TotalStorageUsageGB']):
            if value != 0:
                axes[1].text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f'{value:.2f}',
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    rotation=45
                )

        # Plot number of files (middle, fill #13294B, edge #FF5F05)
        axes[2].set_title(
            f'Number of Files by Last Modified Year for {netid} (Total: {int(yearly["FileCount"].sum()):,})',
            loc='left', fontsize=12, fontstyle='italic', pad=8
        )
        bars_files = axes[2].bar(yearly['Year'], yearly['FileCount'], color='#13294B', edgecolor='#FF5F05')
        axes[2].set_xlabel('Year')
        axes[2].set_ylabel('Number of Files')
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        axes[2].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x)}'))
        axes[2].spines['top'].set_visible(False)
        axes[2].spines['right'].set_visible(False)
        axes[2].margins(y=0.15)
        for bar, value in zip(bars_files, yearly['FileCount']):
            if value != 0:
                axes[2].text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f'{int(value):,}',
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    rotation=45
                )

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(os.path.join(output_dir, f"{netid}_{current_date}.pdf"), bbox_inches='tight')
#        plt.show()
        plt.close()

        # Append plot map row to CSV using user_info from merged_df
        if not info.empty:
            user_info = info.iloc[0]
            user_id = user_info.get('user_id', '')
            user_name = user_info.get('user_name', '')
            user_firstname = user_info.get('user_firstname', '')
            user_lastname = user_info.get('user_lastname', '')
        else:
            user_id = user_name = user_firstname = user_lastname = ''
        plot_name = f"{netid}_{current_date}.pdf"
        with open(plot_map_path, 'a') as f:
            f.write(f'{plot_name},{netid},{user_id},{user_name},{user_firstname},{user_lastname},\n')


if __name__ == "__main__":
    main()


