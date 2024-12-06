import requests
import sys
import pandas as pd
import gzip
import shutil
from datetime import date, datetime
import time
import aasmund
import smtplib
from email.mime.text import MIMEText
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import glob
import logging

base_url = aasmund.CD2_base_url
client_id = aasmund.CD2_client_id
client_secret = aasmund.CD2_client_secret
avsendar = "aasmund.kvamme@hvl.no"
mottakarar = ["aasmund.kvamme@hvl.no"]
# mottakarar = ["aasmund.kvamme@hvl.no", "alisa.rysaeva@hvl.no", "rdeb@hvl.no"]
tittel = "CD2 web log"
idag = date.today().isoformat()

def send_epost(tittel, innhald, avsender, mottakarar):
    msg = MIMEMultipart()
    msg['Subject'] = tittel
    msg['From'] = avsender
    msg['To'] = ', '.join(mottakarar)
    
    # Attach the email body to the message
    msg.attach(MIMEText(innhald, 'plain'))

    # Specify the file to be sent
    filename = "plattformbruk.csv"
    
    try:
        with open(filename, "rb") as attachment:
            # Create the attachment
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {filename}')
            
            # Attach the file to the email
            msg.attach(part)
        
        # Set up the server and send the email
        smtp_server = smtplib.SMTP('smtp-ut.hvl.no', port=25)
        smtp_server.sendmail(avsender, mottakarar, msg.as_string())
        smtp_server.quit() 
        logger.info(f"Sendte e-post til {', '.join(mottakarar)}")

    except Exception as e:
        logger.error(f"Feil ved sending av e-post: {e}")




# opprett ein logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Sett ønska loggnivå

# Opprett formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Opprett filhandler for å logge til fil (ein loggfil kvar dag)
file_handler = logging.FileHandler(f'loggfil-web_log-{idag}.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Opprett konsollhandler for å logge til konsollen
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Legg til handlerne i loggeren
logger.addHandler(file_handler)
logger.addHandler(console_handler)


innhald = f"Resultat frå web_log {idag}\n"


send_epost(tittel, innhald, avsendar, mottakarar)