import os
import shutil
import time


class UtilsFile:

    def __init__(self, log, debug=False):
        self.debug = debug
        self.log = log

    def wait_for_downloads(self, download_path=None, timeout=60):
        """
        Espera todos os downloads terminarem (nenhum .crdownload na pasta).
        """
        if not download_path:
            download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if self.debug: 
            self.log.debug(f"Aguardando downloads na pasta: {download_path}")
        start_time = time.time()
        while True:
            
            if self.debug:
                self.log.debug(f"Verificando downloads na pasta: {download_path}")
            
            if not any(fname.endswith(".crdownload") for fname in os.listdir(download_path)):
                
                if self.debug:
                    self.log.debug("Todos os downloads concluídos (nenhum .crdownload encontrado).")
                
                break
            if time.time() - start_time > timeout:
                raise TimeoutError("Tempo excedido ao esperar downloads.")
            time.sleep(0.5)
    
    def rename_and_move_downloaded_file(self, new_name, target_path, download_path=None, extension=".pdf"):
        """
        Renomeia o último arquivo baixado e move para o destino especificado.
        """
        if not download_path:
            download_path = os.path.join(os.path.expanduser("~"), "Downloads")

        if self.debug:
            self.log.debug(f"Aguardando downloads na pasta: {download_path}")

        # Garante que o diretório de destino existe
        os.makedirs(target_path, exist_ok=True)
        if self.debug:
            self.log.debug(f"Pasta de destino garantida: {target_path}")

        # Pega o último arquivo baixado com a extensão desejada
        files = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.endswith(extension)]

        if self.debug:
            self.log.debug(f"Arquivos encontrados: {files}")

        if not files:
            raise FileNotFoundError(f"Nenhum arquivo com extensão {extension} encontrado na pasta de download.")

        latest_file = max(files, key=os.path.getctime)

        if self.debug:
            self.log.debug(f"Último arquivo encontrado: {latest_file}")
        
        new_path = os.path.join(target_path, new_name)

        if self.debug:
            self.log.debug(f"Renomeando e movendo arquivo para: {new_path}")

        shutil.move(latest_file, new_path)
        return new_path
    
    def verify_required_columns(self, file, required_columns):
        missing_columns = [col for col in required_columns if col not in file.columns]
        if missing_columns:
            self.log.error(f"Arquivo Excel está faltando as colunas obrigatórias: {', '.join(missing_columns)}. Encerrando o programa.")
            return False
        return True

    def verify_file_extension(self, file, allowed_extensions):
        if not any(file.endswith(ext) for ext in allowed_extensions):
            self.log.error(f"Arquivo não possui uma extensão válida. Extensões permitidas: {', '.join(allowed_extensions)}. Encerrando o programa.")
            return False
        return True
