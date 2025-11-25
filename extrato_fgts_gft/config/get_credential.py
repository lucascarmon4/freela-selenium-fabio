import configparser
from utils.core import Utils
import os
from cryptography.fernet import Fernet
from config.config import resource_path

class ConfigSegura:
    def __init__(self, config_path=resource_path('config.ini'), key_path=resource_path('secret.key')):
        self.config_path = config_path
        self.key_path = key_path
        self._fernet = None
        self._config = configparser.ConfigParser()

        self.log = Utils().log

        self._carregar_config()
        self._garantir_chave()

    def _garantir_chave(self):
        if not os.path.exists(self.key_path):
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
        with open(self.key_path, 'rb') as f:
            self._fernet = Fernet(f.read().strip())

    def _carregar_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        self._config.read(self.config_path)

    def _salvar_config(self):
        with open(self.config_path, 'w') as f:
            self._config.write(f)

    def _criptografar(self, texto: str) -> str:
        return self._fernet.encrypt(texto.encode()).decode()

    def _descriptografar(self, texto: str) -> str:
        return self._fernet.decrypt(texto.encode()).decode()

    def obter_credenciais(self):
        if 'DB' not in self._config:
            raise ValueError("Seção 'DB' não encontrada no arquivo de configuração.")

        criptografado = self._config.getboolean('DB', 'cript', fallback=False)

        if not criptografado:
            username = self._config.get('DB', 'username')
            password = self._config.get('DB', 'password')

            self._config.set('DB', 'username', self._criptografar(username))
            self._config.set('DB', 'password', self._criptografar(password))
            self._config.set('DB', 'cript', '1')

            self._salvar_config()
            self.log.success("Configurações criptografadas e atualizadas.")
            return username, password
        else:
            username = self._descriptografar(self._config.get('DB', 'username'))
            password = self._descriptografar(self._config.get('DB', 'password'))
            self.log.success("Configurações descriptografadas com sucesso.")
            return username, password
