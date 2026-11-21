from django.urls import path

from memory.ranking import consultar_ranking, registrar_resultado


urlpatterns = [
    path("api/ranking/semanal/", consultar_ranking, name="ranking_semanal_global"),
    path("api/ranking/resultados/", registrar_resultado, name="registrar_resultado_global"),
]
