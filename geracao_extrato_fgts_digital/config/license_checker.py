from utils.log import UtilsLog
from datetime import datetime
import socket
import winreg


def get_machine_guid():
    key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Cryptography",
        0,
        winreg.KEY_READ
    )
    value, _ = winreg.QueryValueEx(key, "MachineGuid")
    return value

def get_hostname_machine_guid():
    hostname = socket.gethostname()
    machine_guid = get_machine_guid()
    return hostname, machine_guid

def check_license(db):
    hostname, machine_guid = get_hostname_machine_guid()

    result = db.query("""
        SELECT data_vencimento, descricao_local FROM licencas
        WHERE hostname = ? AND machine_guid = ? AND status_licenca = 1 AND produto = 'extrato_fgts'
    """, [hostname, machine_guid])

    if not result:
        UtilsLog.error(f"Licença inativa, favor entrar em contato com administrador: {hostname} ({machine_guid})")
        return False, None

    vencimento = result[0]['data_vencimento']

    if vencimento and datetime.strptime(str(vencimento), "%Y-%m-%d %H:%M:%S") < datetime.now():
        UtilsLog.warning(f"Licença expirada, favor entrar em contato com administrador: {hostname} ({machine_guid})")
        return False, machine_guid

    db.execute("""
        UPDATE licencas SET data_ultimo_acesso = GETDATE()
        WHERE hostname = ? AND machine_guid = ?
    """, [hostname, machine_guid])

    UtilsLog.success(f"Máquina autorizada: {hostname} ({machine_guid})")
    return True, machine_guid
