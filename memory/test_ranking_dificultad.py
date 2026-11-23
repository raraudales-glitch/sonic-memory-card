from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Partida


class RankingPorDificultadTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username="jugador_test", password="prueba_segura_123")
        self.otro = get_user_model().objects.create_user(username="otro_test", password="prueba_segura_456")
        self.client.force_login(self.usuario)
        self.url = reverse("memory:top_semanal")
        zona = ZoneInfo("America/Tegucigalpa")
        hoy = timezone.localtime(timezone.now(), zona).date()
        self.inicio = hoy - timedelta(days=hoy.weekday())
        self.fecha = datetime.combine(self.inicio, time(12), tzinfo=zona)

    def crear_victoria(self, usuario, nivel, puntos, fecha=None):
        return Partida.objects.create(
            usuario=usuario,
            dificultad=nivel,
            estado="GANADA",
            puntaje=puntos,
            limite_segundos=150,
            fin_servidor=fecha or self.fecha,
        )

    def test_los_niveles_no_mezclan_los_puntos(self):
        self.crear_victoria(self.usuario, "FACIL", 1100)
        self.crear_victoria(self.usuario, "NORMAL", 2300)
        respuesta = self.client.get(self.url, {"nivel": "FACIL"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["mejores"][0]["puntos"], 1100)
        respuesta = self.client.get(self.url, {"nivel": "NORMAL"})
        self.assertEqual(respuesta.context["mejores"][0]["puntos"], 2300)
        respuesta = self.client.get(self.url, {"nivel": "DIFICIL"})
        self.assertEqual(respuesta.context["mejores"], [])

    def test_acumula_victorias_del_mismo_nivel(self):
        self.crear_victoria(self.usuario, "FACIL", 500)
        self.crear_victoria(self.usuario, "FACIL", 600)
        self.crear_victoria(self.otro, "FACIL", 700)
        respuesta = self.client.get(self.url, {"nivel": "FACIL"})
        self.assertEqual(respuesta.context["mejores"][0]["puntos"], 1100)
        self.assertEqual(respuesta.context["mejores"][0]["victorias"], 2)
        self.assertEqual(respuesta.context["posicion"], 1)

    def test_una_semana_no_contamina_a_otra(self):
        self.crear_victoria(self.usuario, "FACIL", 900, self.fecha - timedelta(days=7))
        self.crear_victoria(self.usuario, "FACIL", 600)
        respuesta = self.client.get(self.url, {"nivel": "FACIL"})
        self.assertEqual(respuesta.context["mejores"][0]["puntos"], 600)
        respuesta = self.client.get(self.url, {"nivel": "FACIL", "semana": (self.inicio - timedelta(days=7)).isoformat()})
        self.assertEqual(respuesta.context["mejores"][0]["puntos"], 900)

    def test_victoria_sin_puntos_no_esta_en_el_ranking(self):
        self.crear_victoria(self.usuario, "FACIL", 0)
        respuesta = self.client.get(self.url, {"nivel": "FACIL"})
        self.assertEqual(respuesta.context["mejores"], [])

    def test_la_tabla_tiene_cinco_puestos(self):
        for indice in range(7):
            usuario = get_user_model().objects.create_user(username=f"participante_{indice}")
            self.crear_victoria(usuario, "NORMAL", 1000 + indice)
        respuesta = self.client.get(self.url, {"nivel": "NORMAL"})
        self.assertEqual(len(respuesta.context["mejores"]), 5)
