import os
import smtplib
from email.message import EmailMessage
import pandas as pd

def send_email(recipient, subject, body, attachment_paths, smtp_server, smtp_port, sender_email=None):
    """
    Send an email with one or multiple PDF attachments.
    attachment_paths: str (single file) or list of str (multiple files)
    """
    msg = EmailMessage()
    msg['From'] = sender_email if sender_email else 'noreply@localhost'
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_content(body)

    # Normalize to list
    if isinstance(attachment_paths, str):
        paths = [attachment_paths]
    elif isinstance(attachment_paths, list):
        paths = attachment_paths
    else:
        paths = []

    for pdf_path in paths:
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(pdf_path)
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.send_message(msg)