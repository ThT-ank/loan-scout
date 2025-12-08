"""Selenium-based Boursobank simulator collector."""

import time
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options


@dataclass
class Borrower:
    """Typed container for borrower inputs."""

    # pylint: disable=too-few-public-methods
    age: str
    income: str
    expenses: str


@dataclass
class SimulationInputs:
    """Typed container for simulator input values."""

    # pylint: disable=too-few-public-methods
    borrower1: Borrower
    borrower2: Borrower
    loan_amount: str
    down_payment: str
    notary_fees: str

    @classmethod
    def default_values(cls) -> "SimulationInputs":
        """Return sensible defaults for a quick simulation run."""
        return cls(
            borrower1=Borrower(age="24", income="2800", expenses="0"),
            borrower2=Borrower(age="25", income="2800", expenses="0"),
            loan_amount="300000",
            down_payment="22500",
            notary_fees="22500",
        )


BANK_NAME = "Boursobank"  # label returned by the API
URL = (
    "https://www.boursobank.com/credit/credit-immobilier"
    "?origine=2247&at_medium=sl&at_campaign=fr_sea&at_platform=google"
    "&at_term=&at_creation=ppi&at_variant=filrouge&origine=2247"
    "&at_medium=sl&at_campaign=fr_sea&at_platform=google&at_term="
    "&at_creation=ppi&at_variant=filrouge&gad_source=1#simulateur"
)


class BoursoBankSimulator:
    """Drive Boursobank simulator via Selenium."""

    # pylint: disable=too-few-public-methods
    def __init__(self, input_data: SimulationInputs | None = None):
        self.bank_name = BANK_NAME
        self.input_data = input_data or SimulationInputs.default_values()
        self.driver: WebDriver
        self._init_driver()

    def _init_driver(self):
        """Configure headless Chrome driver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=chrome_options)

    def _click_radio_button(self, name: str, index: int):
        """Click a radio button by name and index."""
        radio_buttons = self.driver.find_elements(By.NAME, name)
        self.driver.execute_script("arguments[0].click();", radio_buttons[index])

    def _select_dropdown_option(self, dropdown_index: int, option_text: str):
        """Select dropdown option by visible text."""
        wait = WebDriverWait(self.driver, 10)
        dropdown_containers = self.driver.find_elements(By.CLASS_NAME, "c-select__combobox")
        dropdown_container = dropdown_containers[dropdown_index]
        dropdown_container.click()
        options = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "c-select__option"))
        )
        for option in options:
            if option.text == option_text:
                option.click()
                break

    def _click_next_step(self, label: str = "Étape suivante", timeout: int = 10):
        """Click the next-step button by its label."""
        xpath = (
            f"//a[normalize-space(text())='{label}'] | "
            f"//button[normalize-space(text())='{label}']"
        )
        element = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        time.sleep(0.2)
        element.click()
        time.sleep(0.2)

    def _fill_form(self):
        """Fill the loan form with provided inputs."""
        input_mapping = {
            "text-input-0": self.input_data.borrower1.age,
            "text-input-1": self.input_data.borrower1.income,
            "text-input-2": self.input_data.borrower1.expenses,
            "text-input-3": self.input_data.borrower2.age,
            "text-input-4": self.input_data.borrower2.income,
            "text-input-5": self.input_data.borrower2.expenses,
            "text-input-6": self.input_data.loan_amount,
            "text-input-7": self.input_data.down_payment,
            "text-input-9": self.input_data.notary_fees,
        }

        # Fill the first six fields (borrowers)
        for input_id, value in list(input_mapping.items())[:6]:
            field = self.driver.find_element(By.ID, input_id)
            field.send_keys(value)

        self._click_radio_button("isEmployee", 0)
        self._click_radio_button("isEmployee", 2)
        self._click_next_step()
        self._click_radio_button("isVefa", 1)
        self._click_next_step()
        self._click_radio_button("residenceType", 0)
        self._click_next_step()

        # Fill the last three fields (loan & fees)
        for input_id, value in list(input_mapping.items())[-3:]:
            field = self.driver.find_element(By.ID, input_id)
            field.send_keys(value)

    def run_simulation(self, loan_duration: str) -> dict[str, str]:
        """Run the Boursobank loan simulation for a given duration."""
        t0 = time.perf_counter()

        try:
            self.driver.get(URL)

            # Click initial buttons
            for button_label in ["Vos mensualités", "À deux"]:
                button = self.driver.find_element(By.XPATH, f"//span[text()='{button_label}']")
                button.click()

            self._click_next_step()
            self._fill_form()

            # Select duration and energy rating
            self._select_dropdown_option(0, loan_duration)
            self._select_dropdown_option(1, "B")
            self._click_next_step()

            # Retrieve results
            self.driver.implicitly_wait(10)
            card = self.driver.find_element(By.CLASS_NAME, "simulation-card")
            result_text = self.driver.execute_script("return arguments[0].innerText;", card)

            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            return {
                "bank": self.bank_name,
                "raw_result": result_text,
                "notes": f"scraped in {elapsed_ms}ms",
            }

        finally:
            self.driver.quit()


def process_boursobank_simulation(loan_duration: str) -> str:
    """Backward-compatible helper to get raw result text."""
    simulator = BoursoBankSimulator()
    result = simulator.run_simulation(loan_duration)
    return result["raw_result"]


# Backward compatibility alias
process_BoursoBank_simulation = process_boursobank_simulation  # pylint: disable=invalid-name
