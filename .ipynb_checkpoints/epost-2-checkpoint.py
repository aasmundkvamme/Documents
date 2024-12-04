# -*- coding: utf-8 -*-
"""
Created on Tue May 16 09:56:10 2023

@author: akv
"""

import smtplib
import aasmund
from email.mime.text import MIMEText

def send_email(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    smtp_server = smtplib.SMTP('smtp-ut.hvl.no', port=25)
    smtp_server.sendmail(sender, recipients, msg.as_string())
    smtp_server.quit()

subject = "Email Subject"
body = "This is the body of the text message"
sender = "aasmund.kvamme@hvl.no"
recipients = ["aasmund.kvamme@gmail.com"]
password = aasmund.HVL_passord

send_email(subject, body, sender, recipients, password)