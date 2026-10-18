from django.contrib import admin

from .models import Movimiento, Partida, PerfilJugador, Personaje


@admin.register(PerfilJugador)
class PerfilJugadorAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "alias",
        "volumen_musica",
        "volumen_efectos",
        "silenciado",
    )

    search_fields = (
        "usuario__username",
        "alias",
    )


@admin.register(Personaje)
class PersonajeAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "clave",
        "origen",
        "activo",
    )

    list_filter = (
        "origen",
        "activo",
    )

    search_fields = (
        "nombre",
        "clave",
        "descripcion",
    )


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "dificultad",
        "estado",
        "puntaje",
        "errores",
        "inicio_servidor",
    )

    list_filter = (
        "dificultad",
        "estado",
    )

    search_fields = (
        "usuario__username",
        "id",
    )

    readonly_fields = (
        "id",
        "inicio_servidor",
    )


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "partida",
        "numero",
        "tipo",
        "aceptado",
        "creado_en",
    )

    list_filter = (
        "tipo",
        "aceptado",
    )

    search_fields = (
        "partida__usuario__username",
        "partida__id",
    )

    readonly_fields = (
        "creado_en",
    )