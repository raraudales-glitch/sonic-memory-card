import math
import random
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import Movimiento, Partida, Personaje

NIVELES = {
    "FACIL": {"filas": 4, "columnas": 4, "parejas": 8, "tiempo": 150, "fallos": 16, "vista_previa": 3.0, "tiempo_fallo": 1.0, "multiplicador": 1.0},
    "NORMAL": {"filas": 4, "columnas": 5, "parejas": 10, "tiempo": 150, "fallos": 15, "vista_previa": 1.5, "tiempo_fallo": 0.8, "multiplicador": 1.5},
    "DIFICIL": {"filas": 6, "columnas": 6, "parejas": 18, "tiempo": 210, "fallos": 22, "vista_previa": 0, "tiempo_fallo": 0.6, "multiplicador": 2.0},
}

PERSONAJES_POR_NIVEL = {
    "FACIL": ["sonic", "tails", "knuckles", "amy", "shadow", "tangle", "whisper", "surge"],
    "NORMAL": ["sonic", "tails", "knuckles", "amy", "shadow", "tangle", "whisper", "surge", "eggman", "kit"],
    "DIFICIL": ["sonic", "tails", "knuckles", "amy", "shadow", "eggman", "rouge", "blaze", "silver", "metal-sonic", "tangle", "whisper", "surge", "kit", "belle", "lanolin", "mimic", "jewel"],
}


class ErrorJugada(Exception):
    def __init__(self, mensaje, codigo=400):
        self.mensaje = mensaje
        self.codigo = codigo
        super().__init__(mensaje)


def obtener_nivel(dificultad):
    clave = str(dificultad).upper()
    if clave not in NIVELES:
        raise ValueError("Dificultad no válida")
    return NIVELES[clave]


def fisher_yates(lista, generador):
    cartas = list(lista)
    for i in range(len(cartas) - 1, 0, -1):
        j = generador.randint(0, i)
        cartas[i], cartas[j] = cartas[j], cartas[i]
    return cartas


def crear_tablero(dificultad):
    claves = PERSONAJES_POR_NIVEL[dificultad]
    presentes = set(Personaje.objects.filter(clave__in=claves, activo=True).values_list("clave", flat=True))
    faltantes = set(claves) - presentes
    if faltantes:
        raise ValueError("Faltan personajes: " + ", ".join(sorted(faltantes)))
    semilla = random.SystemRandom().randint(1, 2**63 - 1)
    return {
        "orden": fisher_yates([clave for clave in claves for _ in range(2)], random.Random(semilla)),
        "emparejadas": [],
        "visibles": [],
        "fallos": 0,
        "bloqueado_hasta": None,
    }, semilla


def tiempo_restante(partida, ahora=None):
    ahora = ahora or timezone.now()
    diferencia = (ahora - partida.inicio_servidor).total_seconds()
    return max(0, math.ceil(partida.limite_segundos - diferencia))


