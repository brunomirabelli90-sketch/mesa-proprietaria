"""
Modulo de licenca: gera e valida um arquivo de licenca (licenca.lic)
amarrado ao ID da maquina Windows, com data de validade e assinatura
HMAC (evita que alguem edite o arquivo a mao pra estender a validade
ou trocar de maquina).

NAO e' protecao contra engenharia reversa avancada - so afasta copia
casual. Para reforcar, distribua o autoclicker como .exe (PyInstaller)
em vez do .py.

IMPORTANTE: troque o valor de SEGREDO abaixo por algo unico seu antes
de gerar licencas, e nunca compartilhe esse arquivo (licenca.py) nem o
gerar_licenca.py com quem vai receber a licenca - so o autoclicker
final (de preferencia compilado) e o licenca.lic gerado.
"""
import hashlib
import hmac
import json
from datetime import date

SEGREDO = b"TROQUE_ESTE_SEGREDO_POR_UM_VALOR_UNICO_SEU_E_NAO_COMPARTILHE"


def obter_id_maquina():
    """ID estavel deste Windows (MachineGuid do registro)."""
    import winreg

    chave = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Cryptography",
        0,
        winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
    )
    try:
        valor, _ = winreg.QueryValueEx(chave, "MachineGuid")
    finally:
        winreg.CloseKey(chave)
    return valor


def _assinar(maquina_id, expira_em):
    mensagem = f"{maquina_id}|{expira_em}".encode("utf-8")
    return hmac.new(SEGREDO, mensagem, hashlib.sha256).hexdigest()


def gerar_licenca(maquina_id, expira_em):
    """expira_em no formato AAAA-MM-DD."""
    return {
        "maquina_id": maquina_id,
        "expira_em": expira_em,
        "assinatura": _assinar(maquina_id, expira_em),
    }


def validar_licenca(caminho="licenca.lic"):
    """Retorna (ok: bool, mensagem: str)."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except FileNotFoundError:
        return False, f"Arquivo de licenca '{caminho}' nao encontrado."
    except json.JSONDecodeError:
        return False, "Arquivo de licenca corrompido ou invalido."

    maquina_id = dados.get("maquina_id")
    expira_em = dados.get("expira_em")
    assinatura = dados.get("assinatura")
    if not all([maquina_id, expira_em, assinatura]):
        return False, "Arquivo de licenca incompleto."

    esperada = _assinar(maquina_id, expira_em)
    if not hmac.compare_digest(assinatura, esperada):
        return False, "Assinatura da licenca invalida (arquivo alterado ou gerado com outro segredo)."

    if maquina_id != obter_id_maquina():
        return False, "Esta licenca nao corresponde a esta maquina."

    try:
        data_expira = date.fromisoformat(expira_em)
    except ValueError:
        return False, "Data de validade invalida na licenca."

    if date.today() > data_expira:
        return False, f"Licenca expirada em {expira_em}."

    return True, f"Licenca valida ate {expira_em}."
