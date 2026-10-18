import random
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Movimiento, Partida, Personaje

NIVELES = {
    "FACIL": {
        "filas": 4,
        "columnas": 4,
        "parejas": 8,
        "tiempo": 150,
        "fallos": 16,
        "vista_previa": 3.0,
        "tiempo_fallo": 1.0,
        "multiplicador": 1.0,
    },

    "NORMAL": {
        "filas": 4,
        "columnas": 5,
        "parejas": 10,
        "tiempo": 150,
        "fallos": 15,
        "vista_previa": 1.5,
        "tiempo_fallo": 0.8,
        "multiplicador": 1.5,
    },

    "DIFICIL": {
        "filas": 6,
        "columnas": 6,
        "parejas": 18,
        "tiempo": 210,
        "fallos": 22,
        "vista_previa": 0,
        "tiempo_fallo": 0.6,
        "multiplicador": 2.0,
    },
}


def obtener_nivel(dificultad):
    dificultad = dificultad.upper()

    if dificultad not in NIVELES:
        raise ValueError("Dificultad no válida")

    return NIVELES[dificultad]

import random

from .models import Personaje


PERSONAJES_POR_NIVEL = {
    "FACIL": [
        "sonic",
        "tails",
        "knuckles",
        "amy",
        "shadow",
        "tangle",
        "whisper",
        "surge",
    ],

    "NORMAL": [
        "sonic",
        "tails",
        "knuckles",
        "amy",
        "shadow",
        "tangle",
        "whisper",
        "surge",
        "eggman",
        "kit",
    ],

    "DIFICIL": [
        "sonic",
        "tails",
        "knuckles",
        "amy",
        "shadow",
        "eggman",
        "rouge",
        "blaze",
        "silver",
        "metal-sonic",
        "tangle",
        "whisper",
        "surge",
        "kit",
        "belle",
        "lanolin",
        "mimic",
        "jewel",
    ],
}


def fisher_yates(lista, generador):
    resultado = lista.copy()

    for i in range(len(resultado) - 1, 0, -1):
        j = generador.randint(0, i)
        resultado[i], resultado[j] = resultado[j], resultado[i]

    return resultado


def crear_tablero(dificultad, semilla=None):
    dificultad = dificultad.upper()

    nivel = obtener_nivel(dificultad)

    if dificultad not in PERSONAJES_POR_NIVEL:
        raise ValueError("Dificultad no válida")

    claves = PERSONAJES_POR_NIVEL[dificultad]

    personajes = Personaje.objects.filter(
        clave__in=claves,
        activo=True
    )

    personajes_por_clave = {
        personaje.clave: personaje
        for personaje in personajes
    }

    faltantes = [
        clave
        for clave in claves
        if clave not in personajes_por_clave
    ]

    if faltantes:
        raise ValueError(
            f"Faltan personajes activos: {', '.join(faltantes)}"
        )

    cartas = []

    for clave in claves:
        cartas.append(clave)
        cartas.append(clave)

    if len(cartas) != nivel["filas"] * nivel["columnas"]:
        raise ValueError(
            "La cantidad de cartas no coincide con el tamaño del tablero"
        )

    if semilla is None:
        semilla = random.SystemRandom().randint(
            1,
            9_223_372_036_854_775_807
        )

    generador = random.Random(semilla)

    orden = fisher_yates(cartas, generador)

    estado_juego = {
        "orden": orden,
        "emparejadas": [],
        "visibles": [],
        "fallos": 0,
    }

    return estado_juego, semilla

from .models import Partida


def crear_partida(usuario, dificultad):
    dificultad = dificultad.upper()

    nivel = obtener_nivel(dificultad)

    Partida.objects.filter(
        usuario=usuario,
        estado=Partida.Estado.EN_CURSO
    ).update(
        estado=Partida.Estado.ABANDONADA
    )

    estado_juego, semilla = crear_tablero(dificultad)

    partida = Partida.objects.create(
        usuario=usuario,
        dificultad=dificultad,
        estado=Partida.Estado.EN_CURSO,
        limite_segundos=nivel["tiempo"],
        estado_juego=estado_juego,
        semilla=semilla,
    )

    return partida

