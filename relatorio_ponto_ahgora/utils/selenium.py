
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
import os
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

class UtilsSelenium:

    def __init__(self, log, debug=False):
        self.driver = None
        self.log = log
        self.debug = debug


    def start_undetected_chrome(self, download_dir: str = None, headless: bool = False) -> uc.Chrome:
        """
        Inicia o Chrome com prefs de download para evitar diálogos e garantir
        que PDFs sejam baixados automaticamente no diretório escolhido.
        """
        if not download_dir:
            # se não for passado, cria uma pasta padrão em ~/Downloads/_selenium_downloads
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "_selenium_downloads")
        os.makedirs(download_dir, exist_ok=True)

        options = Options()
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "profile.default_content_settings.popups": 0,
            "plugins.always_open_pdf_externally": True, 
        }
        options.add_experimental_option("prefs", prefs)

        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        try:
            driver = uc.Chrome(options=options, headless=headless)
            self.log.success(f"Chrome iniciado com sucesso! Downloads em: {download_dir}")
        except Exception as e:
            self.log.error(f"Erro: {e}")
            self.log.info("Tentando com ChromeDriverManager...")
            try:
                driver = uc.Chrome(service=Service(ChromeDriverManager().install()), options=options, headless=headless)
                self.log.success("Chrome iniciado com ChromeDriverManager!")
            except Exception as e2:
                self.log.error(f"Erro novamente: {e2}")
                self.log.warning("SOLUÇÃO: Feche o Chrome completamente e execute novamente!")
                input("Pressione ENTER para tentar uma última vez...")
                driver = uc.Chrome(version_main=None, options=options, headless=headless)
                self.log.success("Chrome iniciado na última tentativa!")

        self.driver = driver
        return driver      

    def start_regular_chrome(self, download_dir: str = None, headless: bool = False) -> webdriver.Chrome:
        """
        Inicia Chrome (Selenium "normal") com prefs para baixar PDFs automaticamente
        no diretório indicado. Força o comportamento também em headless via CDP.
        """
        # 1) Diretório de download
        if not download_dir:
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "_selenium_downloads")
        os.makedirs(download_dir, exist_ok=True)

        # 2) Chrome Options + Prefs
        options = Options()
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "profile.default_content_settings.popups": 0,
            "plugins.always_open_pdf_externally": True,  # evita viewer interno (força download)
        }
        options.add_experimental_option("prefs", prefs)

        # flags úteis
        if headless:
            options.add_argument("--headless=new")  # headless moderno
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # 3) Sobe o driver
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            self.log.success(f"Chrome iniciado.")
        except Exception as e:
            self.log.error(f"Erro ao iniciar Chrome: {e}")
            raise

        # 4) Garante download permitido também em headless via CDP
        try:
            driver.execute_cdp_cmd(
                "Page.setDownloadBehavior",
                {
                    "behavior": "allow",
                    "downloadPath": download_dir,
                },
            )
        except Exception as e:
            # Alguns builds mais novos já respeitam as prefs; se der erro aqui, seguimos.
            self.log.warning(f"Não foi possível aplicar Page.setDownloadBehavior (CDP). Prosseguindo. Detalhe: {e}")

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
            element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            element.click()
            element.clear()
            element.send_keys(keys)
            if self.debug:
                self.log.debug(f"Texto enviado para o elemento: {value}")
            return element
        except Exception as e:
            self.log.error(f"Falha ao preencher campo: {(getattr(e,'msg',None) or str(e)).splitlines()[0]}")
            return None

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

    def wait_until_alert_is_present(self, driver, timeout=10):
        
        WebDriverWait(driver, timeout).until(EC.alert_is_present())

        alert = driver.switch_to.alert

        while True:
            try:
                _ = alert.text  
                sleep(1)
            except:
                break

    def hover_over_element(self, by, value, timeout=10, delay=0):
        sleep(delay)
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            actions = ActionChains(self.driver)
            actions.move_to_element(element).perform()
            if self.debug:
                self.log.debug(f"Hover realizado no elemento: {value}")
        except Exception as e:
            self.log.error(f"Falha ao realizar hover: {e}")

    def wait_and_find(self, by, value, timeout=10, delay=0):
        sleep(delay)
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            if self.debug:
                self.log.debug(f"Elemento encontrado: {value}")
            return element
        except Exception as e:
            self.log.error(f"Falha ao encontrar elemento: {e}")
            return None