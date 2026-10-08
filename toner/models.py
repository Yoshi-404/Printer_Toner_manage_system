from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

CORES = [("preto", "Preto"), ("ciano", "Ciano"), ("magenta", "Magenta"),
         ("amarelo", "Amarelo"), ("outro", "Outro")]


class Impressora(models.Model):
    nome = models.CharField(max_length=80)
    ip = models.GenericIPAddressField(unique=True)
    setor = models.CharField(max_length=60)
    marca = models.CharField(max_length=40, blank=True)
    modelo = models.CharField(max_length=80, blank=True)
    community = models.CharField("SNMP community", max_length=60, default="public")
    ativa = models.BooleanField(default=True)
    online = models.BooleanField(default=True)
    ultima_coleta = models.DateTimeField(null=True, blank=True)
    ultimo_erro = models.CharField(max_length=200, blank=True)
    contador_paginas = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["setor", "nome"]
        verbose_name_plural = "impressoras"

    def __str__(self):
        return f"{self.nome} ({self.ip})"

    @property
    def pior_nivel(self):
        n = [s.percentual for s in self.suprimentos.all() if s.percentual is not None]
        return min(n) if n else None


class Suprimento(models.Model):
    impressora = models.ForeignKey(Impressora, on_delete=models.CASCADE, related_name="suprimentos")
    nome = models.CharField(max_length=120)
    cor = models.CharField(max_length=10, choices=CORES, default="outro")
    percentual = models.PositiveSmallIntegerField(null=True, blank=True)
    atualizado = models.DateTimeField(null=True, blank=True)
    alertado = models.BooleanField(default=False)

    class Meta:
        ordering = ["cor", "nome"]
        unique_together = [("impressora", "nome")]

    def __str__(self):
        return f"{self.impressora.nome} - {self.nome}"

    @property
    def classe(self):
        if self.percentual is None:
            return "nd"
        lim = settings.TONER_LIMITE_ALERTA
        if self.percentual <= lim:
            return "crit"
        return "warn" if self.percentual <= lim * 2 else "ok"

    def previsao_dias(self):
        """Estimativa de dias até acabar, com base no consumo dos últimos 30 dias."""
        if self.percentual is None:
            return None
        desde = timezone.now() - timedelta(days=30)
        pts = [(p, d) for p, d in self.leituras.filter(data__gte=desde)
               .order_by("data").values_list("percentual", "data") if p is not None]
        if len(pts) < 2:
            return None
        consumo = sum(max(a[0] - b[0], 0) for a, b in zip(pts, pts[1:]))
        dias = (pts[-1][1] - pts[0][1]).total_seconds() / 86400
        if consumo <= 0 or dias <= 0:
            return None
        return round(self.percentual / (consumo / dias))


class Leitura(models.Model):
    suprimento = models.ForeignKey(Suprimento, on_delete=models.CASCADE, related_name="leituras")
    percentual = models.PositiveSmallIntegerField(null=True, blank=True)
    paginas = models.PositiveIntegerField(null=True, blank=True)
    data = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-data"]


class ModeloToner(models.Model):
    nome = models.CharField("modelo do toner", max_length=80, unique=True)
    cor = models.CharField(max_length=10, choices=CORES, default="preto")
    estoque = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=2)
    impressoras = models.ManyToManyField(Impressora, blank=True, related_name="toners")

    class Meta:
        ordering = ["nome"]
        verbose_name = "modelo de toner"
        verbose_name_plural = "modelos de toner"

    def __str__(self):
        return self.nome

    @property
    def baixo(self):
        return self.estoque <= self.estoque_minimo


class Troca(models.Model):
    impressora = models.ForeignKey(Impressora, on_delete=models.CASCADE, related_name="trocas")
    suprimento = models.ForeignKey(Suprimento, on_delete=models.SET_NULL, null=True, blank=True)
    toner = models.ForeignKey(ModeloToner, on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    automatica = models.BooleanField(default=False)
    observacao = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-data"]
        verbose_name_plural = "trocas"
