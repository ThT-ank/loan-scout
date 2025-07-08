from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

input_data = {
    "text-input-0": "24",
    "text-input-1": "2800",
    "text-input-2": "0",
    "text-input-3": "25",
    "text-input-4": "2800",
    "text-input-5": "0",
    "text-input-6": "300000",
    "text-input-7": "22500",
    "text-input-9": "22500"
}

def click_radio_button(driver, name, index):
    radio_buttons = driver.find_elements(By.NAME, name)
    driver.execute_script("arguments[0].click();", radio_buttons[index])

def select_dropdown_option(driver, dropdown_index, option_text):
    wait = WebDriverWait(driver, 10)
    dropdown_containers = driver.find_elements(By.CLASS_NAME, 'c-select__combobox')
    dropdown_container = dropdown_containers[dropdown_index]
    dropdown_container.click()
    options = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'c-select__option')))
    for option in options:
        if option.text == option_text:
            option.click()
            break

def click_next_step(driver, texte="Étape suivante", timeout=10):
    """
    Clique sur le premier <a> ou <button> dont le texte correspond à 'texte'.
    """
    xpath = (
        f"//a[normalize-space(text())='{texte}'] | "
        f"//button[normalize-space(text())='{texte}']"
    )
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    element.click()

def process_BoursoBank_simulation(loanDuration):

    # Configurer les options pour Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode sans tête
    chrome_options.add_argument("--log-level=3")  # Réduit les logs Chrome

    chrome_options.add_argument("--no-sandbox")  # Nécessaire dans Docker
    chrome_options.add_argument("--disable-gpu")  # Option pour éviter certains bugs graphiques

    ## Créer une instance de navigateur
    driver = webdriver.Chrome(options=chrome_options)

    # URL cible
    url = "https://www.boursobank.com/credit/credit-immobilier?origine=2247&at_medium=sl&at_campaign=fr_sea&at_platform=google&at_term=&at_creation=ppi&at_variant=filrouge&origine=2247&at_medium=sl&at_campaign=fr_sea&at_platform=google&at_term=&at_creation=ppi&at_variant=filrouge&gad_source=1&gclid=Cj0KCQiA4fi7BhC5ARIsAEV1YiacKJ_nRth0h6cpsAtw750ZW6IqhC9Vc2BaarwT32sKlQfEapKXS8EaAoEsEALw_wcB#simulateur"

    # Ouvrir la page avec Selenium
    driver.get(url)

    # Cliquer sur les boutons initiaux
    boutons_a_cliquer = ["Vos mensualités", "À deux"]
    for texte_bouton in boutons_a_cliquer:
        bouton = driver.find_element(By.XPATH, f"//span[text()='{texte_bouton}']")
        bouton.click()
        time.sleep(0.2)

    click_next_step(driver)

    # Remplir les champs
    for input_id, value in list(input_data.items())[:6]:  # Sélection des 3 premiers éléments
        champ_texte = driver.find_element(By.ID, input_id)
        champ_texte.send_keys(value)

    click_radio_button(driver, "isEmployee", 0)
    click_radio_button(driver, "isEmployee", 2)
    click_next_step(driver)
    click_radio_button(driver, "isVefa", 1)
    click_next_step(driver)
    click_radio_button(driver, "residenceType", 0)
    click_next_step(driver)

    # Remplir les champs
    for input_id, value in list(input_data.items())[-3:]:  # Sélection des 3 derniers éléments
        champ_texte = driver.find_element(By.ID, input_id)
        champ_texte.send_keys(value)

    # Sélectionner la durée du prêt et le DPE
    select_dropdown_option(driver, 0, f"{loanDuration}")
    select_dropdown_option(driver, 1, "B")

    # Dernier bouton pour valider
    click_next_step(driver)

    # Attendre le résultat et récupérer les données
    driver.implicitly_wait(10)
    rounded_card = driver.find_element(By.CLASS_NAME, "simulation-card")
    card_text = driver.execute_script("return arguments[0].innerText;", rounded_card)

    driver.quit()
    

    return card_text