
from django.urls import path
from . import views

app_name = "memory"

urlpatterns = [
    path(
        "",
        views.inicio,
        name="inicio"
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
