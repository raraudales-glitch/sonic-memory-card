import hashlib
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Max, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Partida, ResultadoRanking
from .ranking_cliente import RankingNoDisponible, consultar_global, mapa_credenciales, token_valido
from .services import NIVELES
from .views import leer_objeto_json


HUSO = ZoneInfo("America/Tegucigalpa")


def lunes_actual():
    hoy = timezone.now().astimezone(HUSO).date()
    return hoy - timedelta(days=hoy.weekday())


def semana_solicitada(valor):
    actual = lunes_actual()
    if valor is None:
        return actual
    lunes = date.fromisoformat(valor)
    if lunes.isoformat() != valor or lunes.year < 2000 or lunes.weekday() != 0 or lunes > actual:
        raise ValueError
    return lunes


def acceso_central(request, *, obligatorio=False):
    if not getattr(settings, "RANKING_CENTRAL", False):
        return None, JsonResponse({"error": "Servicio central deshabilitado"}, status=404)
    if not request.is_secure():
        return None, JsonResponse({"error": "Se requiere HTTPS"}, status=403)
    cabecera = request.headers.get("Authorization", "")
    if not cabecera and not obligatorio:
        return None, None
    esquema, _, token = cabecera.partition(" ")
    if esquema != "Bearer" or not token_valido(token):
        return None, JsonResponse({"error": "Credencial inválida"}, status=401)
    try:
        credenciales = mapa_credenciales(getattr(settings, "RANKING_CREDENCIALES_CENTRALES", "{}"))
    except RankingNoDisponible:
        return None, JsonResponse({"error": "Configuración no disponible"}, status=503)
    digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    jugador = credenciales.get(digest)
    if not jugador or len(jugador) > 150:
        return None, JsonResponse({"error": "Credencial inválida"}, status=401)
    return jugador, None


@require_GET
@never_cache
def consultar_ranking(request):
    jugador, error = acceso_central(request)
    if error is not None:
        return error
    try:
        lunes = semana_solicitada(request.GET.get("semana"))
    except ValueError:
        return JsonResponse({"error": "Semana inválida"}, status=400)

    return JsonResponse(resumir_semana(ResultadoRanking.objects.all(), "finalizada_en", lunes, jugador))


def resumir_semana(resultados, fecha_fin, lunes, jugador):
    inicio = datetime.combine(lunes, time.min, tzinfo=HUSO)
    siguiente = inicio + timedelta(days=7)
    filas = (
        resultados.filter(**{f"{fecha_fin}__gte": inicio, f"{fecha_fin}__lt": siguiente})
        .values("jugador")
        .annotate(puntos=Sum("puntaje"), victorias=Count("pk"), alcanzado_en=Max(fecha_fin))
        .order_by("-puntos", "-victorias", "alcanzado_en", "jugador")
    )
    ordenadas = list(filas) if jugador is not None else list(filas[:5])
    mejores = [{campo: fila[campo] for campo in ("jugador", "puntos", "victorias")} for fila in ordenadas[:5]]
    propia = next((i for i, fila in enumerate(ordenadas, 1) if fila["jugador"] == jugador), None)

    semanas = resultados.datetimes(fecha_fin, "week", order="DESC", tzinfo=HUSO)
    actual = lunes_actual()
    anteriores = [fecha.date().isoformat() for fecha in semanas if fecha.date() < actual]
    return {
        "inicio": lunes.isoformat(),
        "fin": siguiente.date() - timedelta(days=1),
        "mejores": mejores,
        "posicion": propia,
        "vinculado": jugador is not None,
        "anteriores": anteriores,
    }


def interpretar_resultado(request):
    campos = {"partida_id", "dificultad", "puntaje", "finalizada_en", "practica", "estado"}
    datos = leer_objeto_json(request, campos)
    if datos["practica"] is not False or datos["estado"] != Partida.Estado.GANADA:
        raise ValueError
    identificador = UUID(datos["partida_id"])
    if str(identificador) != datos["partida_id"]:
        raise ValueError
    nivel = NIVELES[datos["dificultad"]]
    puntaje = datos["puntaje"]
    if type(puntaje) is not int or not (
        100 * nivel["multiplicador"] <= puntaje <= (1000 + 5 * nivel["tiempo"]) * nivel["multiplicador"]
    ):
        raise ValueError
    fin = parse_datetime(datos["finalizada_en"])
    if fin is None or timezone.is_naive(fin) or fin.year < 2000 or fin > timezone.now():
        raise ValueError
    return identificador, {"dificultad": datos["dificultad"], "puntaje": puntaje, "finalizada_en": fin}


@csrf_exempt
@require_POST
@never_cache
def registrar_resultado(request):
    jugador, error = acceso_central(request, obligatorio=True)
    if error is not None:
        return error
    if request.content_type != "application/json":
        return JsonResponse({"error": "Se requiere JSON"}, status=415)
    try:
        identificador, datos = interpretar_resultado(request)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        return JsonResponse({"error": "Resultado inválido"}, status=400)
    datos["jugador"] = jugador
    resultado, creado = ResultadoRanking.objects.get_or_create(partida_id=identificador, defaults=datos)
    if not creado and any(getattr(resultado, campo) != valor for campo, valor in datos.items()):
        return JsonResponse({"error": "El identificador ya está registrado"}, status=409)
    return JsonResponse({"ok": True}, status=201 if creado else 200)


@login_required
@require_GET
@never_cache
def top_semanal(request):
    return mostrar_top_semanal(request, sincronizado=False)


@login_required
@require_GET
@never_cache
def top_sincronizado(request):
    return mostrar_top_semanal(request, sincronizado=True)


def mostrar_top_semanal(request, *, sincronizado):
    plantilla = "memory/top_semanal.html"
    contexto = {
        "sincronizado": sincronizado,
        "ruta_ranking": "memory:top_sincronizado" if sincronizado else "memory:top_semanal",
    }
    try:
        lunes = semana_solicitada(request.GET.get("semana"))
    except ValueError:
        contexto["semana_invalida"] = True
        return render(request, plantilla, contexto, status=400)

    contexto.update(inicio=lunes, fin=lunes + timedelta(days=6))
    if sincronizado:
        try:
            contexto["ranking"] = consultar_global(lunes, request.user.username)
        except RankingNoDisponible:
            contexto["no_disponible"] = True
    else:
        victorias = Partida.objects.filter(
            practica=False, estado=Partida.Estado.GANADA,
            fin_servidor__isnull=False, puntaje__gt=0,
        ).annotate(jugador=F("usuario__username"))
        contexto["ranking"] = resumir_semana(victorias, "fin_servidor", lunes, request.user.username)
    return render(request, plantilla, contexto)
