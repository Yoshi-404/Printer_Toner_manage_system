from django.conf import settings
from django.core.management.base import BaseCommand

from toner.coletor import coletar_todas


class Command(BaseCommand):
    help = "Consulta todas as impressoras ativas via SNMP e grava os níveis de toner."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="usa dados simulados")

    def handle(self, *args, **opts):
        ok, falhas = coletar_todas(demo=opts["demo"] or settings.TONER_DEMO)
        self.stdout.write(f"Coleta concluída: {ok} ok, {falhas} com falha.")
