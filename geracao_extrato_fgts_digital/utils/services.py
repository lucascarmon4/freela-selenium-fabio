import os
from config.config import PROCESSED_RECORDS_FILE

class Services:

    def __init__(self, log):
        self.log = log

    def choose_company(self, db, config):
        results = db.query(
            'select item_menu, nome_empresa, cnpj from extrato_fgts_procuradores where cliente = ? order by item_menu',
            [config['cliente']]
        )
        options = {row["item_menu"]: row["nome_empresa"] for row in results}
        companys = {row["item_menu"]: {"nome_empresa": row["nome_empresa"], "cnpj": row["cnpj"]} for row in results}

        self.log.option("Escolha uma opção: ", options)

        while True: 
            try: 
                choice = int(input("Digite o número da empresa: "))
                selected = companys[choice]
                break
            except (ValueError, KeyError): 
                self.log.error("Opção inválida. Tente novamente.")
        self.log.info(f"Empresa selecionada: {selected["nome_empresa"]} - CNPJ: {selected["cnpj"]}")

        return selected["nome_empresa"], selected["cnpj"]
    
    def cpf_already_processed(self, cpf):

        if not os.path.isfile(PROCESSED_RECORDS_FILE):
            self.create_processed_records_file()
        
        with open(PROCESSED_RECORDS_FILE, 'r') as f:
            processed_cpfs = f.read().splitlines()
        
        return cpf in processed_cpfs
    
    def mark_as_processed(self, cpf):

        if not os.path.isfile(PROCESSED_RECORDS_FILE):
            self.create_processed_records_file()

        cpf = cpf.strip()
        with open(PROCESSED_RECORDS_FILE, 'a') as f:
            f.write(cpf + "\n")

    def create_processed_records_file(self):
        with open(PROCESSED_RECORDS_FILE, 'w') as f:
            f.write("")