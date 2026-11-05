
from django.urls import path

from . import views
from .estadisticas import perfil_jugador


app_name = "memory"


urlpatterns = [
    path(
        "",
        views.inicio,
        name="inicio"
    ),

    path(
        "perfil/",
        perfil_jugador,
        name="perfil"
    ),

    path(
        "partidas/nueva/",
        views.nueva_partida,
        name="nueva_partida"
    ),

    path(
        "partidas/<uuid:partida_id>/",
        views.jugar_partida,
        name="jugar_partida"
    ),

    path(
        "partidas/<uuid:partida_id>/vista-previa/",
        views.vista_previa,
        name="vista_previa"
    ),

    path(
        "partidas/<uuid:partida_id>/vista-previa/<int:posicion>/",
        views.carta_vista_previa,
        name="carta_vista_previa"
    ),

    path(
        "partidas/<uuid:partida_id>/voltear/",
        views.voltear,
        name="voltear"
    ),

    path(
        "partidas/<uuid:partida_id>/estado/",
        views.estado_partida,
        name="estado_partida"
    ),

    path(
        "partidas/<uuid:partida_id>/abandonar/",
        views.abandonar,
        name="abandonar"
    ),
]
