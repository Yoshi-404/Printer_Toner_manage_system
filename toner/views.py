from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

import threading
from .coletor import coletar_todas
from .models import Impressora, Leitura, ModeloToner, Suprimento, Troca


def ti_required(view):
    """Acesso liberado a todos (login e grupo de TI removidos)."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        return view(request, *args, **kwargs)
    return wrapper


@ti_required
def dashboard(request):
    setor = request.GET.get("setor", "")
    so_criticos = request.GET.get("criticos") == "1"
    todas = Impressora.objects.filter(ativa=True).prefetch_related("suprimentos")
    lista = [i for i in todas if not setor or i.setor == setor]
    lim = settings.TONER_LIMITE_ALERTA
    criticos = [i for i in lista if i.pior_nivel is not None and i.pior_nivel <= lim]
    resumo = {
        "total": len(lista),
        "offline": sum(1 for i in lista if not i.online),
        "criticos": len(criticos),
        "estoque_baixo": sum(1 for t in ModeloToner.objects.all() if t.baixo),
    }
    if so_criticos:
        lista = criticos
    lista.sort(key=lambda i: (i.pior_nivel is None, i.pior_nivel if i.pior_nivel is not None else 0))
    return render(request, "toner/dashboard.html", {
        "impressoras": lista, "resumo": resumo, "limite": lim,
        "setores": sorted({i.setor for i in todas}), "setor": setor, "so_criticos": so_criticos,
    })


@ti_required
def impressora(request, pk):
    imp = get_object_or_404(Impressora.objects.prefetch_related("suprimentos"), pk=pk)
    toners = ModeloToner.objects.filter(impressoras=imp) or ModeloToner.objects.all()
    return render(request, "toner/impressora.html", {
        "imp": imp, "toners": toners,
        "leituras": Leitura.objects.filter(suprimento__impressora=imp).select_related("suprimento")[:40],
        "trocas": imp.trocas.select_related("suprimento", "toner", "usuario")[:20],
    })


@ti_required
@require_POST
def registrar_troca(request, pk):
    imp = get_object_or_404(Impressora, pk=pk)
    sup = Suprimento.objects.filter(pk=request.POST.get("suprimento"), impressora=imp).first()
    toner = ModeloToner.objects.filter(pk=request.POST.get("toner")).first()
    usuario = request.user if request.user.is_authenticated else None
    Troca.objects.create(impressora=imp, suprimento=sup, toner=toner, usuario=usuario,
                         observacao=request.POST.get("observacao", "")[:200])
    if toner:
        if toner.estoque > 0:
            ModeloToner.objects.filter(pk=toner.pk).update(estoque=F("estoque") - 1)
        else:
            messages.warning(request, f"Estoque de {toner.nome} já estava zerado.")
    messages.success(request, "Troca registrada.")
    return redirect("impressora", pk=pk)


@ti_required
def estoque(request):
    if request.method == "POST":
        t = get_object_or_404(ModeloToner, pk=request.POST.get("toner"))
        try:
            qtd = int(request.POST.get("quantidade", 0))
        except ValueError:
            qtd = 0
        if qtd > 0:
            ModeloToner.objects.filter(pk=t.pk).update(estoque=F("estoque") + qtd)
            messages.success(request, f"+{qtd} em {t.nome}.")
        return redirect("estoque")
    return render(request, "toner/estoque.html", {"toners": ModeloToner.objects.prefetch_related("impressoras")})


@ti_required
@require_POST
def coletar_agora(request):
    threading.Thread(target=coletar_todas, kwargs={"demo": settings.TONER_DEMO}).start()
    messages.success(request, "A coleta foi iniciada em segundo plano! A página será atualizada com os novos dados em instantes.")
    return redirect("dashboard")
