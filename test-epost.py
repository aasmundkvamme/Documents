import requests
import aasmund
import pandas as pd
from datetime import date
import time
import smtplib
from email.mime.text import MIMEText

# Eg treng datoen for å sjekke kva semester vi er i
idag = date.today()

# Set opp sending av e-post:
avsendar = "aasmund.kvamme.test@hvl.no"
mottakarar = ["aasmund.kvamme@hvl.no"]
tittel = f"Vedlikehald av campusrom {idag}"


def send_epost(tittel, innhald, avsender, mottakarar):
    msg = MIMEText(innhald)
    msg['Subject'] = tittel
    msg['From'] = avsendar
    msg['To'] = ', '.join(mottakarar)
    smtp_server = smtplib.SMTP('smtp-ut.hvl.no', port=25)
    smtp_server.sendmail(avsendar, mottakarar, msg.as_string())
    smtp_server.quit() 

innhald = f"Testmelding, generert {idag}"
try:
    send_epost(tittel, innhald, avsendar, mottakarar)
except IOError as feil:
    print(feil)