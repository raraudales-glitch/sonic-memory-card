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
]