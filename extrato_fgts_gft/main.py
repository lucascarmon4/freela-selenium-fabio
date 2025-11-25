#%%
import base64
from datetime import datetime
start_time = datetime.now()
from time import sleep
from tkinter import filedialog
from selenium.webdriver.common.by import By
import pandas as pd
from config.config import PRODUTO, load_config, save_origem
from config.license_checker import check_license
from utils.core import Utils
from db.db import SQLServerHelper
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.print_page_options import PrintOptions
import sys

config = load_config()
utils = Utils(debug=False)
log = utils.log
service = utils.service

db=SQLServerHelper(config)
db.connect()

# Verificação da licença
ok_license, machine_guid = check_license(db, config['cliente'])
if not ok_license:
    input("Pressione Enter para sair...")
    sys.exit(1)

log.warning("Por favor, selecione o arquivo Excel com os CPFs dos funcionários.")

if not os.path.isdir(config['origem']):
    log.error("A origem configurada no arquivo 'config.ini' não é um diretório válido. Encerrando o programa.")
    input("Pressione Enter para sair...")
    sys.exit(1)

file_path = filedialog.askopenfilename(
    initialdir=config["origem"],
    title="Selecione o arquivo Excel"
)
save_origem(os.path.dirname(file_path))

if not file_path:
    log.error("Nenhum arquivo selecionado. Encerrando o programa.")
    input("Pressione Enter para sair...")
    sys.exit(1)

file = pd.read_excel(file_path)

if file.empty:
    log.error("O arquivo está vazio. Encerrando o programa.")
    input("Pressione Enter para sair...")
    sys.exit(1)

log.info("Inicializando Chrome...")

us = utils.selenium

driver = us.start_regular_chrome()
driver.maximize_window()
driver.get(config["url"])

us.wait_and_click(By.ID, "btnEmpregador")
log.warning("Por favor, entre com o certificado digital.")

us.wait_and_select_by_visible_text(By.NAME, "sltOpcao", "Acessar Empresa Outorgante", delay=2, timeout=15)
us.wait_and_send_keys(By.NAME , "txtCNPJ", config["cnpj_outorgante"], delay=1)

us.wait_and_click(By.CSS_SELECTOR, 'a[href="Javascript:subm_verificar_empresa()"]')

us.wait_and_select_by_visible_text(By.NAME, "sltOpcao", "Solicitar Extrato do Trabalhador", delay=1)
wait = WebDriverWait(driver, 10)
first_tab = driver.current_window_handle
#matricula(primeira coluna)- EXTRATO FGTS
opts = PrintOptions()
opts.background = True
opts.orientation = "portrait" 
file = file.dropna(subset=["PIS"])
contador = 0
for index, row in file.iterrows():
    pis = str(row["PIS"]).replace("-", "")
    if service.already_processed("1", pis):
        log.warning(f"PIS {pis} já processado. Pulando...")
        continue
    contador += 1
    us.wait_and_select_by_visible_text(By.NAME, "sltRegiao", config["base_conta"])
    matricula = row[0]
    us.wait_and_send_keys(By.NAME, "txtNumPisPasep", pis)
    us.wait_and_click(By.CSS_SELECTOR, "a[href='javascript:subm_localizar_trabalhador();']", delay=1)

    us.wait_and_click(By.CSS_SELECTOR, "a[href='javascript:impr_solicitar_extrato_fgts();']", delay=1)
    wait.until(EC.number_of_windows_to_be(2))

    for window_handle in driver.window_handles:
        if window_handle != first_tab:
            driver.switch_to.window(window_handle)
            break
    
    pdf_b64 = driver.print_page(opts)
    os.makedirs(config["saida"], exist_ok=True)
    file_path = os.path.join(config["saida"], f"{matricula}- EXTRATO FGTS.pdf")
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(pdf_b64))
    
    driver.close()
    driver.switch_to.window(first_tab)

    us.wait_and_click(By.CSS_SELECTOR, "a[href='javascript:retr_solicitar_extrato_fgts();']", delay=1)
    service.mark_as_processed("1", pis)

# etapa 2
df_step_2 = file[file.apply(lambda row: service.mais_de_um_ano(row["ADM"], row["DEM"]), axis=1)]
if len(df_step_2) > 0: 
    us.wait_and_select_by_visible_text(By.NAME, "sltOpcao", "Solicitar Extrato para Fins Recisórios", delay=2)
    us.wait_and_select_by_visible_text(By.NAME, "sltRegiao", config["base_conta"])
    should_click = False
    for index, row in df_step_2.iterrows():
        pis = str(row["PIS"]).replace("-", "")
        if service.already_processed("2", pis):
            log.warning(f"PIS {pis} já processado. Pulando...")
            continue
        contador += 1
        us.wait_and_send_keys(By.NAME, "txtPIS", pis)
        us.wait_and_click(By.ID, "adicionar")
        service.mark_as_processed("2", pis)
        should_click = True
        sleep(2)
    if should_click:
        us.wait_and_click(By.CSS_SELECTOR, "a[href='javascript:subm_extrato_fins_rescisorios();']", delay=1)

# etapa 3
df_step_3 = file[file.apply(
    lambda row: service.tem_dispensa_no_motivo_e_trabalhou_por_mais_de_6_meses(
        row["ADM"], 
        row["DEM"], 
        row["Motivo"]
    ), 
    axis=1)
]
if len(df_step_3) > 0: 
    us.wait_and_select_by_visible_text(By.NAME, "sltOpcao", "Solicitar Extrato Analítico do Trabalhador", delay=2)
    for index, row in df_step_3.iterrows():
        pis = str(row["PIS"]).replace("-", "")
        if service.already_processed("3", pis):
            log.warning(f"PIS {pis} já processado. Pulando...")
            continue
        contador += 1 
        us.wait_and_select_by_visible_text(By.NAME, "sltRegiao", config["base_conta"])
        us.wait_and_send_keys(By.NAME, "txtPIS", pis)
        us.wait_and_click(By.CSS_SELECTOR, "a[href='javascript:subm_extrato_analitico_trabalhador();']", delay=1)
        us.wait_and_click(By.CSS_SELECTOR, "a[href='javascript:retr_extrato_analitico_trabalhador_comprovante();']", delay=1)
        service.mark_as_processed("3", pis)

end_time = datetime.now()

insert_statistics = """
    INSERT INTO processados
    (machine_guid, data_inicio, data_termino, total_processos, produto, cliente)
    VALUES (?, ?, ?, ?, ?, ?)
"""

db.execute(insert_statistics, [machine_guid, start_time, end_time, contador, PRODUTO, config["cliente"]])
log.success("Estatísticas do processamento salvas com sucesso.")

db.close()
driver.quit()
input("Processo concluído. Pressione Enter para sair...")
# %%
