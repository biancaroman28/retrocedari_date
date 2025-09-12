from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, time

# Folder pentru salvare HTML
OUT_DIR = 'responses/'
os.makedirs(OUT_DIR, exist_ok=True)

# Setări Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless")  # NU folosi headless, vrem să vedem CAPTCHA
chrome_options.add_argument("--disable-gpu")

# Calea către ChromeDriver
driver_path = r"C:\Users\win10\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"

driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)

for i in range(1, 101):
    driver.get("https://www3.pmb.ro/l10")

    print(f"\n👉 Deschide CAPTCHA și rezolvă-l pentru dosarul {i}.")
    # Așteaptă până când input-ul devine vizibil (max 120 secunde)
    try:
        inp = WebDriverWait(driver, 120).until(
            EC.visibility_of_element_located((By.ID, "numar_dosar"))
        )
    except:
        print(f"❌ Input-ul pentru dosar {i} nu a apărut, sari peste acest dosar.")
        continue

    inp.clear()
    inp.send_keys(str(i))

    # Apasă butonul
    submit = driver.find_element(
        By.XPATH,
        "/html/body/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[1]/form/div/button"
    )
    submit.click()
    time.sleep(2)

    # Salvează HTML-ul
    html = driver.page_source
    with open(os.path.join(OUT_DIR, f"{i}.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML dosar {i} salvat.")

print("\nToate dosarele au fost procesate.")
input("Apasă Enter ca să închizi Chrome...")
driver.quit()
