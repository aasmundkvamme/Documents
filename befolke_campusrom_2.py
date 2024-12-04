import requests
import aasmund
import pandas as pd
from datetime import date
import time
import smtplib
from email.mime.text import MIMEText

# Eg treng datoen for å sjekke kva semester vi er i
idag = date.today()

# Her er dei statiske kodene for campus og campusrom
campusnamn_stord = "STORD"
emnenummer_stord = 23313
sis_course_id_stord = "campusrom-STORD"
campusnamn_sogndal = "SOGNDAL"
emnenummer_sogndal = 23255
sis_course_id_sogndal = "campusrom-SOGNDAL"
campusnamn_førde = "FORDE"
emnenummer_førde = 23222
sis_course_id_førde = "campusrom-FORDE"
campusnamn_haugesund = "HAUGESUND"
emnenummer_haugesund = 23257
sis_course_id_haugesund = "campusrom-HAUGESUND"
campusnamn_bergen = "BERGEN"
emnenummer_bergen = 23258
sis_course_id_bergen = "campusrom-BERGEN"

# Set opp autorisasjon mot FS
parametreFS = {}
hodeFS = {
  'Accept': 'application/json;version=1',
  'Authorization': f'Basic {aasmund.tokenFS}'
}

# Set opp autorisasjon mot Canvas
hodeCanvas = {"Authorization": f'Bearer {aasmund.tokenCanvas}'}
parametreCanvas = {'per_page': 100}
baseurl = "https://hvl.instructure.com"
GraphQlurl = "https://hvl.instructure.com/api/graphql"

# Finn rett år og semester ut frå dagens dato
år = str(idag.year)
if idag.month >= 8:
    semester = 'HØST'
    semester_ascii = 'H%C3%98ST'
else:
    semester = 'VÅR'
    semester_ascii = 'V%C3%85R'

# Set opp sending av e-post:
avsendar = "aasmund.kvamme@hvl.no"
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

def graphql(query, variables):
    request = requests.post(GraphQlurl, json={'query': query, 'variables': variables}, headers=hodeCanvas)
    if request.status_code == 200:
        utdata = request.json()
    else:
        raise Exception("Feil i spørjing med kode {}. {}".format(request.status_code, query))
    try:
        print(f"Feil i spørjing: {utdata['errors'][0]['message']} (kode {request.status_code})")
    except KeyError:
        return utdata
    
    
def sis_import(filnamn, handling, campusnamn):
    url = "https://hvl.instructure.com/api/v1/accounts/1/sis_imports"
    filar = {'attachment': open(filnamn, 'rb')}
    r = requests.post(url, headers=hodeCanvas, files=filar)
    resultat = r.json()
    vent = True
    forseinking = 5
    if handling == "slett":
        print("Slettar studentar.")
    else:
        print("Legg til studentar.")
    while vent:
    # Her venter eg til alt er ferdig før eg tar neste campus
        jobb_id = resultat['id']
        time.sleep(forseinking)
        url = f"{baseurl}/api/v1/accounts/1/sis_imports/{jobb_id}"
        r = requests.get(url, headers=hodeCanvas)
        resultat = r.json()
        if resultat['progress']==100:
            print("Ferdig.")
            vent = False
        else:
            print(f"Arbeider framleis, {resultat['progress']} % ferdig.")


