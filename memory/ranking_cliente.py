import json
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings

from .models import EnvioRanking, Partida


class RankingNoDisponible(Exception):
    pass


def mapa_credenciales(valor):
    try:
        datos = json.loads(valor)
    except (ValueError, RecursionError) as error:
        raise RankingNoDisponible from error
    if not isinstance(datos, dict) or any(not isinstance(v, str) or not v for v in datos.values()):
        raise RankingNoDisponible
    return datos


def token_valido(token):
    return token.isascii() and token.isprintable() and 32 <= len(token) <= 256


class SinRedirecciones(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def destino_global():
    destino = getattr(settings, "RANKING_URL", "").rstrip("/")
    try:
        url = urlsplit(destino)
        if url.scheme != "https" or not url.hostname or url.username is not None or url.path or url.query or url.fragment:
            raise ValueError
        if len(destino) > 255 or any(c.isspace() for c in destino):
            raise ValueError
        url.port
    except ValueError as error:
        raise RankingNoDisponible from error
    return destino


def peticion_global(destino, recurso, *, token=None, datos=None):
    cabeceras = {"Accept": "application/json"}
    cuerpo = None
    if token:
        if not token_valido(token):
            raise RankingNoDisponible
        cabeceras["Authorization"] = f"Bearer {token}"
    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        cabeceras["Content-Type"] = "application/json"
    solicitud = Request(f"{destino}/api/ranking/{recurso}", data=cuerpo, headers=cabeceras)
    limite = 512 * 1024
    try:
        with build_opener(SinRedirecciones()).open(solicitud, timeout=3) as respuesta:
            contenido = respuesta.read(limite + 1)
        if len(contenido) > limite:
            raise ValueError
        resultado = json.loads(contenido)
        if not isinstance(resultado, dict):
            raise ValueError
        return resultado
    except (OSError, ValueError, RecursionError) as error:
        raise RankingNoDisponible from error


def consultar_global(lunes, usuario):
    destino = destino_global()
    token = mapa_credenciales(getattr(settings, "RANKING_CREDENCIALES_LOCALES", "{}")).get(usuario)
    consulta = urlencode({"semana": lunes.isoformat()})
    recurso = f"semanal/?{consulta}"
    try:
        datos = peticion_global(destino, recurso, token=token)
    except RankingNoDisponible as error:
        causa = error.__cause__
        if not token or not isinstance(causa, HTTPError) or causa.code != 401:
            raise
        datos = peticion_global(destino, recurso)
    if datos.get("inicio") != lunes.isoformat() or not isinstance(datos.get("mejores"), list):
        raise RankingNoDisponible
    return datos


def sincronizar_resultados(destino, credenciales):
    enviados = fallidos = 0
    for usuario, token in credenciales.items():
        partidas = (
            Partida.objects.filter(
                usuario__username=usuario, practica=False, estado=Partida.Estado.GANADA,
                puntaje__gt=0, fin_servidor__isnull=False,
            ).exclude(envios_ranking__destino=destino).order_by("-fin_servidor", "pk")[:100]
        )
        for partida in partidas:
            datos = {
                "partida_id": str(partida.pk), "dificultad": partida.dificultad,
                "puntaje": partida.puntaje, "finalizada_en": partida.fin_servidor.isoformat(),
                "practica": partida.practica, "estado": partida.estado,
            }
            try:
                if peticion_global(destino, "resultados/", token=token, datos=datos).get("ok") is not True:
                    raise RankingNoDisponible
            except RankingNoDisponible as error:
                fallidos += 1
                causa = error.__cause__
                if isinstance(causa, HTTPError) and causa.code in {400, 409}:
                    continue
                break
            EnvioRanking.objects.get_or_create(partida=partida, destino=destino)
            enviados += 1
    return enviados, fallidos
