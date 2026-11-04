
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Q
from django.shortcuts import render

from .models import Partida, PerfilJugador
from .services import consultar_partida


ESTADOS_FINALES = [
    "GANADA",
    "PERDIDA",
    "TIEMPO_AGOTADO",
    "ABANDONADA",
]

DIFICULTADES = [
    ("FACIL", "Fácil"),
    ("NORMAL", "Normal"),
    ("DIFICIL", "Difícil"),
]


@login_required
def perfil_jugador(request):

    usuario = request.user

    perfil, creado = PerfilJugador.objects.get_or_create(
        usuario=usuario,
        defaults={
            "alias": usuario.username
        }
    )

    nombre = (
        usuario.get_full_name().strip()
        or perfil.alias
        or usuario.username
    )

    partidas_activas = Partida.objects.filter(
        usuario=usuario,
        estado="EN_CURSO"
    )

    for partida_id in list(
        partidas_activas.values_list("id", flat=True)
    ):
        consultar_partida(usuario, partida_id)

    partidas = Partida.objects.filter(
        usuario=usuario,
        estado__in=ESTADOS_FINALES
    )

    resumen = partidas.aggregate(
        total=Count("id"),

        victorias=Count(
            "id",
            filter=Q(estado="GANADA")
        ),

        derrotas=Count(
            "id",
            filter=Q(
                estado__in=[
                    "PERDIDA",
                    "TIEMPO_AGOTADO",
                    "ABANDONADA",
                ]
            )
        ),

        mejor_puntaje=Max(
            "puntaje",
            filter=Q(estado="GANADA")
        ),
    )

    total = resumen["total"] or 0
    victorias = resumen["victorias"] or 0
    derrotas = resumen["derrotas"] or 0
    mejor_puntaje = resumen["mejor_puntaje"] or 0

    porcentaje_victorias = (
        round((victorias / total) * 100, 1)
        if total > 0
        else 0
    )

    niveles = []

    for codigo, nombre_nivel in DIFICULTADES:

        datos = partidas.filter(
            dificultad=codigo
        ).aggregate(
            total=Count("id"),

            victorias=Count(
                "id",
                filter=Q(estado="GANADA")
            ),

            mejor_puntaje=Max(
                "puntaje",
                filter=Q(estado="GANADA")
            ),

            tiempo_promedio=Avg(
                "duracion_segundos"
            ),
        )

        total_nivel = datos["total"] or 0
        victorias_nivel = datos["victorias"] or 0

        niveles.append({
            "nombre": nombre_nivel,
            "total": total_nivel,
            "victorias": victorias_nivel,
            "derrotas": total_nivel - victorias_nivel,
            "mejor_puntaje": (
                datos["mejor_puntaje"] or 0
            ),
            "tiempo_promedio": (
                round(datos["tiempo_promedio"], 1)
                if datos["tiempo_promedio"] is not None
                else None
            ),
        })

    contexto = {
        "nombre": nombre,
        "correo": (
            usuario.email or "Sin correo registrado"
        ),
        "username": usuario.username,
        "total": total,
        "victorias": victorias,
        "derrotas": derrotas,
        "mejor_puntaje": mejor_puntaje,
        "porcentaje_victorias": porcentaje_victorias,
        "partidas_activas": Partida.objects.filter(
            usuario=usuario,
            estado="EN_CURSO"
        ).count(),
        "niveles": niveles,
    }

    return render(
        request,
        "memory/perfil.html",
        contexto
    )
