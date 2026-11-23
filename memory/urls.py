
from django.urls import path

from . import views
from .estadisticas import perfil_jugador
from .ranking import top_sincronizado
from .ranking_por_dificultad import top_semanal_por_dificultad
from . import paginas


app_name = "memory"


urlpatterns = [
    path("instrucciones/", paginas.instrucciones, name="instrucciones"),
    path("jugar/", views.seleccionar_dificultad, name="jugar"),
    path("historial/", paginas.historial, name="historial"),
    path("clasificacion/", paginas.clasificacion, name="clasificacion"),
    path("salud/", paginas.salud, name="salud"),
    path("partidas/<uuid:partida_id>/resultado/", paginas.resultado, name="resultado"),
    path("api/partidas/<uuid:partida_id>/estado/", views.estado_api, name="estado_api"),
    path("api/partidas/<uuid:partida_id>/accion/", views.voltear, name="accion_api"),
    path("api/partidas/<uuid:partida_id>/abandonar/", views.abandonar, name="abandonar_api"),
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

    path("top-semanal/", top_semanal_por_dificultad, name="top_semanal"),
    path("top-sincronizado/", top_sincronizado, name="top_sincronizado"),

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
