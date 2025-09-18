import os
from bs4 import BeautifulSoup
from collections import Counter
import re
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

folder_html = "responses"

# Funcție pentru procesarea unui singur fișier
def procesare_fisier(path):
    result = {
        "nr_dosar": None,
        "dosar_anulat": False,
        "solicitanti": [],
        "adrese": [],
        "proprietati": []
    }

    nr_dosar = os.path.basename(path).split(".")[0]
    result["nr_dosar"] = nr_dosar

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            soup = BeautifulSoup(content, "lxml")  # mai rapid decât 'html.parser'

        # --- Dosar anulat ---
        if 'showAlert("Dosar anulat!", "alert-danger");' in content:
            result["dosar_anulat"] = True

        # --- Solicitanti ---
        try:
            solicitanti_cards = soup.find_all("div", class_="card-body")
            for card in solicitanti_cards:
                h5 = card.find("h5", class_="card-title")
                if h5 and "Solicitanți" in h5.get_text():
                    ol = card.find("ol")
                    if ol:
                        result["solicitanti"].extend([li.get_text(strip=True) for li in ol.find_all("li")])
        except:
            pass

        # --- Adrese și Proprietăți ---
        try:
            adrese_cards = soup.find_all("div", class_="card-body")
            for card in adrese_cards:
                h5 = card.find("h5", class_="card-title")
                if h5 and "Adrese" in h5.get_text():
                    ol = card.find("ol")
                    if ol:
                        for li in ol.find_all("li"):
                            text = li.get_text(strip=True)
                            result["adrese"].append(text)
                            # Tip proprietate în paranteze
                            match_prop = re.search(r"\(([^)]+)\)$", text)
                            if match_prop:
                                result["proprietati"].append(text)
        except:
            pass

    except Exception as e:
        print(f"Eroare la dosar {nr_dosar}: {e}")

    return result


def main():
    html_files = [os.path.join(folder_html, f) for f in os.listdir(folder_html) if f.endswith(".html")]
    html_files.sort(key=lambda x: int(os.path.basename(x).split(".")[0]))

    # Counters
    tipuri_proprietati_counter = Counter()
    tipuri_adrese_istorice_counter = Counter()
    tipuri_adrese_contemporane_counter = Counter()
    persoane_tip_counter = Counter()
    num_solicitanti_counter = Counter()
    num_adrese_counter = Counter()
    num_proprietati_per_dosar_counter = Counter()

    dosare_anulate_list = []
    dosare_zero_solicitanti = []
    dosare_zero_adrese = []
    dosare_zero_proprietati = []

    dosare_anulate = 0
    dosare_corecte = 0

    # Folosim multiprocessing
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(procesare_fisier, path) for path in html_files]

        for idx, future in enumerate(as_completed(futures), 1):
            res = future.result()
            nr_dosar = res["nr_dosar"]

            # --- Dosar anulat ---
            if res["dosar_anulat"]:
                dosare_anulate += 1
                dosare_anulate_list.append(nr_dosar)
            else:
                dosare_corecte += 1

            # --- Solicitanti ---
            solicitanti = res["solicitanti"]
            num_solicitanti_counter[len(solicitanti)] += 1
            if len(solicitanti) == 0:
                dosare_zero_solicitanti.append(nr_dosar)

            for s in solicitanti:
                if any(x in s for x in ["SRL", "SA", "IF", "Companie", "Asociație"]):
                    persoane_tip_counter["juridica"] += 1
                else:
                    persoane_tip_counter["fizica"] += 1

            # --- Adrese și Proprietăți ---
            adrese = res["adrese"]
            proprietati = res["proprietati"]

            num_adrese_counter[len(adrese)] += 1
            if len(adrese) == 0 or all(re.match(r"^\s*nr\.:.*sector\:.*$", a, re.IGNORECASE) for a in adrese):
                dosare_zero_adrese.append(nr_dosar)

            num_proprietati_per_dosar_counter[len(proprietati)] += 1
            if len(proprietati) == 0:
                dosare_zero_proprietati.append(nr_dosar)

            # Tip proprietate și tip adresa
            for adr in adrese:
                match_prop = re.search(r"\(([^)]+)\)$", adr)
                if match_prop:
                    tipuri_proprietati_counter[match_prop.group(1)] += 1

                adr_clean = adr.replace("Istoric:", "").strip()
                adr_clean = re.split(r",|\(|\)", adr_clean)[0].strip()
                adr_prefix = adr_clean.split()[0] if adr_clean else "gol"

                if "Istoric:" in adr:
                    tipuri_adrese_istorice_counter[adr_prefix] += 1
                else:
                    tipuri_adrese_contemporane_counter[adr_prefix] += 1

            # --- Progres ---
            if idx % 2000 == 0:
                print(f"Procesate {idx} fișiere din {len(html_files)}")

    # --- Creare raport JSON ---
    profil = {
        "dosare_anulate": dosare_anulate,
        "dosare_corecte": dosare_corecte,
        "numere_dosare_anulate": dosare_anulate_list,
        "numere_dosare_zero_solicitanti": dosare_zero_solicitanti,
        "numere_dosare_zero_adrese": dosare_zero_adrese,
        "numere_dosare_zero_proprietati": dosare_zero_proprietati,
        "persoane_fizice_vs_juridice": dict(persoane_tip_counter),
        "numar_solicitanti_per_dosar": dict(num_solicitanti_counter),
        "numar_adrese_per_dosar": dict(num_adrese_counter),
        "numar_proprietati_per_dosar": dict(num_proprietati_per_dosar_counter),
        "tipuri_proprietati_distincte": list(tipuri_proprietati_counter.keys()),
        "numar_tipuri_proprietati_distincte": len(tipuri_proprietati_counter),
        "numar_aparitii_per_tip_proprietate": dict(tipuri_proprietati_counter),
        "tipuri_adrese_istorice_distincte": list(tipuri_adrese_istorice_counter.keys()),
        "numar_tipuri_adrese_istorice_distincte": len(tipuri_adrese_istorice_counter),
        "numar_aparitii_per_tip_adresa_istorica": dict(tipuri_adrese_istorice_counter),
        "tipuri_adrese_contemporane_distincte": list(tipuri_adrese_contemporane_counter.keys()),
        "numar_tipuri_adrese_contemporane_distincte": len(tipuri_adrese_contemporane_counter),
        "numar_aparitii_per_tip_adresa_contemporana": dict(tipuri_adrese_contemporane_counter)
    }

    # Salvare raport JSON
    with open("profil_complet_multiproc.json", "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=4)

    print("Raport complet generat în 'profil_complet_multiproc.json'.")


if __name__ == "__main__":
    main()
