import logging
import random
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.utils import timezone

from .models import Impressora, Leitura, ModeloToner, Suprimento, Troca
from .snmp import ler_impressora

log = logging.getLogger("toner")

_CORES = [("black", "preto"), ("preto", "preto"), ("cyan", "ciano"), ("ciano", "ciano"),
          ("magenta", "magenta"), ("yellow", "amarelo"), ("amarelo", "amarelo")]


def detectar_cor(nome):
    n = nome.lower()
    return next((cor for chave, cor in _CORES if chave in n), "outro")


def dados_demo(imp):
    """Simula leituras SNMP para testar o sistema sem impressoras reais."""
    if random.random() < 0.03:
        raise RuntimeError("tempo esgotado (simulado)")
    existentes = list(imp.suprimentos.all())
    if not existentes:
        nomes = ["Black Toner"]
        if "color" in imp.modelo.lower():
            nomes += ["Cyan Toner", "Magenta Toner", "Yellow Toner"]
        sups = [{"nome": n, "percentual": random.randint(25, 100)} for n in nomes]
    else:
        sups = []
        for s in existentes:
            p = max(0, (s.percentual if s.percentual is not None else 50) - random.randint(0, 6))
            if p <= 8 and random.random() < 0.3:
                p = 100  # simula troca de toner
            sups.append({"nome": s.nome, "percentual": p})
    return {"modelo": imp.modelo, "paginas": (imp.contador_paginas or 1000) + random.randint(0, 200),
            "suprimentos": sups}


def _alertar(imp, sup):
    msg = (f"Toner baixo: {sup.nome} em {imp.nome} ({imp.ip}, setor {imp.setor}) "
           f"está com {sup.percentual}%.")
    log.warning(msg)
    if settings.ALERTA_EMAILS:
        send_mail(f"[Toner] {imp.nome}: {sup.nome} {sup.percentual}%", msg, None,
                  settings.ALERTA_EMAILS, fail_silently=True)


def _troca_automatica(imp, sup, agora):
    toner = ModeloToner.objects.filter(impressoras=imp, cor=sup.cor).first()
    Troca.objects.create(impressora=imp, suprimento=sup, toner=toner, data=agora, automatica=True,
                         observacao="Detectada pelo aumento do nível")
    if toner and toner.estoque > 0:
        ModeloToner.objects.filter(pk=toner.pk).update(estoque=F("estoque") - 1)


def salvar(imp, dados, erro, agora):
    imp.ultima_coleta = agora
    if erro:
        imp.online, imp.ultimo_erro = False, str(erro)[:200]
        imp.save(update_fields=["online", "ultimo_erro", "ultima_coleta"])
        return
    imp.online, imp.ultimo_erro = True, ""
    imp.contador_paginas = dados["paginas"] or imp.contador_paginas
    if dados["modelo"]:
        if not imp.modelo:
            imp.modelo = dados["modelo"][:80]
        if not imp.marca:
            # Tenta extrair a marca pegando a primeira palavra do modelo (ex: "Brother DCP...")
            imp.marca = dados["modelo"].split()[0][:40]
    imp.save()
    for s in dados["suprimentos"]:
        sup, _ = Suprimento.objects.get_or_create(
            impressora=imp, nome=s["nome"][:120], defaults={"cor": detectar_cor(s["nome"])})
        antes, novo = sup.percentual, s["percentual"]
        if antes is not None and novo is not None and novo - antes >= settings.TONER_SALTO_TROCA:
            _troca_automatica(imp, sup, agora)
        sup.percentual, sup.atualizado = novo, agora
        if novo is not None:
            if novo > settings.TONER_LIMITE_ALERTA:
                sup.alertado = False
            elif not sup.alertado:
                _alertar(imp, sup)
                sup.alertado = True
        sup.save()
        Leitura.objects.create(suprimento=sup, percentual=novo, paginas=dados["paginas"], data=agora)


def _ler(imp):
    try:
        return imp, ler_impressora(imp.ip, imp.community), None
    except Exception as e:
        return imp, None, e


def coletar_todas(demo=False, agora=None):
    agora = agora or timezone.now()
    imps = list(Impressora.objects.filter(ativa=True))
    if demo:  # simulação lê o banco, então roda sequencial
        resultados = []
        for i in imps:
            try:
                resultados.append((i, dados_demo(i), None))
            except Exception as e:
                resultados.append((i, None, e))
    else:
        with ThreadPoolExecutor(max_workers=10) as ex:  # SNMP em paralelo; banco na thread principal
            resultados = list(ex.map(_ler, imps))
    for imp, dados, erro in resultados:
        salvar(imp, dados, erro, agora)
    falhas = sum(1 for _, _, e in resultados if e)
    return len(imps) - falhas, falhas
