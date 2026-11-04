import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .models import Partida
from .services import (
    ErrorJugada, abandonar_partida, consultar_partida, crear_partida,
    obtener_nivel, voltear_carta,
)


@login_required
def inicio(request):
    return render(request, "memory/inicio.html")


@login_required
@require_POST
def nueva_partida(request):
    try:
        datos = json.loads(request.body or "{}")
        if not isinstance(datos, dict):
            raise ValueError("El cuerpo debe ser un objeto JSON")
        dificultad = str(datos.get("dificultad", "")).upper()
        partida = crear_partida(request.user, dificultad)
        nivel = obtener_nivel(dificultad)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse({"ok": False, "error": str(error)}, status=400)

    return JsonResponse({"ok": True, "partida": {
        "id": str(partida.id), "dificultad": dificultad, "estado": partida.estado,
        "filas": nivel["filas"], "columnas": nivel["columnas"],
        "cantidad_cartas": nivel["filas"] * nivel["columnas"],
        "tiempo": nivel["tiempo"], "fallos_maximos": nivel["fallos"],
        "vista_previa": nivel["vista_previa"],
    }}, status=201)


@login_required
@require_GET
def jugar_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id, usuario=request.user)
    nivel = obtener_nivel(partida.dificultad)
    tapas = {
        "FACIL": "memory/images/tapa/Center_Card.png",
        "NORMAL": "memory/images/tapa/Chaos_Fruit.png",
        "DIFICIL": "memory/images/tapa/The_Master.png",
    }
    return render(request, "memory/partida.html", {
        "partida": partida,
        "nivel": nivel,
        "posiciones": range(nivel["filas"] * nivel["columnas"]),
        "imagen_tapa": tapas[partida.dificultad],
    })


@login_required
@require_GET
def estado_partida(request, partida_id):
    try:
        return JsonResponse(consultar_partida(request.user, partida_id))
    except Partida.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Partida no encontrada"}, status=404)


@login_required
@require_POST
def abandonar(request, partida_id):
    try:
        return JsonResponse(abandonar_partida(request.user, partida_id))
    except Partida.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Partida no encontrada"}, status=404)


@login_required
@require_POST
def voltear(request, partida_id):
    try:
        datos = json.loads(request.body or "{}")
        if not isinstance(datos, dict):
            return JsonResponse({"ok": False, "error": "El cuerpo debe ser un objeto JSON"}, status=400)
        respuesta = voltear_carta(request.user, partida_id, datos.get("posicion"), datos.get("seq_num"))
        return JsonResponse(respuesta, status=200 if respuesta.get("ok") else 409)
    except (TypeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)
    except ErrorJugada as error:
        return JsonResponse({"ok": False, "error": error.mensaje}, status=error.codigo)
    except Partida.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Partida no encontrada"}, status=404)
