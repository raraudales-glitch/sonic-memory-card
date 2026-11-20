
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Case, Count, F, IntegerField, Max, Q, When
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import Partida, PerfilJugador
from .services import partida_vencida


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
@require_GET
def perfil_jugador(request):

    usuario = request.user

    alias = PerfilJugador.objects.filter(usuario=usuario).values_list("alias", flat=True).first()

    nombre = (
        usuario.get_full_name().strip()
        or alias
        or usuario.username
    )

    oficiales = Partida.objects.filter(usuario=usuario, practica=False)
    activa = oficiales.filter(estado=Partida.Estado.EN_CURSO).first()
    ahora = timezone.now()
    vencida = activa is not None and partida_vencida(activa, ahora)

    finales = Q(estado__in=ESTADOS_FINALES)
    derrotadas = Q(estado__in=[Partida.Estado.PERDIDA, Partida.Estado.TIEMPO_AGOTADO, Partida.Estado.ABANDONADA])
    duracion = F("duracion_segundos")
    if vencida:
        pendiente = Q(pk=activa.pk, estado=Partida.Estado.EN_CURSO)
        finales |= pendiente
        derrotadas |= pendiente
        duracion = Case(
            When(pendiente, then=int((ahora - activa.inicio_servidor).total_seconds())),
            default=duracion,
            output_field=IntegerField(),
        )

    partidas = oficiales.filter(finales)

    resumen = partidas.aggregate(
        total=Count("id"),

        victorias=Count(
            "id",
            filter=Q(estado="GANADA")
        ),

        derrotas=Count(
            "id",
            filter=derrotadas
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
                duracion
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
        "partidas_activas": int(activa is not None and not vencida),
        "niveles": niveles,
    }

    return render(
        request,
        "memory/perfil.html",
        contexto
    )