def oppdater_campus(emne, sis_course_id, campusnamn):
    
    # Overskrift i den løpande rapporten
    print(f"Ser på campusrom {campusnamn}:") 
    
    # Først ber eg om studentar frå Canvas
    query = """
    query courseInfo($courseId: ID!) {
      course(id: $courseId) {
        enrollmentsConnection(filter: {types: StudentEnrollment}) {
          nodes {
            user {
              sisId
            }
          }
        }
      }
    }
    """
    variables = {'courseId': emne}
    svar = graphql(query, variables)
    print(f"Har henta {len(svar['data']['course']['enrollmentsConnection']['nodes'])} studentar frå Canvas.")

    # Så lager eg ei liste over personløpenummer
    registrerte = []
    if svar['data'] != {'course': None}:
        for s in svar['data']['course']['enrollmentsConnection']['nodes']:
            registrerte.append(s['user']['sisId'])    

    # Så henter eg alle aktive studentar frå FS
    url = f"https://api.fellesstudentsystem.no/semesterregistreringer?limit=0&semester.ar={år}&semester.termin={semester}&campus.kode={campusnamn}"
    r = requests.get(url, headers=hodeFS, params=parametreFS)
    if r.status_code == 200:
        resultat = r.json()
        data = pd.DataFrame(resultat['items'])['href'].tolist()
        print(f"Har henta {len(data)} studentar frå FS.")
    else:
        print(f"Noko gjekk galt ved henting frå FS; kode {r.status_code}.")

    studentar = pd.DataFrame(data, columns=['temp']).temp.str.split(",", expand=True).rename(columns={0: "url", 1: "år", 2: "semester"})
    studentar.to_csv(f"studentar_{campusnamn}.csv")
    temp = studentar.loc[(studentar['år'] == år) & (studentar['semester'] == semester_ascii)]
    aktive = temp.assign(plnr=temp['url'].str[58:])

    # Så finn eg dei som skal slettast frå Canvas
    slettliste = []
    for s in svar['data']['course']['enrollmentsConnection']['nodes']:
        if s['user']['sisId'][7:] not in aktive['plnr'].values:
            slettliste.append([s['user']['sisId'], sis_course_id, 'student', 'deleted'])
    slettdesse = pd.DataFrame(slettliste, columns=['user_id', 'course_id', 'role', 'status'])
    slettdesse.to_csv("slettdesse.csv", index = None)
    print(f"Skal slette {len(slettliste)}.")
    
    # Ekstra: eg lager ein logg over alle som vert sletta, slik at vi eventuelt kan undersøke kvifor dei vart sletta:
    idag = date.today()
    slettdesse.to_csv(f"slettdesse_{campusnamn}_{idag}.csv", index = None)

    # Og dei som skal bli lagt til i Canvas
    leggtilliste = []
    for a in aktive['plnr']:
        if f"fs:203:{a}" not in registrerte:
            leggtilliste.append([f"fs:203:{a}", sis_course_id, 'student', 'active'])
    leggtildesse = pd.DataFrame(leggtilliste, columns=['user_id', 'course_id', 'role', 'status'])
    leggtildesse.to_csv("leggtildesse.csv", index=None)
    print(f"Skal legge til {len(leggtilliste)}.")

    # Og til slutt sender eg alt til Canvas som SIS-import (eg sender ikkje tomme filer)
    # Dersom det er mange studentar bør eg dele CSV-filene opp i mindre blokkar (på 2000 kvar):
    if len(slettliste) > 2000:
        slettlister = []
        n_blokker = len(slettliste) // 2000 + 1
        for i in range(n_blokker):
            slett = slettliste[(i-1)*2000:i*2000]
            slett.to_csv(f"slett_{i}.csv")
            slettlister.append(f"slett_{i}.csv")
        slett = slettliste[(n_blokker-1)*2000:]
        slett.to_csv(f"slett_{n_blokker}.csv")
        slettlister.append(f"slett_{n_blokker}.csv")
        for i in range(len(slettlister)):
            print(f"Behandler {slettlister[i]}")
            sis_import(slettlister[i], "slett", campusnamn)
    else:
        if len(slettliste) > 0:
            sis_import("slettdesse.csv", "slett", campusnamn)
    if len(leggtilliste) > 2000:
        leggtillister = []
        n_blokker = len(leggtilliste) // 2000 + 1
        for i in range(n_blokker):
            leggtil = leggtilliste[(i-1)*2000:i*2000]
            leggtil.to_csv(f"leggtil_{i}.csv")
            leggtillister.append(f"leggtil_{i}.csv")
        leggtil = leggtilliste[(n_blokker-1)*2000:]
        leggtil.to_csv(f"leggtil_{n_blokker}.csv")
        leggtillister.append(f"leggtil_{n_blokker}.csv")
        for i in range(len(leggtillister)):
            print(f"Behandler {leggtillister[i]}")
            sis_import(leggtillister[i], "leggtil", campusnamn)
    else:
        if len(leggtilliste) > 0:
            sis_import("leggtildesse.csv", "leggtil", campusnamn)
        
    kvittering = f"Har fjerna {len(slettliste)} og lagt til {len(leggtildesse)} studentar i {campusnamn}.\n"
    return kvittering


innhald = f"Rapport for oppdatering av campusrom {idag}\n\n"
innhald += oppdater_campus(emnenummer_førde, "campusrom-FORDE", campusnamn_førde)
innhald += oppdater_campus(emnenummer_sogndal, "campusrom-SOGNDAL", campusnamn_sogndal)
innhald += oppdater_campus(emnenummer_stord, "campusrom-STORD", campusnamn_stord)
innhald += oppdater_campus(emnenummer_haugesund, "campusrom-HAUGESUND", campusnamn_haugesund)
innhald += oppdater_campus(emnenummer_bergen, "campusrom-BERGEN", campusnamn_bergen)

# Send statusrapport
send_epost(tittel, innhald, avsendar, mottakarar)