#!/usr/bin/env python3
import os
import sys
import mysql.connector
import csv
import json
import pandas as pd
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run MySQL queries and summarize billing output")
    parser.add_argument("--config-dir", type=str, default="config",
                        help="Config folder path, relative to project root or absolute (default: config)")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(root_dir + "/lib")
    from stat_utils import get_latest_folder, summarize_mysql_bill

    if os.path.isabs(args.config_dir):
        config_dir = args.config_dir
    else:
        config_dir = os.path.join(root_dir, args.config_dir)

    # Load MySQL config
    MYSQL_CONFIG_FILE = os.path.join(config_dir, 'mysql_config.json')
    with open(MYSQL_CONFIG_FILE, 'r') as f:
        mysql_config = json.load(f)

    with open(os.path.join(config_dir, "scan_config.json")) as f:
        scan_config = json.load(f)

    results_dir = scan_config.get('results_dir', 'results')
    combined_folder = os.path.join(results_dir,get_latest_folder(results_dir), 'combined')
    os.makedirs(combined_folder, exist_ok=True)


    # Connect to MySQL
    mysql_config['connection']['user'] = os.environ.get('MYSQL_USER')
    mysql_config['connection']['password'] = os.environ.get('MYSQL_PASSWORD')
    conn_details = mysql_config['connection']
    conn_details['auth_plugin'] = 'mysql_clear_password'
    conn = mysql.connector.connect(**conn_details)
    cursor = conn.cursor()

    for query_name, query_info in mysql_config['queries'].items():
        sql = query_info['sql']
        output_file = os.path.join(combined_folder, query_info['output'])
        print(f"Running query '{query_name}'")
        cursor.execute(sql)
        rows = cursor.fetchall()
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerows(rows)
        print(f"Results written to {output_file}")


    cursor.close()
    conn.close()

    # --- Post-processing mysql_recent_12_bill.csv ---
    bill_path = os.path.join(combined_folder, 'mysql_recent_12_bill.csv')
    bill_summary_path = os.path.join(combined_folder, 'recent_12_bill_summary.csv')
    summarize_mysql_bill(bill_path,bill_summary_path)
if __name__ == '__main__':
    main()