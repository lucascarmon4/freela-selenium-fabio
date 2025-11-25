from config.get_credential import ConfigSegura
import pyodbc
from utils.core import Utils

class SQLServerHelper:
    def __init__(self, config):
        self.server = config["server"]
        self.database = config["database"]
        self.cript = ConfigSegura()
        self.username, self.password = self.cript.obter_credenciais()
        self.driver = None
        self.conn = None
        self.log = Utils().log

    def connect(self):
        drivers = pyodbc.drivers()
        if 'ODBC Driver 17 for SQL Server' in drivers:
            self.driver = '{ODBC Driver 17 for SQL Server}'
        elif 'SQL Server' in drivers:
            self.driver = '{SQL Server}'
        else:
            raise Exception("Driver ODBC não encontrado.")

        conn_str = (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )

        self.conn = pyodbc.connect(conn_str)
        self.log.success("Conectado com sucesso!")

    def query(self, sql, params=None):
        cursor = self.conn.cursor()
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()
            
    def execute(self, sql, params=None):
        if not self.conn:
            raise Exception("Sem conexão com o banco.")
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params or [])
            self.conn.commit()
        except Exception as e:
            self.log.error(f"Erro ao executar comando: {e}")
            self.conn.rollback()