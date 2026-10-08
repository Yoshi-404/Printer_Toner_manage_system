from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from toner.coletor import coletar_todas
from toner.models import Impressora, ModeloToner

IMPRESSORAS = [
    ("RH-01", "10.10.1.11", "RH", "HP", "LaserJet Pro M404"),
    ("RH-02", "10.10.1.12", "RH", "Brother", "HL-L6402"),
    ("FIN-01", "10.10.2.11", "Financeiro", "Ricoh", "SP 5300 Color"),
    ("FIN-02", "10.10.2.12", "Financeiro", "Kyocera", "ECOSYS P3150"),
    ("COM-01", "10.10.3.11", "Comercial", "Samsung", "Xpress M4020"),
    ("COM-02", "10.10.3.12", "Comercial", "HP", "Color LaserJet M454"),
    ("LOG-01", "10.10.4.11", "Logística", "Lexmark", "MS521"),
    ("TI-01", "10.10.5.11", "TI", "Xerox", "B225"),
]
TONERS = [("HP CF258A", "preto", 4), ("Brother TN-3492", "preto", 1), ("Ricoh SP 5300 Preto", "preto", 2),
          ("Kyocera TK-1175", "preto", 3), ("Samsung MLT-D111S", "preto", 5), ("Lexmark 56F4000", "preto", 2),
          ("Xerox 106R02777", "preto", 1)]


class Command(BaseCommand):
    help = "Cria dados de demonstração (impressoras, toners, histórico de 12 dias e usuário admin)."

    def handle(self, *args, **opts):
        Group.objects.get_or_create(name="TI")
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@empresa.local", "admin123")
        for nome, ip, setor, marca, modelo in IMPRESSORAS:
            Impressora.objects.get_or_create(ip=ip, defaults=dict(nome=nome, setor=setor, marca=marca, modelo=modelo))
        for nome, cor, qtd in TONERS:
            ModeloToner.objects.get_or_create(nome=nome, defaults=dict(cor=cor, estoque=qtd))
        for t, imp in zip(ModeloToner.objects.all(), Impressora.objects.all()):
            t.impressoras.add(imp)
        agora = timezone.now()
        for i in range(12, -1, -1):
            coletar_todas(demo=True, agora=agora - timedelta(days=i))
        self.stdout.write(self.style.SUCCESS("Demo pronta. Login: admin / admin123 (apenas para testes!)"))
