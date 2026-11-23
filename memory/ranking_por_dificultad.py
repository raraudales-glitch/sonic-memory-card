from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Sum
from django.db.models.functions import TruncWeek
from django.shortcuts import render
from django.utils import timezone

from .models import Partida


ZONA = ZoneInfo("America/Tegucigalpa")
NIVELES = (
    ("FACIL", "Fácil"),
    ("NORMAL", "Normal"),
    ("DIFICIL", "Difícil"),
)


def partidas_oficiales():
    partidas = Partida.objects.filter(estado="GANADA", puntaje__gt=0, fin_servidor__isnull=False)
    campos = {campo.name: campo for campo in Partida._meta.concrete_fields}

    for nombre in ("es_practica", "modo_practica", "practica"):
        if nombre in campos and campos[nombre].get_internal_type() == "BooleanField":
            return partidas.filter(**{nombre: False})

    if "es_oficial" in campos and campos["es_oficial"].get_internal_type() == "BooleanField":
        return partidas.filter(es_oficial=True)

    if "modo" in campos:
        opciones = dict(campos["modo"].flatchoices)
        valores = {str(valor).upper(): valor for valor in opciones}
        if "OFICIAL" in valores:
            return partidas.filter(modo=valores["OFICIAL"])

    return partidas


@login_required
def top_semanal_por_dificultad(request):
    nivel = request.GET.get("nivel", "FACIL").strip().upper()
    if nivel not in dict(NIVELES):
        nivel = "FACIL"

    hoy = timezone.localtime(timezone.now(), ZONA).date()
    semana_actual = hoy - timedelta(days=hoy.weekday())
    semana_param = request.GET.get("semana", "").strip()
    semana_invalida = False

    if semana_param:
        try:
            inicio = date.fromisoformat(semana_param)
            if inicio.weekday() != 0 or inicio > semana_actual:
                raise ValueError
        except ValueError:
            inicio = semana_actual
            semana_invalida = True
    else:
        inicio = semana_actual

    fin_exclusivo = inicio + timedelta(days=7)
    inicio_dt = datetime.combine(inicio, time.min, tzinfo=ZONA)
    fin_dt = datetime.combine(fin_exclusivo, time.min, tzinfo=ZONA)

    oficiales = partidas_oficiales().filter(dificultad=nivel)
    resultados = oficiales.filter(fin_servidor__gte=inicio_dt, fin_servidor__lt=fin_dt)
    acumulados = resultados.values("usuario_id", "usuario__username").annotate(
        puntos=Sum("puntaje"),
        victorias=Count("pk"),
        logrado_en=Max("fin_servidor"),
    ).order_by("-puntos", "-victorias", "logrado_en", "usuario__username")

    mejores = []
    posicion = None
    for numero, fila in enumerate(acumulados, start=1):
        if numero <= 5:
            mejores.append({
                "puesto": numero,
                "jugador": fila["usuario__username"],
                "puntos": fila["puntos"],
                "victorias": fila["victorias"],
            })
        if fila["usuario_id"] == request.user.pk:
            posicion = numero

    fechas = oficiales.filter(fin_servidor__lt=inicio_dt).annotate(
        semana=TruncWeek("fin_servidor", tzinfo=ZONA)
    ).values_list("semana", flat=True).distinct().order_by("-semana")[:16]
    anteriores = [fecha.date().isoformat() for fecha in fechas if fecha]

    historico = partidas_oficiales().filter(
        fin_servidor__gte=inicio_dt,
        fin_servidor__lt=fin_dt,
    ).values("usuario_id", "usuario__username").annotate(
        puntos=Sum("puntaje"),
        victorias=Count("pk"),
        logrado_en=Max("fin_servidor"),
    ).order_by("-puntos", "-victorias", "logrado_en", "usuario__username")

    mejores_generales = []
    posicion_general = None
    for numero, fila in enumerate(historico, start=1):
        if numero <= 5:
            mejores_generales.append({
                "jugador": fila["usuario__username"],
                "puntos": fila["puntos"],
                "victorias": fila["victorias"],
            })
        if fila["usuario_id"] == request.user.pk:
            posicion_general = numero

    ranking_compatible = {
        "mejores": mejores_generales,
        "posicion": posicion_general,
        "vinculado": True,
        "anteriores": anteriores,
        "inicio": inicio.isoformat(),
    }

    return render(request, "memory/top_semanal_niveles.html", {
        "niveles_ranking": NIVELES,
        "nivel": nivel,
        "nombre_nivel": dict(NIVELES)[nivel],
        "inicio": inicio,
        "fin": fin_exclusivo - timedelta(days=1),
        "semana_param": inicio.isoformat(),
        "semana_invalida": semana_invalida,
        "mejores": mejores,
        "ranking": ranking_compatible,
        "posicion": posicion,
        "anteriores": anteriores,
    })
