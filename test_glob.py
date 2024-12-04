import glob
import os

# Finn alle filer som samsvarar med mønsteret "web_logs-*.txt"
filer = glob.glob("web_logs-*.txt")

# Sletta kvar fil
for fil in filer:
    try:
        os.remove(fil)
        print(f"Slettet fil: {fil}")
    except OSError as e:
        print(f"Error: {fil} : {e.strerror}")