import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import creds


def send_email(subject, sender, recipient, text):
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = recipient

    html = MIMEText(text, "html")
    message.attach(html)

    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        if os.environ["EMAIL_USER"]:
            server.login(user=os.environ["EMAIL_USER"], password=os.environ["EMAIL_PASSWORD"])
        else:
            server.login(user=creds.USER, password=creds.PASSWORD)
        server.sendmail(from_addr=sender, to_addrs=recipient, msg=message.as_string())
