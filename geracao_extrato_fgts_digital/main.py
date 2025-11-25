#%%
from datetime import datetime
start_time = datetime.now()

from time import sleep
from tkinter import filedialog
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from config.config import load_config, save_origem
from config.license_checker import check_license
from utils.core import Utils
from db.db import SQLServerHelper
import os
import sys

config = load_config()
utils = Utils()
log = utils.log
service = utils.service

db=SQLServerHelper(config)
db.connect()

company_name, company_cnpj = service.choose_company(db, config)

# Verificação da licença
ok_license, mac = check_license(db)
if not ok_license:
    sys.exit(1)

log.warning("Por favor, selecione o arquivo Excel com os CPFs dos funcionários.")

file_path = filedialog.askopenfilename(
    initialdir=config["origem"],
    title="Selecione o arquivo Excel"
)
save_origem(os.path.dirname(file_path))
if not file_path:
    log.error("Nenhum arquivo selecionado. Encerrando o programa.")
    sys.exit(1)

file = pd.read_excel(file_path)
if file.empty:
    log.error("O arquivo está vazio. Encerrando o programa.")
    sys.exit(1)

if not (utils.file.verify_required_columns(file, ['CPF', 'Data De Deslig']) and utils.file.verify_file_extension(file_path, ['.xlsx'])):
    sys.exit(1)

log.info("Inicializando Chrome...")
log.warning("Se der erro, feche TODAS as janelas do Chrome e tente novamente!")

us = utils.selenium

driver = us.start_undetected_chrome()

driver.maximize_window()

driver.get(config['url_fgts_digital'])

us.wait_and_click(By.CLASS_NAME, "entrar", delay=2)

log.warning("Por favor, entre com o certificado digital.")

sleep(12)

us.select_ng_option_by_text(
    dropdown_by=By.CSS_SELECTOR,
    dropdown_value=".ng-select-container",
    option_text="Procurador",
    timeout=300
)

us.wait_and_send_keys(
    by=By.CSS_SELECTOR,
    value='input[placeholder="Informe CNPJ ou CPF"]',
    keys=company_cnpj,
    delay=1
) # CNPJ da empresa

us.wait_and_click(
    by=By.XPATH,
    value='//button[contains(text(), "Definir")]',
    delay=1
) # Botão Definir

us.wait_and_click(
    by=By.XPATH,
    value='//img[@alt="image" and contains(@src, "icone-ficha.png")]',
    delay=2
) # REMUNERAÇÃO PARA FINS RESCISÓRIOS

us.wait_and_click(
    by=By.XPATH,
    value="//div[contains(@class, 'cardListItem')]//span[text()[contains(., 'Gestão de Histórico de Remunerações')]]/..",
) # Gestão de Histórico de Remunerações

wait = WebDriverWait(driver, 10)
cont = 0

formated_date = datetime.today().strftime('%Y%m%d_%H%M')

for index, row in file.iterrows():

    cpf = str(int(row['CPF'])).replace(".", "").replace("-", "").zfill(11)

    if service.cpf_already_processed(cpf):
        log.warning(f"CPF {cpf} já processado. Pulando...")
        continue        

    log.info(f"Processando CPF: {cpf} ({index+1}/{len(file)})")
    
    us.wait_and_send_keys(
        by=By.CSS_SELECTOR,
        value='input.brx-input[maxlength="14"]',
        keys=cpf
    ) # CPF do funcionário

    periodo_desligamento = f"01/{row['Data De Deslig'].month:02d}/{row['Data De Deslig'].year}"

    us.scroll_to_element(
        By.CSS_SELECTOR,
        value='input.brx-input[maxlength="10"]'
    )

    us.wait_and_send_keys(
        by=By.CSS_SELECTOR,
        value='input.brx-input[maxlength="10"]',
        keys=periodo_desligamento
    ) # Período de desligamento
    
    us.wait_and_click(
        by=By.XPATH,
        value='//button[contains(@class, "br-button") and contains(text(), "Pesquisar")]',
        delay=1
    ) # Botão Pesquisar

    cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    sleep(2)

    try: 
        wait.until(
        lambda d: d.find_elements(By.XPATH, f'//datatable-body-cell//span[text()="{cpf_formatado}"]') or
                  d.find_elements(By.XPATH, '//div[contains(@class, "br-message") and contains(.,"Nenhum registro encontrado")]')
        )
        if driver.find_elements(By.XPATH, '//div[contains(@class, "br-message") and contains(.,"Nenhum registro encontrado")]'):
            log.error(f"Nenhuma linha encontrada para o CPF {cpf_formatado}. Pulando funcionário...")
            continue
    except Exception as e: 
        log.error(f"Erro ao buscar linha para o CPF {cpf_formatado}: {e}")
        continue

    log.success("Encontrou " + cpf_formatado)

    us.wait_and_click(
        by=By.XPATH,
        value=f'//span[text()="{cpf_formatado}"]/ancestor::datatable-body-row//button[@title="Visualizar"]',
        delay=1
    ) # Botão Visualizar 

    us.wait_and_click(
        by=By.XPATH,
        value='//button[@title="Baixar resultado da pesquisa em pdf"]',
        delay=1
    ) # Botão Baixar em PDF

    sleep(1) # Se precisar, aumentar aqui

    utils.file.wait_for_downloads()
    utils.file.rename_and_move_downloaded_file(
        new_name=f"EXTRATO - {row['Nome']}.pdf",
        target_path=f"{config['saida']}/{formated_date}_{company_name}_EXTRATO-FGTS"
    )
    service.mark_as_processed(cpf)
    cont += 1
    
    # Voltar à página de pesquisa.
    driver.back()
    sleep(1)
    log.success(f"Extrato do FGTS para o CPF {cpf_formatado} gerado com sucesso.")

end_time = datetime.now()

log.success("Todos os extratos do FGTS da planilha foram gerados com sucesso.")

insert_statistics = """
    INSERT INTO processados
    (mac_address, data_inicio, data_termino, total_processos, produto, cliente)
    VALUES (?, ?, ?, ?, ?, ?)
"""

produto = "extrato_fgts"    

db.execute(insert_statistics, [mac, start_time, end_time, cont, produto, config["cliente"]])
log.success("Estatísticas do processamento salvas com sucesso.")

db.close()
driver.quit()

sleep(60)
# %%