@transaction.atomic
def voltear_carta(usuario, partida_id, posicion, seq_num):
    partida = Partida.objects.select_for_update().get(
        id=partida_id,
        usuario=usuario
    )

    movimiento_anterior = Movimiento.objects.filter(
        partida=partida,
        numero=seq_num
    ).first()

    if movimiento_anterior:
        return movimiento_anterior.datos

    if partida.estado != Partida.Estado.EN_CURSO:
        raise ValueError("La partida ya terminó")

    estado = dict(partida.estado_juego)

    orden = estado.get("orden", [])
    emparejadas = list(estado.get("emparejadas", []))
    visibles = list(estado.get("visibles", []))

    ahora = timezone.now()

    bloqueado_hasta = estado.get("bloqueado_hasta")

    if bloqueado_hasta:
        if ahora.timestamp() < bloqueado_hasta:
            raise ValueError(
                "Espera a que las cartas vuelvan a ocultarse"
            )

        estado["bloqueado_hasta"] = None

    try:
        posicion = int(posicion)
    except (TypeError, ValueError):
        raise ValueError("Posición inválida")

    if posicion < 0 or posicion >= len(orden):
        raise ValueError("Posición fuera del tablero")

    if posicion in emparejadas:
        raise ValueError("Esa carta ya fue emparejada")

    if posicion in visibles:
        raise ValueError("Esa carta ya está visible")

    clave = orden[posicion]

    personaje = Personaje.objects.get(
        clave=clave,
        activo=True
    )

    carta_actual = {
        "posicion": posicion,
        "clave": personaje.clave,
        "nombre": personaje.nombre,
        "imagen": personaje.imagen,
    }

    if len(visibles) == 0:
        estado["visibles"] = [posicion]

        respuesta = {
            "ok": True,
            "tipo": "primera",
            "carta": carta_actual,
        }

    else:
        primera_posicion = visibles[0]
        primera_clave = orden[primera_posicion]

        primer_personaje = Personaje.objects.get(
            clave=primera_clave,
            activo=True
        )

        primera_carta = {
            "posicion": primera_posicion,
            "clave": primer_personaje.clave,
            "nombre": primer_personaje.nombre,
            "imagen": primer_personaje.imagen,
        }

        es_pareja = primera_clave == clave

        estado["visibles"] = []

        if es_pareja:
            emparejadas.extend(
                [
                    primera_posicion,
                    posicion
                ]
            )

            estado["emparejadas"] = list(
                sorted(set(emparejadas))
            )

            respuesta = {
                "ok": True,
                "tipo": "pareja",
                "pareja": True,
                "cartas": [
                    primera_carta,
                    carta_actual
                ],
                "personaje": {
                    "clave": personaje.clave,
                    "nombre": personaje.nombre,
                    "descripcion": personaje.descripcion,
                    "frase": personaje.frase,
                    "origen": personaje.get_origen_display(),
                    "imagen": personaje.imagen,
                }
            }

        else:
            estado["fallos"] = (
                estado.get("fallos", 0) + 1
            )

            nivel = obtener_nivel(
                partida.dificultad
            )

            estado["bloqueado_hasta"] = (
                ahora
                + timedelta(
                    seconds=nivel["tiempo_fallo"]
                )
            ).timestamp()

            respuesta = {
                "ok": True,
                "tipo": "fallo",
                "pareja": False,
                "cartas": [
                    primera_carta,
                    carta_actual
                ],
                "fallos": estado["fallos"],
                "espera_ms": int(
                    nivel["tiempo_fallo"] * 1000
                )
            }

    partida.estado_juego = estado
    partida.errores = estado.get("fallos", 0)
    partida.movimientos += 1

    partida.save(
        update_fields=[
            "estado_juego",
            "errores",
            "movimientos"
        ]
    )

    Movimiento.objects.create(
        partida=partida,
        numero=seq_num,
        tipo="VOLTEAR",
        datos=respuesta,
        aceptado=True
    )

    return respuesta