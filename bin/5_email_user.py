#!/usr/bin/env python3
import pandas as pd
import os
import json
import sys
from datetime import datetime

def main():
    # root_dir = os.path.abspath(os.getcwd())
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(root_dir + "/lib")
    from stat_utils import get_input_folder
    from email_utils import send_email
    
    # Load email config inside main
    with open('config/email_config.json') as f:
        email_config = json.load(f)

    SMTP_SERVER = email_config['smtp_server']
    SMTP_PORT = email_config['smtp_port']
    SENDER_EMAIL = email_config['sender_email']
    user_message= email_config['user_message']
    supervisor_message= email_config['supervisor_message']
    map_file = email_config['plot_map']


    scan_config = os.path.join(root_dir, "config", "scan_config.json")
    input_folder = get_input_folder(scan_config)
    pdf_dir = os.path.join(input_folder, 'plots')
    map_df = pd.read_csv(os.path.join(input_folder, map_file))
    supervisor_df = pd.read_csv(os.path.join(input_folder, email_config['user_supervisor']))

    # Ensure supervisor supervises themselves
    supervisor_df['supervised_user_ids'] = supervisor_df.apply(
        lambda row: ','.join(sorted(set(str(row['supervised_user_ids']).split(',') + [str(row['user_id'])]))), axis=1
    )
    # Build set of supervisor user_ids
    supervisor_ids = set(supervisor_df['user_id'].astype(str))
    # Build mapping from supervisor_id to supervised_user_ids (as set)
    supervisor_map = {str(row['user_id']): set(str(row['supervised_user_ids']).split(',')) for _, row in supervisor_df.iterrows()}

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
        print(f"Sending email to {user_name}")
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
            send_email(
                recipient=user_email,
                subject=subject,
                body=body,
                attachment_paths=user_attachments,
                sender_email=SENDER_EMAIL,
                smtp_server=SMTP_SERVER,
                smtp_port=SMTP_PORT
            )


if __name__ == "__main__":
    main()