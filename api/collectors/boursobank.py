import time
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options


@dataclass
class SimulationInputs:
    emprunteur1_age: str
    emprunteur1_revenu: str
    emprunteur1_charges: str
    emprunteur2_age: str
    emprunteur2_revenu: str
    emprunteur2_charges: str
    montant_emprunt: str
    apport: str
    frais_notaire: str

    @classmethod
    def default_values(cls) -> "SimulationInputs":
        return cls(
            emprunteur1_age="24",
            emprunteur1_revenu="2800",
            emprunteur1_charges="0",
            emprunteur2_age="25",
            emprunteur2_revenu="2800",
            emprunteur2_charges="0",
            montant_emprunt="300000",
            apport="22500",
            frais_notaire="22500"
        )


BANK_NAME = "Boursobank"  # libellé affiché côté API
URL = (
    "https://www.boursobank.com/credit/credit-immobilier"
    "?origine=2247&at_medium=sl&at_campaign=fr_sea&at_platform=google&at_term="
    "&at_creation=ppi&at_variant=filrouge&origine=2247&at_medium=sl"
    "&at_campaign=fr_sea&at_platform=google&at_term=&at_creation=ppi"
    "&at_variant=filrouge&gad_source=1&gclid=Cj0KCQiA4fi7BhC5ARIsAEV1YiacKJ_n"
    "Rth0h6cpsAtw750ZW6IqhC9Vc2BaarwT32sKlQfEapKXS8EaAoEsEALw_wcB#simulateur"
)


class BoursoBankSimulator:
    def __init__(self, input_data: SimulationInputs | None = None):
        self.bank_name = BANK_NAME
        self.input_data = input_data or SimulationInputs.default_values()
        self.driver: WebDriver
        self._init_driver()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=chrome_options)

    def _click_radio_button(self, name: str, index: int):
        radio_buttons = self.driver.find_elements(By.NAME, name)
        self.driver.execute_script("arguments[0].click();", radio_buttons[index])

    def _select_dropdown_option(self, dropdown_index: int, option_text: str):
        wait = WebDriverWait(self.driver, 10)
        dropdown_containers = self.driver.find_elements(By.CLASS_NAME, 'c-select__combobox')
        dropdown_container = dropdown_containers[dropdown_index]
        dropdown_container.click()
        options = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'c-select__option')))
        for option in options:
            if option.text == option_text:
                option.click()
                break

    def _click_next_step(self, texte: str = "Étape suivante", timeout: int = 10):
        xpath = (
            f"//a[normalize-space(text())='{texte}'] | "
            f"//button[normalize-space(text())='{texte}']"
        )
        element = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        time.sleep(0.2)
        element.click()
        time.sleep(0.2)

    def _fill_form(self):
        # Remplir les informations de l'emprunteur 1
        input_mapping = {
            "text-input-0": self.input_data.emprunteur1_age,
            "text-input-1": self.input_data.emprunteur1_revenu,
            "text-input-2": self.input_data.emprunteur1_charges,
            "text-input-3": self.input_data.emprunteur2_age,
            "text-input-4": self.input_data.emprunteur2_revenu,
            "text-input-5": self.input_data.emprunteur2_charges,
            "text-input-6": self.input_data.montant_emprunt,
            "text-input-7": self.input_data.apport,
            "text-input-9": self.input_data.frais_notaire
        }

        # Remplir les 6 premiers champs
        for input_id, value in list(input_mapping.items())[:6]:
            champ_texte = self.driver.find_element(By.ID, input_id)
            champ_texte.send_keys(value)

        self._click_radio_button("isEmployee", 0)
        self._click_radio_button("isEmployee", 2)
        self._click_next_step()
        self._click_radio_button("isVefa", 1)
        self._click_next_step()
        self._click_radio_button("residenceType", 0)
        self._click_next_step()

        # Remplir les 3 derniers champs
        for input_id, value in list(input_mapping.items())[-3:]:
            champ_texte = self.driver.find_element(By.ID, input_id)
            champ_texte.send_keys(value)

    def run_simulation(self, loan_duration: str) -> dict[str, str]:
        """
        Lance une simulation de crédit immobilier sur le site de BoursoBank.

        Args:
            loan_duration (str): La durée du prêt (ex: "20 ans")

        Returns:
            dict: Résultat normalisé de la simulation
        """
        t0 = time.perf_counter()

        try:
            self.driver.get(URL)

            # Cliquer sur les boutons initiaux
            for texte_bouton in ["Vos mensualités", "À deux"]:
                bouton = self.driver.find_element(By.XPATH, f"//span[text()='{texte_bouton}']")
                bouton.click()

            self._click_next_step()
            self._fill_form()

            # Sélectionner la durée et le DPE
            self._select_dropdown_option(0, loan_duration)
            self._select_dropdown_option(1, "B")
            self._click_next_step()

            # Récupérer les résultats
            self.driver.implicitly_wait(10)
            card = self.driver.find_element(By.CLASS_NAME, "simulation-card")
            result_text = self.driver.execute_script("return arguments[0].innerText;", card)

            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            return {
                "bank": self.bank_name,
                "raw_result": result_text,
                "notes": f"scraped in {elapsed_ms}ms"
            }

        finally:
            self.driver.quit()


# Fonction de compatibilité pour l'ancien nom
def process_BoursoBank_simulation(loan_duration: str) -> str:
    simulator = BoursoBankSimulator()
    result = simulator.run_simulation(loan_duration)
    return result["raw_result"]
