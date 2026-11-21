from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import DatabaseError, connections, router
from django.db.models import F, OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import Partida
from .services import NIVELES


@require_GET
def instrucciones(request):
    niveles = [(etiqueta, NIVELES[clave]) for clave, etiqueta in Partida.Dificultad.choices]
    return render(request, "memory/instrucciones.html", {"niveles": niveles})


@require_GET
def clasificacion(request):
    nivel = request.GET.get("nivel", "facil").upper()
    niveles = [(clave.lower(), etiqueta) for clave, etiqueta in Partida.Dificultad.choices]
    if nivel not in Partida.Dificultad.values:
        return render(request, "memory/clasificacion.html", {"niveles": niveles}, status=400)

    orden = ("-puntaje", "duracion_segundos", F("fin_servidor").asc(nulls_last=True), "id")
    ganadas = Partida.objects.filter(
        dificultad=nivel, estado=Partida.Estado.GANADA, practica=False,
    )
    mejor = ganadas.filter(usuario_id=OuterRef("usuario_id")).order_by(*orden)
    partidas = (
        ganadas.filter(pk=Subquery(mejor.values("pk")[:1]))
        .select_related("usuario__perfil")
        .order_by(*orden)[:10]
    )
    return render(request, "memory/clasificacion.html", {
        "nivel": nivel.lower(),
        "niveles": niveles,
        "partidas": partidas,
    })


@require_GET
@never_cache
def salud(request):
    try:
        with connections[router.db_for_read(Partida)].cursor() as cursor:
            cursor.execute("SELECT 1")
            disponible = cursor.fetchone() == (1,)
    except DatabaseError:
        disponible = False
    return JsonResponse({"ok": disponible}, status=200 if disponible else 503)


@login_required
@require_GET
@never_cache
def historial(request):
    partidas = Partida.objects.filter(usuario=request.user).order_by("-inicio_servidor", "-id")
    pagina = Paginator(partidas, 10).get_page(request.GET.get("pagina"))
    return render(request, "memory/historial.html", {"pagina": pagina})


@login_required
@require_GET
@never_cache
def resultado(request, partida_id):
    partida = get_object_or_404(Partida, pk=partida_id, usuario=request.user)
    if partida.estado == Partida.Estado.EN_CURSO:
        return redirect("memory:jugar_partida", partida_id=partida.pk)
    return render(request, "memory/resultado.html", {"partida": partida})
