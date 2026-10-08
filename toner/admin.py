from django.contrib import admin
from .models import Impressora, Leitura, ModeloToner, Suprimento, Troca


class SuprimentoInline(admin.TabularInline):
    model = Suprimento
    extra = 0
    readonly_fields = ("nome", "cor", "percentual", "atualizado", "alertado")
    can_delete = False


@admin.register(Impressora)
class ImpressoraAdmin(admin.ModelAdmin):
    list_display = ("nome", "ip", "setor", "marca", "modelo", "ativa", "online", "ultima_coleta")
    list_filter = ("setor", "marca", "ativa", "online")
    search_fields = ("nome", "ip", "setor", "modelo")
    inlines = [SuprimentoInline]
    readonly_fields = ("marca", "modelo", "contador_paginas", "online", "ultima_coleta", "ultimo_erro")

    fieldsets = (
        ("Configuração Principal", {
            "fields": ("nome", "ip", "setor", "community", "ativa"),
            "description": "Dados essenciais para a comunicação com a impressora."
        }),
        ("Dados Extraídos Automaticamente", {
            "fields": ("marca", "modelo", "contador_paginas"),
            "description": "Esses campos são preenchidos sozinhos pelo sistema através da leitura SNMP."
        }),
        ("Monitoramento", {
            "fields": ("online", "ultima_coleta", "ultimo_erro"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ModeloToner)
class ModeloTonerAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor", "estoque", "estoque_minimo")
    list_editable = ("estoque", "estoque_minimo")
    filter_horizontal = ("impressoras",)


@admin.register(Troca)
class TrocaAdmin(admin.ModelAdmin):
    list_display = ("data", "impressora", "suprimento", "toner", "usuario", "automatica")
    list_filter = ("automatica", "impressora__setor")
    date_hierarchy = "data"


admin.site.register(Leitura)
