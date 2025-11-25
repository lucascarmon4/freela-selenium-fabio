import os
import shutil
import time


class UtilsFile:

    def __init__(self, log, debug=False):
        self.debug_on = debug
        self.log = log


    def debug(self, message):
        if self.debug_on:
            self.log.debug(message)


    def _wait_file_stable(self, file_path: str, stable_secs: float = 1.0, poll: float = 0.2, timeout: int = 120):
        """Espera o arquivo parar de crescer antes de prosseguir."""
        t0 = time.time()
        last = -1
        since = None
        while True:
            try:
                size = os.path.getsize(file_path)
            except FileNotFoundError:
                size = -1

            if size > 0 and size == last:
                if since is None:
                    since = time.time()
                if time.time() - since >= stable_secs:
                    self.debug(f"Estável: {file_path} ({size} bytes)")
                    return
            else:
                since = None

            last = size
            if time.time() - t0 > timeout:
                raise TimeoutError(f"Timeout aguardando estabilidade de {file_path}")
            time.sleep(poll)


    def wait_for_downloads(self, download_path=None, timeout=120, poll=0.25):
        """
        Espera pelo **próximo** download terminar na pasta indicada.
        Funciona mesmo se NUNCA existir .crdownload (pdf rápido).

        Retorna o caminho do PDF baixado.
        """
        if not download_path:
            download_path = os.path.join(os.path.expanduser("~"), "Downloads", "_selenium_downloads")
        os.makedirs(download_path, exist_ok=True)

        baseline = set(os.listdir(download_path))
        t0 = time.time()
        self.debug(f"Aguardando novo download em: {download_path}")

        saw_cr = False
        while True:
            current = set(os.listdir(download_path))
            new_entries = list(current - baseline)

            crs = [f for f in new_entries if f.endswith(".crdownload")]
            if crs:
                saw_cr = True
                self.debug(f".crdownload detectado: {crs}")

            pdfs = []
            for f in current:
                if f.lower().endswith(".pdf"):
                    p = os.path.join(download_path, f)
                    try:
                        if f in new_entries or os.path.getctime(p) >= t0 - 0.5:
                            pdfs.append(p)
                    except FileNotFoundError:
                        pass

            if pdfs:
                pdf_path = max(pdfs, key=os.path.getctime)
                self._wait_file_stable(pdf_path, stable_secs=1.0, timeout=timeout)
                self.debug(f"Download concluído: {pdf_path}")
                return pdf_path

            if saw_cr:
                any_cr_now = any(f.endswith(".crdownload") for f in current)
                if not any_cr_now:
                    self.debug("crdownload sumiu; aguardando PDF aparecer...")

            if time.time() - t0 > timeout:
                raise TimeoutError("Tempo excedido aguardando novo download (PDF).")
            time.sleep(poll)


    def rename_and_move_downloaded_file(self, new_name, target_path, download_path=None, extension=".pdf"):
        """
        Renomeia o último arquivo baixado e move para o destino especificado.
        """
        if not download_path:
            download_path = os.path.join(os.path.expanduser("~"), "Downloads", "_selenium_downloads")

        self.debug(f"Aguardando downloads na pasta: {download_path}")

        os.makedirs(target_path, exist_ok=True)
        self.debug(f"Pasta de destino garantida: {target_path}")

        files = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.endswith(extension)]

        self.debug(f"Arquivos encontrados: {files}")

        if not files:
            raise FileNotFoundError(f"Nenhum arquivo com extensão {extension} encontrado na pasta de download.")

        latest_file = max(files, key=os.path.getctime)

        self.debug(f"Último arquivo encontrado: {latest_file}")
        
        new_path = os.path.join(target_path, new_name)

        self.debug(f"Renomeando e movendo arquivo para: {new_path}")

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
