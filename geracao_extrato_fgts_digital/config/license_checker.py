from utils.log import UtilsLog
from datetime import datetime
import socket, uuid

def get_hostname_mac():
    hostname = socket.gethostname()
    mac = ':'.join(['{:02X}'.format((uuid.getnode() >> i) & 0xff) for i in range(40, -1, -8)])
    return hostname, mac

def check_license(db):
    hostname, mac = get_hostname_mac()

    result = db.query("""
        SELECT data_vencimento, descricao_local FROM licencas
        WHERE hostname = ? AND mac_address = ? AND status_licenca = 1 AND produto = 'extrato_fgts'
    """, [hostname, mac])

    if not result:
        UtilsLog.error(f"Licença inativa, favor entrar em contato com administrador: {hostname} ({mac})")
        return False, None

    vencimento = result[0]['data_vencimento']

    if vencimento and datetime.strptime(str(vencimento), "%Y-%m-%d %H:%M:%S") < datetime.now():
        UtilsLog.warning(f"Licença expirada, favor entrar em contato com administrador: {hostname} ({mac})")
        return False, mac

    db.execute("""
        UPDATE licencas SET data_ultimo_acesso = GETDATE()
        WHERE hostname = ? AND mac_address = ?
    """, [hostname, mac])

    UtilsLog.success(f"Máquina autorizada: {hostname} ({mac})")
    return True, mac
