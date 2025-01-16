import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from datetime import date, datetime, timedelta

today = date.today()
idag = today.isoformat()
igår = (today - timedelta(days=1)).isoformat()

def send_epost(tittel, innhald, avsender, mottakarar, vedlegg):
    msg = MIMEMultipart()
    msg['Subject'] = tittel
    msg['From'] = avsender
    msg['To'] = ', '.join(mottakarar)
    
    # Attach the email body to the message
    msg.attach(MIMEText(innhald, 'plain'))

    if vedlegg != "":
        try:
            with open(vedlegg, "rb") as attachment:
                # Create the attachment
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {vedlegg}')
                
                # Attach the file to the email
                msg.attach(part)
            
            # Set up the server and send the email
            smtp_server = smtplib.SMTP('smtp-ut.hvl.no', port=25)
            smtp_server.sendmail(avsender, mottakarar, msg.as_string())
            smtp_server.quit() 

        except Exception as e:
            print(f"Feil ved sending: {e}")
    else:
        smtp_server = smtplib.SMTP('smtp-ut.hvl.no', port=25)
        smtp_server.sendmail(avsender, mottakarar, msg.as_string())
        smtp_server.quit()

data = pd.read_csv("dagens_web_log.csv")
antal = len(data)
klikk = len(data[data['value.url'].str.contains('/images/thumbnails/')])

nye_lister = pd.DataFrame([{'dato': idag, 'profilbilete': klikk}])
gamle_lister = pd.read_csv("diverse_statistikk.csv")
oppdaterte_lister = pd.concat([nye_lister, gamle_lister]).groupby('dato').sum().reset_index()
oppdaterte_lister.to_csv("diverse_statistikk.csv", index=False)

avsendar = "aasmund.kvamme@hvl.no"
mottakarar = ["aasmund.kvamme@hvl.no"]
tittel = "Diverse statistikk frå web_log"
vedlegg = "diverse_statistikk.csv"
innhald = f"Andel klikk på profilbilete: {klikk/antal*100:.2f} ({klikk} av {antal})"

send_epost(tittel, innhald, avsendar, mottakarar, vedlegg)