from datetime import datetime
import os
from config.config import PROCESSED_RECORDS_FILE
import pandas as pd
import re

class Services:

    def __init__(self, log):
        self.log = log
    
    def already_processed(self, step, data):

        if not os.path.isfile(PROCESSED_RECORDS_FILE[step]):
            self.create_processed_records_file(step)
    
        with open(PROCESSED_RECORDS_FILE[step], 'r') as f:
            processed_data = f.read().splitlines()
        
        return data in processed_data
    
    def mark_as_processed(self, step, data):

        if not os.path.isfile(PROCESSED_RECORDS_FILE[step]):
            self.create_processed_records_file(step)

        data = data.strip()
        with open(PROCESSED_RECORDS_FILE[step], 'a') as f:
            f.write(data + "\n")

    def create_processed_records_file(self, step):
        with open(PROCESSED_RECORDS_FILE[step], 'w') as f:
            f.write("")

    def get_cpf_mask(self, cpf) -> str: 
        cpf = str(cpf).zfill(11)

        if cpf.isdigit():
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf
    
    def to_datetime_safe(self, value):
        if pd.isna(value):
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        try:
            return datetime.strptime(str(value), "%d/%m/%Y")
        except:
            return None


    def mais_de_um_ano(self, d1, d2) -> bool:
        d1 = self.to_datetime_safe(d1)
        d2 = self.to_datetime_safe(d2)
        if not d1 or not d2:
            return False
        return abs((d2 - d1).days) > 365


    def tem_dispensa_no_motivo_e_trabalhou_por_mais_de_6_meses(self, adm, dem, motivo) -> bool:
        if not motivo or pd.isna(motivo):
            return False

        if not re.search(r"dispensa", str(motivo), re.IGNORECASE):
            return False

        d1 = self.to_datetime_safe(adm)
        d2 = self.to_datetime_safe(dem)
        if not d1 or not d2:
            return False

        anos = d2.year - d1.year
        meses = d2.month - d1.month
        total_meses = anos * 12 + meses

        if d2.day < d1.day:
            total_meses -= 1

        return total_meses >= 6