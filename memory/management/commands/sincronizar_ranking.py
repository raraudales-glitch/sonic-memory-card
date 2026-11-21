from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from memory.ranking_cliente import RankingNoDisponible, destino_global, mapa_credenciales, sincronizar_resultados


class Command(BaseCommand):
    help = "Envía al servicio central las victorias oficiales pendientes."

    def add_arguments(self, parser):
        parser.add_argument("--continuo", action="store_true")

    def handle(self, *args, **options):
        if settings.RANKING_CENTRAL:
            raise CommandError("La sincronización se ejecuta en las instalaciones de juego.")
        try:
            destino = destino_global()
            credenciales = mapa_credenciales(settings.RANKING_CREDENCIALES_LOCALES)
        except RankingNoDisponible as error:
            raise CommandError("Configura la dirección HTTPS y las credenciales locales del ranking.") from error
        if not credenciales:
            raise CommandError("Configura al menos una credencial local del ranking.")

        while True:
            enviados, fallidos = sincronizar_resultados(destino, credenciales)
            if enviados or fallidos or not options["continuo"]:
                self.stdout.write(f"Confirmados: {enviados}. Envíos aplazados: {fallidos}.")
            if not options["continuo"]:
                break
            sleep(30)
            close_old_connections()
