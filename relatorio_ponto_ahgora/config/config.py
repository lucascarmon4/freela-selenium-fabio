import configparser
import os
import sys
import certifi

PROCESSED_RECORDS_FILE = "ponto_ahgora_processados.txt"

os.environ['SSL_CERT_FILE'] = certifi.where()

def resource_path(relative_path) -> str:
    """Retorna o caminho absoluto do arquivo"""
    if getattr(sys, 'frozen', False):  
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

CONFIG_PATH = resource_path("config.ini")

def load_config() -> dict: 
    def to_bool(value):
        return str(value).strip().lower() in ['1', 'true', 'yes', 'sim']
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    if not config.sections():
        raise FileNotFoundError("Arquivo de configuração não encontrado ou vazio.")
    
    config_values = { 
        "usuario_ahgora": config.get("PARAMETROS", "usuario_ahgora"),
        "cliente": config.get("PARAMETROS", "cliente"),

        "origem": config.get("DIRETORIOS", "origem"),
        "saida": config.get("DIRETORIOS", "saida"),

        "server": config.get("DB", "server"),
        "database": config.get("DB", "database"),
        "username": config.get("DB", "username"),
        "password": config.get("DB", "password"),
        "cript": to_bool(config.get("DB", "cript"))
    }

    return config_values

def save_origem(new_path: str):
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")

    if not config.has_section("DIRETORIOS"):
        config.add_section("DIRETORIOS")

    if new_path:
        config.set("DIRETORIOS", "origem", new_path)

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)