
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class UtilsSelenium:

    def __init__(self, log, debug=False):
        self.driver = None
        self.log = log
        self.debug = debug

    def start_undetected_chrome(self) -> uc.Chrome:
        try:
            driver = uc.Chrome()
            self.log.success("Chrome iniciado com sucesso!")
        except Exception as e:
            self.log.error(f"Erro: {e}")
            self.log.info("Tentando com configurações alternativas...")
            try:
                driver = uc.Chrome(service=Service(ChromeDriverManager().install()))
                self.log.success("Chrome iniciado com ChromeDriverManager!")
            except Exception as e2:
                self.log.error(f"Erro novamente: {e2}")
                self.log.warning("SOLUÇÃO: Feche o Chrome completamente e execute novamente!")
                input("Pressione ENTER para tentar uma última vez...")
                driver = uc.Chrome(version_main=None)
                self.log.success("Chrome iniciado na última tentativa!")
        self.driver = driver
        return driver

    def wait_and_click(self, by, value, timeout=10, delay=0):
        sleep(delay)
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
            element.click()
            if self.debug:
                self.log.debug(f"Clique realizado no elemento: {value}")
        except Exception as e:
            self.log.error(f"Falha ao clicar: {e}")
            self.log.info("Tentando clicar via JavaScript...")
            self.driver.execute_script("arguments[0].click();", element)
            if self.debug:
                self.log.debug(f"Clique realizado no elemento via JavaScript: {value}")

    def wait_and_send_keys(self, by, value, keys, timeout=10, delay=0):
        sleep(delay)
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((by, value)))
            element.clear()
            element.send_keys(keys)
            if self.debug:
                self.log.debug(f"Texto enviado para o elemento: {value}")
            return element
        except Exception as e:
            self.log.error(f"Falha ao preencher campo: {e}")


    def wait_for_element(self, by, value, timeout=10, delay=0):
        sleep(delay)
        try:
            if self.debug:
                self.log.debug(f"Aguardando elemento: {value}")
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
        except Exception as e:
            self.log.error(f"Elemento não encontrado: {e}")
            return None


    def scroll_to_element(self, by, value, timeout=10, delay=0):
        sleep(delay)
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            if self.debug:
                self.log.debug(f"Rolagem até o elemento: {value}")
        except Exception as e:
            self.log.error(f"Falha ao rolar até o elemento: {e}")


    def wait_and_select_by_value(self, by, value, option_value, timeout=10, delay=0):
        sleep(delay)
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
            select = Select(element)
            select.select_by_value(option_value)
            if self.debug:
                self.log.debug(f"Valor '{option_value}' selecionado no elemento: {value}")
        except Exception as e:
            self.log.error(f"Falha ao selecionar valor '{option_value}': {e}")


    def wait_and_select_by_visible_text(self, by, value, visible_text, timeout=10, delay=0):
        sleep(delay)
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
            select = Select(element)
            select.select_by_visible_text(visible_text)
            if self.debug:
                self.log.debug(f"Texto '{visible_text}' selecionado no elemento: {value}")
        except Exception as e:
            self.log.error(f"Falha ao selecionar texto '{visible_text}': {e}")

    def select_ng_option_by_text(self, dropdown_by, dropdown_value, option_text, timeout=10, delay=0):
        sleep(delay)
        try:
            # Clica no dropdown para abrir as opções
            dropdown = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((dropdown_by, dropdown_value)))
            dropdown.click()
            if self.debug:
                self.log.debug(f"Abrindo dropdown: {dropdown_value}")
            # Espera a opção com o texto desejado aparecer e clica nela
            option_xpath = f"//div[contains(@class, 'ng-option')]//span[text()='{option_text}']"
            option = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
            option.click()
            if self.debug:
                self.log.debug(f"Opção '{option_text}' selecionada no dropdown: {dropdown_value}")
        except Exception as e:
            self.log.error(f"Erro ao selecionar '{option_text}' no dropdown: {e}")