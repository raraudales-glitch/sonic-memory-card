import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Partida, Personaje
from .services import NIVELES, PERSONAJES_POR_NIVEL


class ModoPracticaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username="jugador")
        Personaje.objects.bulk_create([
            Personaje(clave=clave, nombre=clave, origen=Personaje.Origen.VIDEOJUEGO)
            for clave in PERSONAJES_POR_NIVEL["DIFICIL"]
        ])

    def setUp(self):
        self.client.force_login(self.usuario)

    def crear(self, dificultad, **opciones):
        respuesta = self.client.post(
            reverse("memory:nueva_partida"),
            {"dificultad": dificultad, **opciones},
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 201)
        return Partida.objects.get(id=respuesta.json()["partida"]["id"])

    def jugar_parejas(self, partida):
        parejas = {}
        for posicion, clave in enumerate(partida.estado_juego["orden"]):
            parejas.setdefault(clave, []).append(posicion)
        url = reverse("memory:voltear", args=[partida.id])
        posiciones = [posicion for pareja in parejas.values() for posicion in pareja]
        for secuencia, posicion in enumerate(posiciones, start=1):
            respuesta = self.client.post(
                url,
                {"posicion": posicion, "seq_num": secuencia},
                content_type="application/json",
            )
            self.assertEqual(respuesta.status_code, 200)
        partida.refresh_from_db()
        self.assertEqual(partida.estado, Partida.Estado.GANADA)
        return respuesta.json()

    def test_practica_en_las_tres_dificultades(self):
        inicio = reverse("memory:inicio")
        self.assertContains(self.client.get(inicio), 'id="modo-practica"')

        for dificultad, nivel in NIVELES.items():
            with self.subTest(dificultad=dificultad):
                partida = self.crear(dificultad, practica=True)
                tablero = self.client.get(reverse("memory:jugar_partida", args=[partida.id]))
                self.assertContains(tablero, 'data-practica="true"')
                self.assertContains(tablero, 'class="carta"', count=2 * nivel["parejas"])
                previa = self.client.get(reverse("memory:vista_previa", args=[partida.id]))
                self.assertEqual(previa.json()["activa"], nivel["vista_previa"] > 0)
                self.assertEqual(self.jugar_parejas(partida)["puntaje"], 0)
                self.assertEqual(partida.puntaje, 0)

        perfil = self.client.get(reverse("memory:perfil")).context
        self.assertEqual(perfil["total"], 0)
        self.assertEqual(perfil["victorias"], 0)
        self.assertEqual(perfil["mejor_puntaje"], 0)
        self.assertTrue(all(nivel["total"] == 0 for nivel in perfil["niveles"]))

    def test_practica_y_partida_oficial_coexisten(self):
        oficial = self.crear("FACIL")
        primera = self.crear("NORMAL", practica=True)
        segunda = self.crear("DIFICIL", practica=True)
        primera.refresh_from_db()
        oficial.refresh_from_db()
        self.assertEqual(primera.estado, Partida.Estado.ABANDONADA)
        self.assertEqual(oficial.estado, Partida.Estado.EN_CURSO)

        self.client.get(reverse("memory:jugar_partida", args=[segunda.id]))
        inicio = reverse("memory:inicio")
        self.assertContains(self.client.get(inicio + "?practica=1"), 'id="modo-practica" checked')
        self.assertRedirects(
            self.client.get(inicio),
            reverse("memory:jugar_partida", args=[oficial.id]),
            fetch_redirect_response=False,
        )
        perfil_url = reverse("memory:perfil")
        self.assertEqual(self.client.get(perfil_url).context["partidas_activas"], 1)

        self.assertGreater(self.jugar_parejas(oficial)["puntaje"], 0)
        Partida.objects.filter(id=segunda.id).update(
            inicio_servidor=timezone.now() - timedelta(seconds=segunda.limite_segundos + 3)
        )
        estado = self.client.get(reverse("memory:estado_partida", args=[segunda.id])).json()
        self.assertEqual(estado["estado"], Partida.Estado.TIEMPO_AGOTADO)
        self.assertEqual(estado["puntaje"], 0)
        perfil = self.client.get(perfil_url).context
        self.assertEqual(perfil["total"], 1)
        self.assertEqual(perfil["derrotas"], 0)
        self.assertEqual(perfil["mejor_puntaje"], oficial.puntaje)

    def test_modo_invalido_no_crea_partida(self):
        respuesta = self.client.post(
            reverse("memory:nueva_partida"),
            json.dumps({"dificultad": "FACIL", "practica": "false"}),
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Partida.objects.exists())