def cerrar_partida(partida, resultado, ahora=None):
    if partida.estado != Partida.Estado.EN_CURSO:
        return
    ahora = ahora or timezone.now()
    partida.estado = resultado
    partida.fin_servidor = ahora
    partida.duracion_segundos = max(0, int((ahora - partida.inicio_servidor).total_seconds()))
    if resultado == Partida.Estado.GANADA:
        nivel = obtener_nivel(partida.dificultad)
        restante = tiempo_restante(partida, ahora)
        base = max(100, 1000 + 5 * restante - 25 * partida.errores)
        calculo = Decimal(base) * Decimal(str(nivel["multiplicador"]))
        partida.puntaje = int(calculo.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    else:
        partida.puntaje = 0
    partida.save(update_fields=["estado", "fin_servidor", "duracion_segundos", "puntaje"])


def verificar_vencimiento(partida, ahora=None):
    ahora = ahora or timezone.now()
    segundos_transcurridos = (ahora - partida.inicio_servidor).total_seconds()
    # Dos segundos de tolerancia para solicitudes que ya estaban en tránsito.
    if partida.estado == Partida.Estado.EN_CURSO and segundos_transcurridos > partida.limite_segundos + 2:
        cerrar_partida(partida, Partida.Estado.TIEMPO_AGOTADO, ahora)
    return partida


def datos_carta(posicion, clave, catalogo):
    personaje = catalogo[clave]
    return {"posicion": posicion, "clave": personaje.clave, "nombre": personaje.nombre, "imagen": personaje.imagen}


def estado_publico(partida):
    nivel = obtener_nivel(partida.dificultad)
    estado = partida.estado_juego
    orden = estado.get("orden", [])
    posiciones = list(set(estado.get("emparejadas", []) + estado.get("visibles", [])))
    claves = {orden[i] for i in posiciones if 0 <= i < len(orden)}
    catalogo = Personaje.objects.in_bulk(claves, field_name="clave")
    cartas = [datos_carta(i, orden[i], catalogo) for i in sorted(posiciones) if 0 <= i < len(orden) and orden[i] in catalogo]
    return {
        "ok": True,
        "id": str(partida.id),
        "estado": partida.estado,
        "tiempo_restante": tiempo_restante(partida),
        "fallos": partida.errores,
        "fallos_maximos": nivel["fallos"],
        "parejas_encontradas": len(estado.get("emparejadas", [])) // 2,
        "parejas_objetivo": nivel["parejas"],
        "emparejadas": [c for c in cartas if c["posicion"] in estado.get("emparejadas", [])],
        "visibles": [c for c in cartas if c["posicion"] in estado.get("visibles", [])],
        "bloqueado_hasta": estado.get("bloqueado_hasta"),
        "ultima_secuencia": partida.movimientos,
        "puntaje": partida.puntaje,
    }


@transaction.atomic
def crear_partida(usuario, dificultad):
    dificultad = str(dificultad).upper()
    nivel = obtener_nivel(dificultad)
    get_user_model().objects.select_for_update().get(pk=usuario.pk)
    for anterior in Partida.objects.select_for_update().filter(usuario=usuario, estado=Partida.Estado.EN_CURSO):
        verificar_vencimiento(anterior)
        if anterior.estado == Partida.Estado.EN_CURSO:
            cerrar_partida(anterior, Partida.Estado.ABANDONADA)
    estado, semilla = crear_tablero(dificultad)
    return Partida.objects.create(usuario=usuario, dificultad=dificultad,
                                  limite_segundos=nivel["tiempo"], estado_juego=estado,
                                  semilla=semilla)


@transaction.atomic
def consultar_partida(usuario, partida_id):
    partida = Partida.objects.select_for_update().get(id=partida_id, usuario=usuario)
    verificar_vencimiento(partida)
    return estado_publico(partida)


@transaction.atomic
def abandonar_partida(usuario, partida_id):
    partida = Partida.objects.select_for_update().get(id=partida_id, usuario=usuario)
    verificar_vencimiento(partida)
    if partida.estado == Partida.Estado.EN_CURSO:
        cerrar_partida(partida, Partida.Estado.ABANDONADA)
    return estado_publico(partida)


@transaction.atomic
def voltear_carta(usuario, partida_id, posicion, seq_num):
    partida = Partida.objects.select_for_update().get(id=partida_id, usuario=usuario)
    try:
        seq_num = int(seq_num)
        posicion = int(posicion)
    except (ValueError, TypeError):
        raise ErrorJugada("Posición o secuencia inválida")
    if seq_num < 1:
        raise ErrorJugada("La secuencia debe ser positiva")

    anterior = Movimiento.objects.filter(partida=partida, numero=seq_num).first()
    if anterior:
        return anterior.datos

    verificar_vencimiento(partida)
    if partida.estado != Partida.Estado.EN_CURSO:
        return {"ok": False, "error": "La partida ya terminó", "estado": partida.estado, "tiempo_restante": 0, "puntaje": partida.puntaje}
    if seq_num != partida.movimientos + 1:
        raise ErrorJugada("Número de secuencia fuera de orden", 409)

    estado = dict(partida.estado_juego)
    orden = estado["orden"]
    emparejadas = list(estado.get("emparejadas", []))
    visibles = list(estado.get("visibles", []))
    ahora = timezone.now()
    if estado.get("bloqueado_hasta") and ahora.timestamp() < estado["bloqueado_hasta"]:
        raise ErrorJugada("Espera a que las cartas se oculten", 409)
    if not 0 <= posicion < len(orden):
        raise ErrorJugada("Posición fuera del tablero")
    if posicion in emparejadas or posicion in visibles:
        raise ErrorJugada("Esta carta ya está descubierta")

    estado["bloqueado_hasta"] = None
    claves = {orden[posicion]} | {orden[i] for i in visibles}
    catalogo = Personaje.objects.in_bulk(claves, field_name="clave")
    actual = datos_carta(posicion, orden[posicion], catalogo)

    if not visibles:
        estado["visibles"] = [posicion]
        respuesta = {"ok": True, "tipo": "primera", "carta": actual}
    else:
        primera = visibles[0]
        previa = datos_carta(primera, orden[primera], catalogo)
        es_pareja = orden[primera] == orden[posicion]
        estado["visibles"] = []
        if es_pareja:
            emparejadas.extend([primera, posicion])
            estado["emparejadas"] = sorted(set(emparejadas))
            personaje = catalogo[orden[posicion]]
            respuesta = {
                "ok": True, "tipo": "pareja", "pareja": True, "cartas": [previa, actual],
                "personaje": {"clave": personaje.clave, "nombre": personaje.nombre,
                              "descripcion": personaje.descripcion, "frase": personaje.frase,
                              "origen": personaje.get_origen_display(), "imagen": personaje.imagen},
            }
        else:
            estado["fallos"] = estado.get("fallos", 0) + 1
            segundos = obtener_nivel(partida.dificultad)["tiempo_fallo"]
            estado["bloqueado_hasta"] = (ahora + timedelta(seconds=segundos)).timestamp()
            respuesta = {"ok": True, "tipo": "fallo", "pareja": False,
                         "cartas": [previa, actual], "fallos": estado["fallos"],
                         "espera_ms": int(segundos * 1000)}

    partida.estado_juego = estado
    partida.errores = estado.get("fallos", 0)
    partida.movimientos += 1
    partida.save(update_fields=["estado_juego", "errores", "movimientos"])

    nivel = obtener_nivel(partida.dificultad)
    if len(estado.get("emparejadas", [])) == 2 * nivel["parejas"]:
        cerrar_partida(partida, Partida.Estado.GANADA, ahora)
    elif partida.errores > nivel["fallos"]:
        cerrar_partida(partida, Partida.Estado.PERDIDA, ahora)

    respuesta.update({"estado": partida.estado, "tiempo_restante": tiempo_restante(partida),
                      "puntaje": partida.puntaje, "fallos": partida.errores,
                      "parejas_encontradas": len(estado.get("emparejadas", [])) // 2})
    Movimiento.objects.create(partida=partida, numero=seq_num, tipo="VOLTEAR", datos=respuesta)
    return respuesta
