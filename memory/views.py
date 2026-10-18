import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Partida
from .services import (
    crear_partida,
    obtener_nivel,
    voltear_carta,
)


@login_required
def inicio(request):
    return render(
        request,
        "memory/inicio.html"
    )


@login_required
@require_POST
def nueva_partida(request):
    try:
        datos = json.loads(request.body or "{}")

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "ok": False,
                "error": "JSON inválido"
            },
            status=400
        )

    dificultad = datos.get(
        "dificultad",
        ""
    ).upper()

    if dificultad not in [
        "FACIL",
        "NORMAL",
        "DIFICIL"
    ]:
        return JsonResponse(
            {
                "ok": False,
                "error": "Dificultad no válida"
            },
            status=400
        )

    try:
        partida = crear_partida(
            request.user,
            dificultad
        )

        nivel = obtener_nivel(
            dificultad
        )

    except ValueError as error:
        return JsonResponse(
            {
                "ok": False,
                "error": str(error)
            },
            status=400
        )

    return JsonResponse(
        {
            "ok": True,

            "partida": {
                "id": str(partida.id),

                "dificultad":
                    partida.dificultad,

                "estado":
                    partida.estado,

                "filas":
                    nivel["filas"],

                "columnas":
                    nivel["columnas"],

                "cantidad_cartas":
                    nivel["filas"]
                    * nivel["columnas"],

                "tiempo":
                    nivel["tiempo"],

                "fallos_maximos":
                    nivel["fallos"],

                "vista_previa":
                    nivel["vista_previa"],
            }
        },
        status=201
    )


@login_required
def jugar_partida(
    request,
    partida_id
):
    partida = get_object_or_404(
        Partida,
        id=partida_id,
        usuario=request.user
    )

    nivel = obtener_nivel(
        partida.dificultad
    )

    cantidad_cartas = (
        nivel["filas"]
        * nivel["columnas"]
    )

    contexto = {
        "partida": partida,
        "nivel": nivel,
        "posiciones": range(
            cantidad_cartas
        ),
    }

    return render(
        request,
        "memory/partida.html",
        contexto
    )


@login_required
@require_POST
def voltear(
    request,
    partida_id
):
    try:
        datos = json.loads(
            request.body or "{}"
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "ok": False,
                "error": "JSON inválido"
            },
            status=400
        )

    posicion = datos.get(
        "posicion"
    )

    seq_num = datos.get(
        "seq_num"
    )

    if posicion is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "Falta posición"
            },
            status=400
        )

    if seq_num is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "Falta seq_num"
            },
            status=400
        )

    try:
        seq_num = int(
            seq_num
        )

        respuesta = voltear_carta(
            request.user,
            partida_id,
            posicion,
            seq_num
        )

        return JsonResponse(
            respuesta
        )

    except Partida.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error":
                    "Partida no encontrada"
            },
            status=404
        )

    except (ValueError, TypeError) as error:
        return JsonResponse(
            {
                "ok": False,
                "error": str(error)
            },
            status=400
        )