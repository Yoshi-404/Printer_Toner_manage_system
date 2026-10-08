"""Leitura SNMP via Printer MIB (RFC 3805). Requer o pacote 'snmp' (net-snmp) no servidor."""
import subprocess

OID_NOME = "1.3.6.1.2.1.43.11.1.1.6"
OID_MAX = "1.3.6.1.2.1.43.11.1.1.8"
OID_NIVEL = "1.3.6.1.2.1.43.11.1.1.9"
OID_PAGINAS = "1.3.6.1.2.1.43.10.2.1.4.1.1"
OID_MODELO = "1.3.6.1.2.1.25.3.2.1.3.1"


class SNMPError(Exception):
    pass


def _walk(ip, community, oid, timeout=4):
    try:
        r = subprocess.run(
            ["snmpwalk", "-v2c", "-c", community, "-Oqv", "-t", str(timeout), "-r", "1", ip, oid],
            capture_output=True, text=True, timeout=timeout * 3,
        )
    except FileNotFoundError:
        raise SNMPError("snmpwalk não instalado (apt install snmp)")
    except subprocess.TimeoutExpired:
        raise SNMPError("tempo esgotado")
    if r.returncode != 0 or not r.stdout.strip():
        raise SNMPError((r.stderr or r.stdout or "sem resposta SNMP").strip()[:150])
    return [l.strip().strip('"') for l in r.stdout.splitlines() if l.strip()]


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def ler_proprietario_brother(ip, community, timeout=4):
    oid = "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0"
    try:
        r = subprocess.run(
            ["snmpwalk", "-v2c", "-c", community, "-Oqv", "-t", str(timeout), "-r", "1", ip, oid],
            capture_output=True, text=True, timeout=timeout * 3,
        )
    except Exception:
        return {}
    if r.returncode != 0 or not r.stdout.strip() or "No Such Object" in r.stdout:
        return {}
    
    hex_str = r.stdout.replace('"', '').replace('\n', '').replace('\r', '').replace(' ', '')
    chunks = [hex_str[i:i+14] for i in range(0, len(hex_str), 14) if len(hex_str[i:i+14]) == 14]
    
    toner_codes = {
        "6f": "black", "a1": "black",
        "70": "cyan",  "a2": "cyan",
        "71": "magenta","a3": "magenta",
        "72": "yellow", "a4": "yellow",
    }
    
    brother_sups = {}
    for chunk in chunks:
        code = chunk[0:2].lower()
        if code in toner_codes:
            try:
                val_hex = chunk[6:14]
                pct = int(val_hex, 16) / 100
                brother_sups[toner_codes[code]] = round(pct)
            except ValueError:
                pass
    return brother_sups

def ler_impressora(ip, community="public"):
    brother_extras = ler_proprietario_brother(ip, community)
    nomes = _walk(ip, community, OID_NOME)
    maximos = _walk(ip, community, OID_MAX)
    niveis = _walk(ip, community, OID_NIVEL)
    
    suprimentos = []
    for nome, mx, nv in zip(nomes, maximos, niveis):
        n_lower = nome.lower()
        if any(x in n_lower for x in ["fuser", "roller", "belt", "transfer", "retard"]):
            continue

        pct = None
        if brother_extras:
            if "black" in n_lower or ("toner" in n_lower and "cyan" not in n_lower and "magenta" not in n_lower and "yellow" not in n_lower):
                pct = brother_extras.get("black", pct)
            if "cyan" in n_lower: pct = brother_extras.get("cyan", pct)
            if "magenta" in n_lower: pct = brother_extras.get("magenta", pct)
            if "yellow" in n_lower: pct = brother_extras.get("yellow", pct)

        if pct is None:
            mx, nv = _int(mx), _int(nv)
            # -2 = desconhecido, -3 = "ainda tem" sem informar quanto
            if mx and mx > 0 and nv is not None and nv >= 0:
                pct = round(nv / mx * 100)
            elif mx is not None and mx <= 0 and nv is not None and 0 <= nv <= 100:
                pct = nv
            elif mx is not None and mx <= 0 and nv == -3:
                # Brother frequentemente retorna -3 para "nível OK/Cheio". Para não quebrar a tela, assumimos 100%
                pct = 100
        
        suprimentos.append({"nome": nome, "percentual": pct})
    try:
        paginas = _int(_walk(ip, community, OID_PAGINAS)[0])
    except SNMPError:
        paginas = None
    try:
        modelo = _walk(ip, community, OID_MODELO)[0]
    except SNMPError:
        modelo = ""
    return {"modelo": modelo, "paginas": paginas, "suprimentos": suprimentos}
