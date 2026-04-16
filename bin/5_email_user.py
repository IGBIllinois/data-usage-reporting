#!/usr/bin/env python3
import pandas as pd
import os
import json
import sys
import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Send email reports to users')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what emails would be sent without actually sending them')
    parser.add_argument('--config-dir', type=str, default='config',
                        help='Config folder path, relative to project root or absolute (default: config)')
    args = parser.parse_args()
    
    # Initialize summary counters
    summary = {'users': 0, 'supervisors': 0, 'total_attachments': 0}
    
    if args.dry_run:
        print("\n=== DRY RUN MODE - No emails will be sent ===\n")
    # root_dir = os.path.abspath(os.getcwd())
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(root_dir + "/lib")
    from stat_utils import get_input_folder
    from email_utils import send_email

    if os.path.isabs(args.config_dir):
        config_dir = args.config_dir
    else:
        config_dir = os.path.join(root_dir, args.config_dir)
    
    # Load email config inside main
    email_config_path = os.path.join(config_dir, "email_config.json")
    with open(email_config_path) as f:
        email_config = json.load(f)

    SMTP_SERVER = email_config['smtp_server']
    SMTP_PORT = email_config['smtp_port']
    SENDER_EMAIL = email_config['sender_email']
    user_message= email_config['user_message']
    supervisor_message= email_config['supervisor_message']
    map_file = email_config['plot_map']


    scan_config = os.path.join(config_dir, "scan_config.json")
    input_folder = get_input_folder(scan_config)
    pdf_dir = os.path.join(input_folder, 'plots')
    map_df = pd.read_csv(os.path.join(input_folder, map_file))
    supervisor_df = pd.read_csv(os.path.join(input_folder, email_config['user_supervisor']))

    # Ensure supervisor supervises themselves
    supervisor_df['supervised_user_ids'] = supervisor_df.apply(
        lambda row: ','.join(sorted(set(str(row['supervised_user_ids']).split(',') + [str(row['supervisor_id'])]))), axis=1
    )
    # Build set of supervisor user_ids
    supervisor_ids = set(supervisor_df['supervisor_id'].astype(str))
    # Build mapping from supervisor_id to supervised_user_ids (as set)
    supervisor_map = {str(row['supervisor_id']): set(str(row['supervised_user_ids']).split(',')) for _, row in supervisor_df.iterrows()}

    # Get current year and month
    now = datetime.now()
    year_month = now.strftime("%Y-%m")
    
    # Only send supervisor emails for supervisors present in map_df
    map_user_ids = set(map_df['user_id'].astype(str))
    # Group map_df by user_id
    grouped = map_df.groupby(map_df['user_id'].astype(str))
    for user_id, group in grouped:
        # Use first row for name/email info
        row = group.iloc[0]
        user_email = str(row.get('email', '')).strip()
        if user_email.lower() == 'nan' or not user_email:
            user_email = row['user_name'] + '@igb.illinois.edu'
        subject = f"Biocluster Data Usage Report ({year_month})"
        user_name = row['user_name']
        # Collect all PDFs for this user
        user_attachments = []
        for _, user_row in group.iterrows():
            plot_name = user_row['plot_name']
            pdf_path_user = os.path.join(pdf_dir, plot_name)
            if os.path.exists(pdf_path_user):
                user_attachments.append(pdf_path_user)
        # Supervisor or regular user
        if user_id in supervisor_ids and user_id in map_user_ids:
            # Supervisor: also collect supervised users' PDFs
            supervised_ids = supervisor_map[user_id]
            attachments = list(user_attachments)
            names = []
            for uid in supervised_ids:
                uid = uid.strip()
                if uid not in map_user_ids:
                    continue
                for _, user_row in map_df[map_df['user_id'].astype(str) == uid].iterrows():
                    plot_name = user_row['plot_name']
                    pdf_path_supervised = os.path.join(pdf_dir, plot_name)
                    if os.path.exists(pdf_path_supervised):
                        if pdf_path_supervised not in attachments:
                            attachments.append(pdf_path_supervised)
                        names.append(user_row.get('user_firstname', uid))
            supervisor_body = f"Dear {row['user_firstname']} {row['user_lastname']},\n\n{supervisor_message}"
            summary['supervisors'] += 1
            summary['total_attachments'] += len(attachments)
            if not args.dry_run:
                send_email(
                    recipient=user_email,
                    subject=subject,
                    body=supervisor_body,
                    attachment_paths=attachments,
                    sender_email=SENDER_EMAIL,
                    smtp_server=SMTP_SERVER,
                    smtp_port=SMTP_PORT
                )
        else:
            body = f"Dear {row['user_firstname']} {row['user_lastname']},\n\n{user_message}"
            summary['users'] += 1
            summary['total_attachments'] += len(user_attachments)
            if not args.dry_run:
                send_email(
                    recipient=user_email,
                    subject=subject,
                    body=body,
                    attachment_paths=user_attachments,
                    sender_email=SENDER_EMAIL,
                    smtp_server=SMTP_SERVER,
                    smtp_port=SMTP_PORT
                )
    
    # Print summary
    if args.dry_run:
        print(f"\n=== DRY RUN SUMMARY ===")
        print(f"Total emails that would be sent: {summary['users'] + summary['supervisors']}")
        print(f"  - Regular users: {summary['users']}")
        print(f"  - Supervisors: {summary['supervisors']}")
        print(f"Total attachments: {summary['total_attachments']}")
        print(f"\nNo emails were actually sent.\n")
    else:
        print(f"\n=== EMAIL SUMMARY ===")
        print(f"Total emails sent: {summary['users'] + summary['supervisors']}")
        print(f"  - Regular users: {summary['users']}")
        print(f"  - Supervisors: {summary['supervisors']}")
        print(f"Total attachments sent: {summary['total_attachments']}")
        print(f"\nEmails sent successfully.\n")


if __name__ == "__main__":
    main()