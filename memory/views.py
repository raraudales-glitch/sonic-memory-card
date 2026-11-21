
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Partida, Personaje
from .services import (
    ErrorJugada,
    abandonar_partida,
    confirmar_vencimiento,
    consultar_partida,
    crear_partida,
    obtener_nivel,
    segundos_previa_restantes,
    voltear_carta,
)


def leer_objeto_json(request, campos):
    def objeto_sin_duplicados(pares):
        objeto = dict(pares)
        if len(objeto) != len(pares):
            raise ValueError("El JSON contiene campos duplicados")
        return objeto

    datos = json.loads(request.body, object_pairs_hook=objeto_sin_duplicados)
    if not isinstance(datos, dict) or datos.keys() - campos:
        raise ValueError("El objeto JSON contiene campos inválidos")
    return datos


@login_required
@require_GET
def inicio(request):
    if request.GET.get("practica") == "1":
        return render(request, "memory/inicio.html", {"practica": True})

    partida = Partida.objects.filter(
        usuario=request.user,
        practica=False,
        estado=Partida.Estado.EN_CURSO,
    ).first()
    if partida:
        return redirect("memory:jugar_partida", partida_id=partida.id)

    return render(request, "memory/inicio.html")


@login_required
@require_GET
def seleccionar_dificultad(request):
    return render(request, "memory/inicio.html", {
        "practica": request.GET.get("practica") == "1",
    })


@login_required
@require_POST
def nueva_partida(request):
    try:
        datos = leer_objeto_json(request, {"dificultad", "practica"})
        dificultad = datos.get("dificultad")
        if not isinstance(dificultad, str):
            raise ValueError("Dificultad no válida")
        dificultad = dificultad.upper()

        practica = datos.get("practica", False)
        if not isinstance(practica, bool):
            raise ValueError("Modo de práctica inválido")

        partida = crear_partida(request.user, dificultad, practica=practica)

        nivel = obtener_nivel(dificultad)

    except (ValueError, RecursionError) as error:
        return JsonResponse(
            {"ok": False, "error": str(error)},
            status=400
        )

    return JsonResponse({
        "ok": True,
        "partida": {
            "id": str(partida.id),
            "dificultad": dificultad,
            "estado": partida.estado,
            "filas": nivel["filas"],
            "columnas": nivel["columnas"],
            "cantidad_cartas": (
                nivel["filas"] * nivel["columnas"]
            ),
            "tiempo": nivel["tiempo"],
            "fallos_maximos": nivel["fallos"],
            "vista_previa": nivel["vista_previa"],
        }
    }, status=201)


@login_required
@require_GET
@never_cache
def jugar_partida(request, partida_id):
    partida = get_object_or_404(
        Partida,
        id=partida_id,
        usuario=request.user
    )

    nivel = obtener_nivel(partida.dificultad)

    tapas = {
        "FACIL": "memory/images/tapa/Center_Card.png",
        "NORMAL": "memory/images/tapa/Chaos_Fruit.png",
        "DIFICIL": "memory/images/tapa/The_Master.png",
    }

    return render(
        request,
        "memory/partida.html",
        {
            "partida": partida,
            "nivel": nivel,
            "posiciones": range(
                nivel["filas"] * nivel["columnas"]
            ),
            "imagen_tapa": tapas[partida.dificultad],
        }
    )


@login_required
@require_POST
@never_cache
@transaction.atomic
def vista_previa(request, partida_id):
    partida = get_object_or_404(
        Partida.objects.select_for_update(),
        id=partida_id,
        usuario=request.user
    )

    nivel = obtener_nivel(partida.dificultad)
    ahora = timezone.now()

    transcurrido = (
        ahora - partida.inicio_servidor
    ).total_seconds()

    estado_juego = dict(partida.estado_juego)

    if (
        partida.estado == Partida.Estado.EN_CURSO
        and nivel["vista_previa"] > 0
        and transcurrido < partida.limite_segundos
        and partida.movimientos == 0
        and not estado_juego.get("vista_previa_inicio")
    ):
        estado_juego["vista_previa_inicio"] = (
            ahora.timestamp()
        )

        partida.estado_juego = estado_juego

        partida.save(
            update_fields=["estado_juego"]
        )

    restante = segundos_previa_restantes(
        partida,
        ahora
    )

    return JsonResponse({
        "ok": True,
        "activa": restante > 0,
        "restante_ms": int(restante * 1000),
        "cantidad_cartas": (
            nivel["filas"] * nivel["columnas"]
        ),
    })


@login_required
@require_GET
@never_cache
def carta_vista_previa(request, partida_id, posicion):
    partida = get_object_or_404(
        Partida,
        id=partida_id,
        usuario=request.user
    )

    if segundos_previa_restantes(
        partida,
        timezone.now()
    ) <= 0:
        return JsonResponse(
            {
                "ok": False,
                "error": "Vista previa terminada"
            },
            status=403
        )

    orden = partida.estado_juego.get(
        "orden",
        []
    )

    if not 0 <= posicion < len(orden):
        return JsonResponse(
            {
                "ok": False,
                "error": "Posición inválida"
            },
            status=400
        )

    personaje = Personaje.objects.filter(
        clave=orden[posicion],
        activo=True
    ).first()

    if personaje is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "Personaje no encontrado"
            },
            status=404
        )

    return JsonResponse({
        "ok": True,
        "posicion": posicion,
        "nombre": personaje.nombre,
        "imagen": personaje.imagen,
    })


@login_required
@require_http_methods(["GET", "POST"])
@never_cache
def estado_partida(request, partida_id):
    consultar = confirmar_vencimiento if request.method == "POST" else consultar_partida
    try:
        return JsonResponse(
            consultar(
                request.user,
                partida_id
            )
        )
    except Partida.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": "Partida no encontrada"
            },
            status=404
        )


@require_GET
def estado_api(request, partida_id):
    return estado_partida(request, partida_id)


@login_required
@require_POST
def abandonar(request, partida_id):
    try:
        datos = abandonar_partida(
            request.user,
            partida_id
        )

        return JsonResponse(datos)

    except Partida.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": "Partida no encontrada"
            },
            status=404
        )


@login_required
@require_POST
@never_cache
def voltear(request, partida_id):
    try:
        datos = leer_objeto_json(request, {"posicion", "seq_num"})

        respuesta = voltear_carta(
            request.user,
            partida_id,
            datos.get("posicion"),
            datos.get("seq_num")
        )

        return JsonResponse(
            respuesta,
            status=200 if respuesta.get("ok") else 409
        )

    except (ValueError, RecursionError):
        return JsonResponse(
            {
                "ok": False,
                "error": "JSON inválido"
            },
            status=400
        )

    except ErrorJugada as error:
        return JsonResponse(
            {
                "ok": False,
                "error": error.mensaje
            },
            status=error.codigo
        )

    except Partida.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "error": "Partida no encontrada"
            },
            status=404
        )
