import os
from bs4 import BeautifulSoup
import csv

OUT_DIR = 'responses/'
OUTPUT_CSV = 'dosare.csv'

# Creează CSV și scrie header
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "Numar Dosar",
        "Data Dosar",
        "Notificari Număr",
        "Notificari Data",
        "Solicitanti",
        "Adrese",
        "DPG",
        "Data Solutie",
        "Rezultat Solutie"
    ])

    for file_name in sorted(os.listdir(OUT_DIR)):
        if not file_name.endswith(".html"):
            continue
        path = os.path.join(OUT_DIR, file_name)
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')

            # Verifică dacă există dosar valid
            dosar_card = soup.find("h5", string=lambda t: t and "Rezultat căutare după dosarul" in t)
            if not dosar_card:
                print(f"⚠️ Dosar {file_name} anulat sau invalid, sărim.")
                continue

            # Numar și data dosar
            numar_tag = soup.find("span", string=lambda t: t and "Număr:" in t)
            numar_dosar = numar_tag.get_text(strip=True).replace("Număr:","") if numar_tag else ""
            data_tag = numar_tag.find_next("span") if numar_tag else None
            data_dosar = data_tag.get_text(strip=True).replace("Data:","") if data_tag else ""

            # Notificări (dacă există)
            notif_tags = soup.select("div.card-body .badge.text-bg-info")
            notif_num = notif_data = ""
            for idx, tag in enumerate(notif_tags):
                if "Notificare" in tag.text:
                    spans = tag.find_parent("div").find_all("span")
                    if len(spans) >= 2:
                        notif_num = spans[0].get_text(strip=True).replace("Număr:", "")
                        notif_data = spans[1].get_text(strip=True).replace("Data:", "")

            # Solicitanti
            solicitanti_tag = soup.find("h5", string=lambda t: t and "Solicitanți" in t)
            solicitanti = ""
            if solicitanti_tag:
                ol = solicitanti_tag.find_next("ol")
                if ol:
                    solicitanti = "; ".join(li.get_text(strip=True) for li in ol.find_all("li"))

            # Adrese
            adrese_tag = soup.find("h5", string=lambda t: t and "Adrese" in t)
            adrese = ""
            if adrese_tag:
                ol = adrese_tag.find_next("ol")
                if ol:
                    adrese = "; ".join(li.get_text(strip=True) for li in ol.find_all("li"))

            # Solutie dosar
            solutie_tag = soup.find("h5", string=lambda t: t and "Soluția la dosar" in t)
            dpg = data_sol = rezultat_sol = ""
            if solutie_tag:
                spans = solutie_tag.find_next("div").find_all("span")
                for span in spans:
                    text = span.get_text(strip=True)
                    if text.startswith("DPG:"):
                        dpg = text.replace("DPG:", "")
                    elif text.startswith("Dată:"):
                        data_sol = text.replace("Dată:", "")
                    else:
                        rezultat_sol = text.strip()

            # Scrie în CSV
            writer.writerow([
                numar_dosar,
                data_dosar,
                notif_num,
                notif_data,
                solicitanti,
                adrese,
                dpg,
                data_sol,
                rezultat_sol
            ])

print(f"✅ Toate datele extrase în {OUTPUT_CSV}")
