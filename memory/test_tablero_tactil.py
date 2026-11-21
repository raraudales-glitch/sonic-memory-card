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
        self.ventana_real = os.environ.get("CHROMIUM_HEADED") == "1"
        interfaz = ["--window-size=1280,950"] if self.ventana_real else ["--headless=new", "--disable-gpu"]
        navegador = subprocess.Popen([
            binario, *interfaz, "--no-first-run", "--disable-background-networking",
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

    def configurar_vista(self, ancho, *, movil):
        self.cdp("Emulation.setTouchEmulationEnabled", enabled=movil)
        if self.ventana_real and not movil:
            self.cdp("Emulation.clearDeviceMetricsOverride")
        else:
            self.cdp("Emulation.setDeviceMetricsOverride", mobile=movil, width=ancho, height=800, deviceScaleFactor=2)

    def abrir(self, partida, ancho, *, movil=True):
        self.configurar_vista(ancho, movil=movil)
        url = self.live_server_url + ruta("jugar_partida", partida)
        self.cdp("Page.navigate", url=url)
        self.esperar(lambda: self.js(
            f"location.href === {json.dumps(url)} && !!document.querySelector('.carta[aria-disabled=false]')"
        ))

    def tocar(self, posicion, *, tactil=True):
        selector = f".carta[data-posicion='{posicion}']"
        x, y = self.js(f"""(() => {{
            const carta = document.querySelector("{selector}");
            carta.scrollIntoView({{block: 'center'}});
            const rect = carta.getBoundingClientRect();
            return [rect.x + rect.width / 2, rect.y + rect.height / 2];
        }})()""")
        if tactil:
            self.cdp("Input.dispatchTouchEvent", type="touchStart", touchPoints=[{"x": x, "y": y}])
            self.cdp("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        else:
            for tipo in ("mousePressed", "mouseReleased"):
                self.cdp("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)

    def comprobar_giro_jugada(self, *, tactil, animado):
        self.js("""(() => {
            window.giroDeJugada = {};
            const giro = document.querySelector('.carta-giro');
            giro.addEventListener('transitionstart', () => {
                setTimeout(() => {
                    giroDeJugada.intermedio = new DOMMatrix(getComputedStyle(giro).transform).m11;
                }, 100);
            }, {once: true});
            giro.addEventListener('transitionend', evento => {
                giroDeJugada.duracion = evento.elapsedTime;
            }, {once: true});
        })()""")
        self.tocar(0, tactil=tactil)
        self.esperar(lambda: self.cantidad(".carta.volteada") == 1)
        if animado:
            self.esperar(lambda: self.js("giroDeJugada.duracion === 0.3"))
            self.assertLess(abs(self.js("giroDeJugada.intermedio")), 0.98)
        else:
            self.assertEqual(self.js("document.querySelector('.carta-giro').getAnimations().length"), 0)
            self.assertEqual(self.js("giroDeJugada"), {})

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

    def test_vista_previa_simultanea_y_con_duracion_por_nivel(self):
        self.cdp("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "no-preference"}])
        self.cdp("Page.enable")
        self.cdp("Page.addScriptToEvaluateOnNewDocument", source="""
            window.fasesPrevia = [];
            const decode = HTMLImageElement.prototype.decode;
            let primeraPrecarga = true;
            HTMLImageElement.prototype.decode = function () {
                const lista = decode.call(this);
                if (this.isConnected || !primeraPrecarga) return lista;
                primeraPrecarga = false;
                return lista.then(() => new Promise(resolve => setTimeout(() => {
                    window.precargaCompleta = performance.now();
                    resolve();
                }, 300)));
            };
            window.girosPrevia = [];
            window.muestrasPrevia = {};
            const animate = Element.prototype.animate;
            Element.prototype.animate = function (...argumentos) {
                const giro = animate.apply(this, argumentos);
                if (!this.matches('.animando-previa .carta-giro')) return giro;
                girosPrevia.push(giro);
                if (girosPrevia.length === 1) requestAnimationFrame(muestrear);
                return giro;
            };
            function muestrear() {
                const primero = girosPrevia[0];
                if (primero.playState === 'finished') return;
                const transcurrido = primero.currentTime;
                const restante = primero.effect.getTiming().duration - transcurrido;
                let fase;
                if (transcurrido > 80 && transcurrido < 220) fase = 'apertura';
                if (transcurrido > 350 && restante > 350) fase = 'pausa';
                if (restante > 80 && restante < 220) fase = 'cierre';
                if (fase && !muestrasPrevia[fase]) {
                    const giros = [...document.querySelectorAll('.carta-giro')];
                    muestrasPrevia[fase] = {
                        angulos: giros.map(giro => new DOMMatrix(getComputedStyle(giro).transform).m11),
                        habilitadas: document.querySelectorAll('.carta[aria-disabled=false]').length,
                    };
                    giros[0].closest('.carta').click();
                }
                requestAnimationFrame(muestrear);
            }
            new MutationObserver(cambios => {
                for (const cambio of cambios) {
                    const tablero = cambio.target;
                    if (!tablero.classList?.contains('tablero') || cambio.attributeName !== 'class') continue;
                    const cartas = [...tablero.querySelectorAll('.carta')];
                    fasesPrevia.push({
                        instante: performance.now(),
                        perspectiva: getComputedStyle(cartas[0]).perspective,
                        activa: tablero.classList.contains('animando-previa'),
                        listas: cartas.filter(carta => carta.querySelector('.carta-personaje').naturalWidth > 0).length,
                        habilitadas: cartas.filter(carta => carta.getAttribute('aria-disabled') === 'false').length,
                    });
                }
            }).observe(document, {attributes: true, subtree: true});
        """)
        for ancho in (390, 1200):
            self.configurar_vista(ancho, movil=ancho == 390)
            for dificultad, total, duracion in (("FACIL", 16, 3000), ("NORMAL", 20, 1500), ("DIFICIL", 36, 0)):
                with self.subTest(ancho=ancho, dificultad=dificultad):
                    partida = crear(self.client, dificultad)
                    url = self.live_server_url + ruta("jugar_partida", partida)
                    self.cdp("Page.navigate", url=url)
                    self.esperar(lambda: self.js(f"location.href === {json.dumps(url)} && !!document.querySelector('.tablero')"))
                    self.assertIsNotNone(self.js("window.fasesPrevia"))
                    self.esperar(lambda: self.cantidad(".carta[aria-disabled=false]") == total)
                    fases = self.js("fasesPrevia")
                    consultas = self.js("performance.getEntriesByType('resource').filter(r => r.name.includes('/vista-previa/')).length")
                    self.assertEqual(consultas, int(bool(duracion)))
                    if duracion:
                        self.assertEqual([fase["activa"] for fase in fases], [True, False])
                        self.assertEqual([fase["habilitadas"] for fase in fases], [0, total])
                        self.assertEqual([fase["perspectiva"] for fase in fases], ["650px", "none"])
                        self.assertEqual([fase["listas"] for fase in fases], [total, 0])
                        self.assertGreaterEqual(fases[0]["instante"], self.js("precargaCompleta"))
                        self.assertAlmostEqual(fases[1]["instante"] - fases[0]["instante"], duracion, delta=120)
                        giros = self.js("""girosPrevia.map(giro => ({
                            inicio: giro.startTime,
                            duracion: giro.effect.getTiming().duration,
                            estado: giro.playState,
                            puntos: giro.effect.getKeyframes().map(fotograma => fotograma.offset),
                        }))""")
                        self.assertEqual(len(giros), total)
                        self.assertEqual(len({giro["inicio"] for giro in giros}), 1)
                        for giro in giros:
                            self.assertEqual(giro["duracion"], duracion)
                            self.assertEqual(giro["estado"], "finished")
                            self.assertEqual(giro["puntos"], [0, 300 / duracion, 1 - 300 / duracion, 1])
                        muestras = self.js("muestrasPrevia")
                        self.assertEqual(set(muestras), {"apertura", "pausa", "cierre"})
                        for fase, muestra in muestras.items():
                            self.assertEqual(muestra["habilitadas"], 0)
                            angulos = muestra["angulos"]
                            self.assertEqual(len(angulos), total)
                            self.assertAlmostEqual(max(angulos), min(angulos), delta=0.01)
                            if fase == "pausa":
                                self.assertAlmostEqual(angulos[0], -1)
                            else:
                                self.assertLess(abs(angulos[0]), 0.98)
                    else:
                        self.assertEqual(fases, [])
                        self.assertEqual(self.js("girosPrevia.length"), 0)
                    self.assertTrue(self.js("""[...document.querySelectorAll('.carta-giro')]
                        .every(giro => getComputedStyle(giro).transform === 'none')"""))
                    self.assertEqual(self.cantidad(".carta-personaje[src]"), 0)
                    self.assertFalse(Movimiento.objects.filter(partida=partida).exists())
                    self.assertTrue(self.js("document.querySelector('#preferencia-giros').offsetParent === null"))
                    self.comprobar_giro_jugada(tactil=ancho == 390, animado=True)
                    self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 1)

    def test_movimiento_reducido_y_activacion_explicita_de_giros(self):
        self.cdp("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
        self.cdp("Page.enable")
        self.cdp("Page.addScriptToEvaluateOnNewDocument", source="""
            window.fotogramasPrevia = [];
            document.addEventListener('DOMContentLoaded', () => {
                const estilo = document.createElement('style');
                estilo.textContent = '@media (pointer: fine) { body .tablero .carta-giro { transition: none !important; } }';
                document.head.append(estilo);
            });
            const animate = Element.prototype.animate;
            Element.prototype.animate = function (...args) {
                const animacion = animate.apply(this, args);
                if (this.matches('.animando-previa .carta-giro')) {
                    fotogramasPrevia.push(animacion.effect.getKeyframes().map(fotograma => fotograma.transform));
                }
                return animacion;
            };
        """)
        for activados in (False, True, False):
            with self.subTest(activados=activados):
                partida = crear(self.client, "NORMAL")
                self.abrir(partida, 1200, movil=False)
                self.assertTrue(self.js("matchMedia('(prefers-reduced-motion: reduce)').matches"))
                self.assertTrue(self.js("document.querySelector('#preferencia-giros').offsetParent !== null"))
                estado = self.js("document.querySelector('#preferencia-giros').getAttribute('aria-pressed')")
                self.assertEqual(estado, str(activados).lower())
                self.assertTrue(self.js("matchMedia('(pointer: fine)').matches"))
                transicion = self.js("getComputedStyle(document.querySelector('.carta-giro')).transitionDuration")
                self.assertEqual(transicion, "0.3s" if activados else "0s")
                recurso = self.js("performance.getEntriesByType('resource').find(r => r.name.includes('tablero.js')).name")
                self.assertTrue(recurso.endswith("?v=6"))
                poses = ["rotateY(180deg)"] * 2
                if activados:
                    poses = ["rotateY(0deg)", *poses, "rotateY(0deg)"]
                self.assertEqual(self.js("fotogramasPrevia"), [poses] * 20)
                self.comprobar_giro_jugada(tactil=False, animado=activados)
                self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 1)
                self.js("document.querySelector('#preferencia-giros').click()")

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
