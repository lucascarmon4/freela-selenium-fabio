#%%
from datetime import datetime
start_time = datetime.now()
from time import sleep
from tkinter import filedialog
from selenium.webdriver.common.by import By
import pandas as pd
from config.config import load_config, save_origem
from config.license_checker import check_license
from utils.core import Utils
from db.db import SQLServerHelper
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sys

config = load_config()
utils = Utils(debug=False)
log = utils.log
service = utils.service

db=SQLServerHelper(config)
db.connect()

company_name, _ = service.choose_company(db, config)

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

if not (utils.file.verify_required_columns(file, ['CPF']) and utils.file.verify_file_extension(file_path, ['.xlsx'])):
    log.error("O arquivo selecionado não possui as colunas necessárias ou a extensão é inválida. Encerrando o programa.")
    input("Pressione Enter para sair...")
    sys.exit(1)

log.info("Inicializando Chrome...")

us = utils.selenium

driver = us.start_regular_chrome()
driver.maximize_window()

email = config['usuario_ahgora']
url, password = service.get_url_and_password(db, config['cliente'], email)

driver.get(url)

us.wait_and_send_keys(By.ID, "email", email, delay=1)

xpath_entrar = "//button[contains(@class,'MuiButton-root') and contains(., 'Entrar')]"

us.wait_and_click(
    By.XPATH, 
    xpath_entrar, 
    delay=1
) # Botão Entrar

us.wait_and_send_keys(By.ID, "password", password)

us.wait_and_click(
    By.XPATH, 
    xpath_entrar, 
    delay=1
) # Botão Entrar

us.wait_and_find(By.ID, "code")

alert_text = "Por favor, digite o código que foi enviado para o seu e-mail."
driver.execute_script(f"alert('{alert_text}');")
us.wait_until_alert_is_present(driver)

sleep(1)

i = 0
while i < 20:
    try:
        driver.find_element(By.XPATH, xpath_entrar)
        sleep(1)
        i+=1
        if i == 20:
            us.wait_and_click(By.XPATH, xpath_entrar)
    except:
        break
        
cliente = config['cliente'].strip().upper()

XPATH_ITEM = (
    "//div[@role='button' and contains(@class,'MuiListItemButton-root')]"
    "[.//span[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '%s')]]"
) % cliente

us.wait_and_click(By.XPATH, XPATH_ITEM)

sleep(2)
WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
sleep(1)
driver.get("https://app.ahgora.com.br/batidas/apuracao")


new_file_data = []
contador = 0

formated_date = datetime.today().strftime('%Y%m%d_%H%M')

for index, row in file.iterrows():

    cpf = str(row['CPF']).zfill(11)
    cpf_mask = service.get_cpf_mask(cpf)

    if service.cpf_already_processed(cpf):
        log.warning(f"CPF {cpf_mask} já processado. Pulando...")
        continue

    data_desligamento = row['Data De Deslig']

    mes_desligamento = data_desligamento.month
    ano_desligamento = data_desligamento.year

    
    log.info(f"Processando CPF: {cpf_mask}")
    us.wait_and_send_keys(By.ID, "matricula", cpf_mask, timeout=20)    

    XPATH_CARD = (
        "//a[contains(@class,'fjs_item')]"
        "[.//div[contains(@class,'cpfElement')]//span[contains(normalize-space(.), '%s')]]"
    ) % cpf_mask

    wait_time = 2
    try:
        WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, XPATH_CARD)))
        us.wait_and_click(By.XPATH, XPATH_CARD, timeout=6, delay=0)
    except TimeoutException:
        log.warning(f"CPF {cpf_mask}: nenhum card encontrado em {wait_time}s — continuando para o próximo.")
        continue
    except Exception as e:
        log.warning(f"CPF {cpf_mask}: falha ao clicar ({e}) — continuando para o próximo.")
        continue

    us.wait_and_select_by_value(By.ID, "monthsSess", str(mes_desligamento), delay=1)
    us.wait_and_select_by_value(By.ID, "yearsSess", str(ano_desligamento), delay=1)

    matricula_input = us.wait_and_find(By.ID, "matricula")
    while matricula_input.get_attribute("value").strip().upper() != str(row['Nome']).strip().upper():
        sleep(1)
        matricula_input = us.wait_and_find(By.ID, "matricula")

    checkbox_bloquear = us.wait_and_find(By.ID, "reckonBlockEmployee")
    divs_checkbox_bloquear = checkbox_bloquear.find_elements(By.TAG_NAME, 'div')
    
    if divs_checkbox_bloquear[0].text.strip() == "DESBLOQUEAR COMPETÊNCIA": 
        is_checked = True
    else:
        is_checked = False

    saldo_atual = us.wait_and_find(By.ID, "SALDO ATUAL").text

    status = "CONCLUIDO"

    if saldo_atual != "00:00": 
        status = "SALDO DO MÊS DE DESLIGAMENTO DIFERENTE DE 00:00"

    if not is_checked: 
        status = "COMPETÊNCIA DO MÊS DE DESLIGAMENTO ESTÁ ABERTA"

    new_file_data.append({
        "MATRICULA": row['Matrícula'],
        "NOME": row['Nome'],
        "CPF": cpf,
        "STATUS": status
    })

    if status != "CONCLUIDO":
        continue

    us.wait_and_click(By.XPATH, "//button[contains(@class,'espelho')][contains(normalize-space(.),'Múltiplos Meses')]")

    if data_desligamento.month == 1:
        mes_anterior = 12
        ano_anterior = data_desligamento.year - 1
    else:
        mes_anterior = data_desligamento.month - 1
        ano_anterior = data_desligamento.year

    us.wait_and_select_by_value(By.ID, "mesInicio", str(mes_anterior), delay=1)
    us.wait_and_send_keys(By.ID, "anoInicio", str(ano_anterior), delay=1)

    us.wait_and_click(By.CSS_SELECTOR, "button.btn.btn-success[onclick='print_espelhos_periodo()']")

    utils.file.wait_for_downloads()
    utils.file.rename_and_move_downloaded_file(
        new_name=f"PONTO - {row['Nome']}.pdf",
        target_path=f"{config['saida']}/{formated_date}_{company_name}_PONTO"
    )
    service.mark_as_processed(cpf)
    contador += 1
    log.success(f"CPF {cpf_mask} ({row['Nome']}) processado com sucesso.")

log.success("Todos os relatórios de pontos foram gerados com sucesso.")

if new_file_data:
    new_file_df = pd.DataFrame(new_file_data)
    output_excel_path = os.path.join(config['saida'], f"{formated_date}_{company_name}_PONTO", f"RESULTADO.xlsx")
    if os.path.exists(output_excel_path):
        existing_df = pd.read_excel(output_excel_path)
        combined_df = pd.concat([existing_df, new_file_df], ignore_index=True)
        combined_df.to_excel(output_excel_path, index=False)
        log.success(f"Arquivo de resultados atualizado (append) em: {output_excel_path}")
    else:
        new_file_df.to_excel(output_excel_path, index=False)
        log.success(f"Arquivo de resultados salvo em: {output_excel_path}")

end_time = datetime.now()

insert_statistics = """
    INSERT INTO processados
    (machine_guid, data_inicio, data_termino, total_processos, produto, cliente)
    VALUES (?, ?, ?, ?, ?, ?)
"""

produto = "ponto_ahgora"

db.execute(insert_statistics, [machine_guid, start_time, end_time, contador, produto, config["cliente"]])
log.success("Estatísticas do processamento salvas com sucesso.")

db.close()
driver.quit()
input("Processo concluído. Pressione Enter para sair...")
# %%
