import os
from bs4 import BeautifulSoup
import re
import pandas as pd

folder_html = "responses"
num_files = 2000  # doar primele 2000

# Listă pentru datele finale
tabel_dosare = []

html_files = [f for f in os.listdir(folder_html) if f.endswith(".html")]
html_files.sort(key=lambda x: int(x.split(".")[0]))
html_files = html_files[:num_files]

for idx, filename in enumerate(html_files, 1):
    nr_dosar = filename.split(".")[0]
    path = os.path.join(folder_html, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        soup = BeautifulSoup(content, "lxml")

    # Dosar anulat
    dosar_anulat = 'showAlert("Dosar anulat!", "alert-danger");' in content

    # Dosar PMB și Notificare PMB
    dosar_pmb = ""
    notificare_pmb = ""
    try:
        cards = soup.find_all("div", class_="card-body")
        for card in cards:
            h5 = card.find("h5", class_="card-title")
            if h5:
                text = h5.get_text(strip=True)
                if "Dosar PMB" in text:
                    spans = card.find_all("span", class_="btn btn-outline-dark")
                    for sp in spans:
                        if "Număr:" in sp.get_text():
                            dosar_pmb = sp.get_text(strip=True)
                        if "Data:" in sp.get_text():
                            dosar_pmb += " " + sp.get_text(strip=True)
                elif "Notificare PMB" in text:
                    spans = card.find_all("span", class_="btn btn-outline-dark")
                    for sp in spans:
                        if "Număr:" in sp.get_text():
                            notificare_pmb = sp.get_text(strip=True)
                        if "Data:" in sp.get_text():
                            notificare_pmb += " " + sp.get_text(strip=True)
    except:
        pass

    # Solicitanti
    solicitanti = []
    try:
        for card in cards:
            h5 = card.find("h5", class_="card-title")
            if h5 and "Solicitanți" in h5.get_text():
                ol = card.find("ol")
                if ol:
                    solicitanti = [li.get_text(strip=True) for li in ol.find_all("li")]
    except:
        pass

    # Adrese
    adrese = []
    adrese_contemporane = []
    adrese_istorice = []
    tip_proprietate = []
    try:
        for card in cards:
            h5 = card.find("h5", class_="card-title")
            if h5 and "Adrese" in h5.get_text():
                ol = card.find("ol")
                if ol:
                    for li in ol.find_all("li"):
                        text = li.get_text(strip=True)
                        adrese.append(text)
                        if "Istoric:" in text:
                            adrese_istorice.append(text)
                        else:
                            adrese_contemporane.append(text)
                        match = re.search(r"\(([^)]+)\)$", text)
                        tip_proprietate.append(match.group(1) if match else "")
    except:
        pass

    multiple_adrese = len(adrese) > 1 or len(tip_proprietate) > 1
    istorie_acte = ""

    tabel_dosare.append({
        "Dosar PMB": dosar_pmb,
        "Notificare PMB": notificare_pmb,
        "Solicitanți": ", ".join(solicitanti),
        "Adrese": ", ".join(adrese),
        "Adresa contemporană": ", ".join(adrese_contemporane),
        "Adresa istorică": ", ".join(adrese_istorice),
        "Tip proprietate": ", ".join(tip_proprietate),
        "Mai multe adrese/proprietăți": multiple_adrese,
        "Istorie acte": istorie_acte
    })

    if idx % 200 == 0:
        print(f"Procesate {idx} dosare din {num_files}")

# Creează DataFrame și export CSV
df = pd.DataFrame(tabel_dosare)
df.to_csv("dosare_primele_2000.csv", index=False, encoding="utf-8")
print("Tabelul pentru primele 2000 de dosare a fost creat în 'dosare_primele_2000.csv'.")
