import smtplib
import time
import random
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from dotenv import load_dotenv
from imapclient import IMAPClient
import pyzmail

# Load environment variables
load_dotenv()

# Multiple accounts
email_accounts = [
    {
        "name": "account1",
        "smtp_user": os.getenv("SMTP_USER_1"),
        "smtp_pass": os.getenv("SMTP_PASS_1"),
        "smtp_host": os.getenv("SMTP_HOST_1"),
        "smtp_port": int(os.getenv("SMTP_PORT_1")),
        "imap_user": os.getenv("IMAP_USER_1"),
        "imap_pass": os.getenv("IMAP_PASS_1"),
        "imap_host": os.getenv("IMAP_HOST_1"),
        "imap_port": int(os.getenv("IMAP_PORT_1")),
    },
    {
        "name": "account2",
        "smtp_user": os.getenv("SMTP_USER_2"),
        "smtp_pass": os.getenv("SMTP_PASS_2"),
        "smtp_host": os.getenv("SMTP_HOST_2"),
        "smtp_port": int(os.getenv("SMTP_PORT_2")),
        "imap_user": os.getenv("IMAP_USER_2"),
        "imap_pass": os.getenv("IMAP_PASS_2"),
        "imap_host": os.getenv("IMAP_HOST_2"),
        "imap_port": int(os.getenv("IMAP_PORT_2")),
    }
]

# Warm-up inboxes
warmup_inboxes = [
    "testinbox1@example.com",
    "testinbox2@example.com",
    "testinbox3@example.com"
]

def send_email(account, to_email, reply=False):
    subject = "Re: Warming up..." if reply else "Hello from warm-up bot"
    body = "Replying to your warm-up email." if reply else "Warming up this inbox. 😊"
    msg = MIMEText(body)
    msg['From'] = account["smtp_user"]
    msg['To'] = to_email
    msg['Subject'] = subject

    try:
        with smtplib.SMTP(account["smtp_host"], account["smtp_port"]) as server:
            server.starttls()
            server.login(account["smtp_user"], account["smtp_pass"])
            server.sendmail(account["smtp_user"], to_email, msg.as_string())
        print(f"[{account['name']}] Sent {'reply' if reply else 'email'} to {to_email}")
    except Exception as e:
        print(f"[{account['name']}] Failed to send to {to_email}: {e}")

def check_and_reply(account):
    try:
        with IMAPClient(account["imap_host"], port=account["imap_port"], ssl=True) as client:
            client.login(account["imap_user"], account["imap_pass"])
            folders = [b"INBOX", b"Spam", b"Junk"]

            for folder in folders:
                client.select_folder(folder.decode("utf-8"), readonly=False)
                since = datetime.now() - timedelta(days=1)
                messages = client.search(['SINCE', since.strftime('%d-%b-%Y')])

                for uid in messages:
                    raw_message = client.fetch([uid], ['BODY[]', 'FLAGS'])[uid][b'BODY[]']
                    message = pyzmail.PyzMessage.factory(raw_message)
                    subject = message.get_subject()
                    sender = message.get_address('from')[1]

                    if account["smtp_user"] in subject or account["smtp_user"] in sender:
                        print(f"[{account['name']}] Found message in {folder.decode()} from {sender}")
                        if folder.lower() in [b"spam", b"junk"]:
                            client.move([uid], 'INBOX')
                            print(f"[{account['name']}] Moved email to INBOX")
                        client.add_flags([uid], [b'\\Seen'])
                        send_email(account, sender, reply=True)
    except Exception as e:
        print(f"[{account['name']}] IMAP error: {e}")

def run_warmup():
    for account in email_accounts:
        day = datetime.now().day
        emails_today = min(day * 2, len(warmup_inboxes))
        today_targets = random.sample(warmup_inboxes, emails_today)

        print(f"--- Warming up {account['name']} ---")
        for email_addr in today_targets:
            send_email(account, email_addr)
            wait = random.randint(60, 180)
            print(f"⏱ Waiting {wait}s before next email...")
            time.sleep(wait)

        print(f"🔍 Checking {account['name']} inbox for spam rescue and replies...")
        check_and_reply(account)

run_warmup()
