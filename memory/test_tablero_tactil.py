import json
import os
import subprocess
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from urllib.request import urlopen

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

from .models import Movimiento
from .test_auditoria_partidas import crear, ruta


@override_settings(SECURE_SSL_REDIRECT=False)
class TableroTactilTests(StaticLiveServerTestCase):
    def setUp(self):
        binario = os.environ.get("CHROMIUM_BIN")
        if not binario:
            self.skipTest("Define CHROMIUM_BIN para ejecutar la prueba táctil")
        from websocket import create_connection

        perfil = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(perfil.cleanup)
        navegador = subprocess.Popen([
            binario, "--headless=new", "--no-first-run", "--disable-background-networking", "--disable-gpu",
            "--remote-debugging-port=0", f"--user-data-dir={perfil.name}", "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self.cerrar, navegador)
        puerto = Path(perfil.name) / "DevToolsActivePort"
        self.esperar(puerto.exists)
        with urlopen(f"http://127.0.0.1:{puerto.read_text().splitlines()[0]}/json/list", timeout=5) as respuesta:
            destino = next(p for p in json.load(respuesta) if p["type"] == "page")
        self.conexion = create_connection(destino["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
        self.addCleanup(self.conexion.close)
        self.comando_id = 0
        call_command("cargar_personajes", stdout=StringIO())
        self.client.force_login(get_user_model().objects.create_user(username="tactil"))
        cookie = self.client.cookies["sessionid"]
        self.cdp("Network.setCookie", name=cookie.key, value=cookie.value, url=self.live_server_url)
        self.cdp("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=1)

    @staticmethod
    def cerrar(navegador):
        navegador.terminate()
        navegador.wait(timeout=10)

    def cdp(self, metodo, **parametros):
        self.comando_id += 1
        self.conexion.send(json.dumps({"id": self.comando_id, "method": metodo, "params": parametros}))
        while True:
            respuesta = json.loads(self.conexion.recv())
            if respuesta.get("id") == self.comando_id:
                self.assertNotIn("error", respuesta)
                return respuesta["result"]

    def js(self, expresion):
        resultado = self.cdp("Runtime.evaluate", expression=expresion, returnByValue=True)
        self.assertNotIn("exceptionDetails", resultado)
        return resultado["result"].get("value")

    def esperar(self, condicion, segundos=12):
        limite = monotonic() + segundos
        while monotonic() < limite:
            if condicion():
                return
            sleep(0.05)
        self.fail("La condición no se cumplió a tiempo")

    def abrir(self, partida, ancho):
        self.cdp("Emulation.setDeviceMetricsOverride", mobile=True, width=ancho, height=800, deviceScaleFactor=2)
        url = self.live_server_url + ruta("jugar_partida", partida)
        self.cdp("Page.navigate", url=url)
        self.esperar(lambda: self.js(
            f"location.href === {json.dumps(url)} && !!document.querySelector('.carta[aria-disabled=false]')"
        ))

    def tocar(self, posicion):
        selector = f".carta[data-posicion='{posicion}']"
        x, y = self.js(f"""(() => {{
            const carta = document.querySelector("{selector}");
            carta.scrollIntoView({{block: 'center'}});
            const rect = carta.getBoundingClientRect();
            return [rect.x + rect.width / 2, rect.y + rect.height / 2];
        }})()""")
        self.cdp("Input.dispatchTouchEvent", type="touchStart", touchPoints=[{"x": x, "y": y}])
        self.cdp("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def cantidad(self, selector):
        return self.js(f"document.querySelectorAll({json.dumps(selector)}).length")

    def test_cuadriculas_y_toques_en_cuatro_anchos(self):
        self.cdp("Emulation.setCPUThrottlingRate", rate=4)
        for ancho in (360, 375, 390, 430):
            for dificultad, total in (("FACIL", 16), ("NORMAL", 20), ("DIFICIL", 36)):
                with self.subTest(ancho=ancho, dificultad=dificultad):
                    partida = crear(self.client, dificultad)
                    self.abrir(partida, ancho)
                    self.assertEqual(self.cantidad(".carta"), total)
                    self.assertTrue(self.js("""[...document.querySelectorAll('.carta')].every(carta => {
                        const r = carta.getBoundingClientRect();
                        return r.left >= 0 && r.right <= innerWidth && r.width >= 40;
                    })"""))
                    self.tocar(total - 1)
                    self.esperar(lambda: self.js(
                        "document.querySelector('.carta.volteada .carta-personaje')?.naturalWidth > 0"
                    ))
                    self.assertEqual(self.cantidad(".carta.volteada"), 1)
                    self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 1)

    def test_toques_rapidos_timeout_y_reintento_idempotente(self):
        partida = crear(self.client, "DIFICIL")
        orden = partida.estado_juego["orden"]
        pareja = orden.index(orden[0], 1)
        distinta = next(i for i, clave in enumerate(orden) if clave != orden[0])
        self.abrir(partida, 390)
        self.js("""(() => {
            const original = window.fetch;
            window.intentos = [];
            window.fetch = async (url, opciones) => {
                if (!url.endsWith('/accion/')) return original(url, opciones);
                intentos.push(JSON.parse(opciones.body));
                const respuesta = await original(url, opciones);
                if (intentos.length !== 1) return respuesta;
                return new Promise((_, rechazar) => opciones.signal.addEventListener(
                    'abort', () => rechazar(opciones.signal.reason), {once: true}
                ));
            };
        })()""")
        self.tocar(0)
        self.tocar(pareja)
        self.tocar(distinta)
        self.assertEqual(self.cantidad(".carta.pendiente"), 2)
        self.assertEqual(self.cantidad(".carta.volteada"), 0)
        self.esperar(lambda: self.js("!document.querySelector('#reintentar-jugada').hidden"))
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 1)
        self.js("document.querySelector('#reintentar-jugada').click()")
        self.esperar(lambda: self.cantidad(".carta.emparejada") == 2)
        self.tocar(0)
        self.assertEqual(self.js("intentos"), [
            {"posicion": 0, "seq_num": 1},
            {"posicion": 0, "seq_num": 1},
            {"posicion": pareja, "seq_num": 2},
        ])
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 2)

        self.tocar(distinta)
        self.esperar(lambda: self.cantidad(".carta.volteada") == 3)
        segunda = next(i for i, clave in enumerate(orden) if i not in (0, pareja) and clave != orden[distinta])
        tercera = next(i for i in range(len(orden)) if i not in (0, pareja, distinta, segunda))
        self.tocar(segunda)
        self.esperar(lambda: self.cantidad(".carta.volteada") == 4)
        self.tocar(tercera)
        self.esperar(lambda: self.cantidad(".carta.volteada") == 2)
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 4)
        self.assertEqual(self.cantidad(".carta[aria-disabled=false]"), 34)
