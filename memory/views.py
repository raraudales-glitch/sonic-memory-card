
import json
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import Partida, Personaje
from .services import (
    ErrorJugada,
    abandonar_partida,
    consultar_partida,
    crear_partida,
    obtener_nivel,
    voltear_carta,
)


CLAVE_PARTIDA = "sonic_partida_pendiente"


@login_required
def inicio(request):
    referencia = request.session.get(CLAVE_PARTIDA)
    partida = None

    if referencia:
        try:
            identificador = UUID(str(referencia))
        except (TypeError, ValueError, AttributeError):
            request.session.pop(CLAVE_PARTIDA, None)
        else:
            partida = Partida.objects.filter(
                id=identificador,
                usuario=request.user,
            ).first()

            if partida is None:
                request.session.pop(CLAVE_PARTIDA, None)

    if partida is None:
        partida = Partida.objects.filter(
            usuario=request.user,
            estado=Partida.Estado.EN_CURSO,
        ).order_by("-inicio_servidor").first()

    if partida:
        if partida.estado == Partida.Estado.EN_CURSO:
            try:
                datos = consultar_partida(
                    request.user,
                    partida.id
                )
            except Partida.DoesNotExist:
                request.session.pop(CLAVE_PARTIDA, None)
            else:
                if datos.get("estado") in {
                    Partida.Estado.EN_CURSO,
                    Partida.Estado.TIEMPO_AGOTADO,
                }:
                    if datos["estado"] == Partida.Estado.EN_CURSO:
                        request.session[CLAVE_PARTIDA] = str(
                            partida.id
                        )
                    else:
                        request.session.pop(
                            CLAVE_PARTIDA,
                            None
                        )

                    return redirect(
                        "memory:jugar_partida",
                        partida_id=partida.id
                    )

                request.session.pop(CLAVE_PARTIDA, None)

        elif partida.estado == Partida.Estado.TIEMPO_AGOTADO:
            request.session.pop(CLAVE_PARTIDA, None)

            return redirect(
                "memory:jugar_partida",
                partida_id=partida.id
            )
        else:
            request.session.pop(CLAVE_PARTIDA, None)

    return render(request, "memory/inicio.html")


@login_required
@require_POST
def nueva_partida(request):
    try:
        datos = json.loads(request.body or "{}")

        if not isinstance(datos, dict):
            raise ValueError(
                "El cuerpo debe ser un objeto JSON"
            )

        dificultad = str(
            datos.get("dificultad", "")
        ).upper()

        partida = crear_partida(
            request.user,
            dificultad
        )

        nivel = obtener_nivel(dificultad)

    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse(
            {"ok": False, "error": str(error)},
            status=400
        )

    request.session[CLAVE_PARTIDA] = str(partida.id)

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
def jugar_partida(request, partida_id):
    partida = get_object_or_404(
        Partida,
        id=partida_id,
        usuario=request.user
    )

    if partida.estado == Partida.Estado.EN_CURSO:
        consultar_partida(
            request.user,
            partida.id
        )

        partida.refresh_from_db()

        if partida.estado == Partida.Estado.EN_CURSO:
            request.session[CLAVE_PARTIDA] = str(
                partida.id
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


def segundos_previa_restantes(partida, ahora):
    nivel = obtener_nivel(partida.dificultad)

    marca = partida.estado_juego.get(
        "vista_previa_inicio"
    )

    if (
        partida.estado != Partida.Estado.EN_CURSO
        or not marca
        or partida.movimientos > 0
    ):
        return 0

    transcurrido = (
        ahora - partida.inicio_servidor
    ).total_seconds()

    if transcurrido >= partida.limite_segundos:
        return 0

    return max(
        0,
        min(
            float(nivel["vista_previa"]) -
            (ahora.timestamp() - float(marca)),
            partida.limite_segundos - transcurrido,
        )
    )


@login_required
@require_GET
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
@require_GET
def estado_partida(request, partida_id):
    try:
        return JsonResponse(
            consultar_partida(
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


@login_required
@require_POST
def abandonar(request, partida_id):
    try:
        datos = abandonar_partida(
            request.user,
            partida_id
        )

        if str(
            request.session.get(CLAVE_PARTIDA)
        ) == str(partida_id):
            request.session.pop(
                CLAVE_PARTIDA,
                None
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
def voltear(request, partida_id):
    try:
        datos = json.loads(request.body or "{}")

        if not isinstance(datos, dict):
            return JsonResponse(
                {
                    "ok": False,
                    "error": "El cuerpo debe ser un objeto JSON"
                },
                status=400
            )

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

    except (TypeError, json.JSONDecodeError):
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
