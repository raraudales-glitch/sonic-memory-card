
(() => {
    "use strict";

    const CLAVES = {
        musica: "sonic_panel_musica_vol",
        efectos: "sonic_panel_efectos_vol",
        muteMusica: "sonic_panel_musica_mute",
        muteEfectos: "sonic_panel_efectos_mute"
    };

    function leerVolumen(clave, claveAnterior, valorInicial) {
        const guardado = localStorage.getItem(clave)
            ?? localStorage.getItem(claveAnterior);

        const numero = Number(guardado);

        return guardado !== null && Number.isFinite(numero)
            ? Math.max(0, Math.min(100, numero))
            : valorInicial;
    }

    function iniciarMenu() {
        if (document.getElementById("sonic-boton-menu")) {
            return;
        }

        const estado = {
            musica: leerVolumen(
                CLAVES.musica,
                "sonic_volumen",
                65
            ),

            efectos: leerVolumen(
                CLAVES.efectos,
                "sonic_volumen_efectos",
                80
            ),

            muteMusica:
                localStorage.getItem(CLAVES.muteMusica) === "1",

            muteEfectos:
                localStorage.getItem(CLAVES.muteEfectos) === "1"
        };

        const css = document.createElement("style");
        css.id = "sonic-estilos-menu-opciones";

        css.textContent = `
            .sonic-audio-menu,
            .sonic-controles-audio,
            .sonic-volumen-efectos {
                display: none !important;
            }

            #sonic-acciones-sonido {
                display: inline-flex !important;
                align-items: center !important;
                justify-content: flex-end;
                gap: 10px;
                flex: 0 0 auto;
                position: relative;
                min-width: 0;
                margin: 0;
            }

            #sonic-acciones-sonido > form {
                position: static !important;
                margin: 0 !important;
                display: inline-flex;
                align-items: center;
            }

            #sonic-acciones-sonido > a,
            #sonic-acciones-sonido > button {
                position: static !important;
                inset: auto !important;
                margin: 0 !important;
                transform: none !important;
            }

            #sonic-boton-menu {
                position: static !important;
                inset: auto !important;
                transform: none !important;

                display: inline-flex !important;
                flex-direction: column;
                align-items: center;
                justify-content: center;

                gap: 5px;
                width: 44px;
                height: 44px;
                min-width: 44px;

                padding: 0;
                margin: 0 !important;

                border: 2px solid #ffdf00;
                border-radius: 10px;

                background: #081d45;
                box-shadow: 0 0 12px rgba(0,107,255,.33);

                cursor: pointer;
                z-index: 1;
            }

            #sonic-boton-menu span {
                display: block;
                width: 23px;
                height: 3px;
                border-radius: 4px;
                background: #ffdf00;
            }

            #sonic-boton-menu:hover,
            #sonic-boton-menu[aria-expanded="true"] {
                background: #103a78;
            }

            #sonic-panel-sonido {
                box-sizing: border-box;
                position: fixed;
                top: 70px;
                right: 12px;
                z-index: 10000;

                width: 330px;
                max-width: calc(100vw - 24px);
                max-height: calc(100vh - 24px);

                overflow-y: auto;
                padding: 22px;

                color: #fff;
                font-family: Arial, Helvetica, sans-serif;

                background: rgba(5,20,50,.98);
                border: 2px solid #ffdf00;
                border-radius: 18px;

                box-shadow: 0 15px 40px rgba(0,0,0,.6);

                opacity: 0;
                visibility: hidden;
                pointer-events: none;

                transform: translateY(-8px);

                transition:
                    opacity .2s,
                    transform .2s,
                    visibility .2s;
            }

            #sonic-panel-sonido.abierto {
                opacity: 1;
                visibility: visible;
                pointer-events: auto;
                transform: translateY(0);
            }

            .sonic-panel-cabecera {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 22px;
            }

            .sonic-panel-cabecera h2 {
                margin: 0;
                color: #ffdf00;
                font-size: 24px;
            }

            #sonic-cerrar-menu {
                width: 36px;
                height: 36px;
                color: #fff;
                font-size: 22px;

                background: #17396a;
                border: 1px solid #5485bc;
                border-radius: 8px;

                cursor: pointer;
            }

            .sonic-grupo-sonido {
                margin-bottom: 24px;
            }

            .sonic-etiqueta-sonido {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 12px;
            }

            .sonic-etiqueta-sonido label {
                font-size: 16px;
                font-weight: bold;
            }

            .sonic-etiqueta-sonido output {
                color: #a5dfff;
                font-size: 13px;
            }

            .sonic-control-sonido {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .sonic-control-sonido input[type="range"] {
                flex: 1;
                width: 100%;
                min-width: 0;
                accent-color: #ffdf00;
                cursor: pointer;
            }

            .sonic-boton-mute {
                flex: 0 0 42px;
                height: 38px;

                border: 0;
                border-radius: 9px;

                background: #ffdf00;
                color: #081d45;

                font-size: 18px;
                font-weight: 900;
                cursor: pointer;
            }

            .sonic-boton-mute.activo {
                background: #b52339;
                color: #fff;
                border: 1px solid #ff7487;
            }

            .sonic-panel-ayuda {
                margin: 0;
                padding-top: 15px;

                border-top: 1px solid #294b7b;

                color: #a9beda;
                font-size: 12px;
                line-height: 1.6;
            }

            #sonic-boton-menu:focus-visible,
            #sonic-panel-sonido button:focus-visible,
            #sonic-panel-sonido input:focus-visible {
                outline: 3px solid #8addff;
                outline-offset: 3px;
            }

            @media (max-width: 700px) {
                #sonic-acciones-sonido {
                    gap: 7px;
                }

                #sonic-boton-menu {
                    width: 42px;
                    height: 42px;
                    min-width: 42px;
                }

                #sonic-panel-sonido {
                    padding: 18px;
                }
            }
        `;

        document.head.appendChild(css);

        const boton = document.createElement("button");

        boton.type = "button";
        boton.id = "sonic-boton-menu";

        boton.setAttribute(
            "aria-label",
            "Abrir opciones de sonido"
        );

        boton.setAttribute("aria-expanded", "false");

        boton.setAttribute(
            "aria-controls",
            "sonic-panel-sonido"
        );

        boton.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;

        const panel = document.createElement("aside");

        panel.id = "sonic-panel-sonido";

        panel.setAttribute(
            "aria-label",
            "Opciones de sonido"
        );

        panel.setAttribute("aria-hidden", "true");
        panel.setAttribute("inert", "");

        panel.innerHTML = `
            <div class="sonic-panel-cabecera">
                <h2>Sonido</h2>

                <button
                    type="button"
                    id="sonic-cerrar-menu"
                    aria-label="Cerrar menú"
                >×</button>
            </div>

            <div class="sonic-grupo-sonido">
                <div class="sonic-etiqueta-sonido">
                    <label for="sonic-barra-musica">
                        Música
                    </label>

                    <output id="sonic-valor-musica">
                        65%
                    </output>
                </div>

                <div class="sonic-control-sonido">
                    <input
                        id="sonic-barra-musica"
                        type="range"
                        min="0"
                        max="100"
                        value="65"
                    >

                    <button
                        type="button"
                        id="sonic-mute-musica"
                        class="sonic-boton-mute"
                        aria-label="Silenciar música"
                        aria-pressed="false"
                    >M</button>
                </div>
            </div>

            <div class="sonic-grupo-sonido">
                <div class="sonic-etiqueta-sonido">
                    <label for="sonic-barra-efectos">
                        Efectos
                    </label>

                    <output id="sonic-valor-efectos">
                        80%
                    </output>
                </div>

                <div class="sonic-control-sonido">
                    <input
                        id="sonic-barra-efectos"
                        type="range"
                        min="0"
                        max="100"
                        value="80"
                    >

                    <button
                        type="button"
                        id="sonic-mute-efectos"
                        class="sonic-boton-mute"
                        aria-label="Silenciar efectos"
                        aria-pressed="false"
                    >M</button>
                </div>
            </div>

            <p class="sonic-panel-ayuda">
                M silencia cada canal por separado.
                Esc abre o cierra el menú.
                El tiempo del juego continúa mientras ajustas el sonido.
            </p>
        `;

        const cabecera = document.querySelector(
            ".barra-superior, header, nav"
        );

        const controles = cabecera
            ? Array.from(
                cabecera.querySelectorAll(
                    "a, button, input[type='submit']"
                )
            )
            : [];

        const salida = controles.find(
            el => el.matches(".btn-salir")
        ) || controles.find(el => {
            const texto = (
                el.textContent ||
                el.value ||
                el.getAttribute("aria-label") ||
                ""
            )
                .replace(/\s+/g, " ")
                .trim();

            return /salir|cerrar\s+sesi[oó]n|logout/i.test(texto);
        });

        const acciones = document.createElement("div");
        acciones.id = "sonic-acciones-sonido";

        if (salida) {
            const elementoSalida =
                salida.closest("form") || salida;

            elementoSalida.parentNode.insertBefore(
                acciones,
                elementoSalida
            );

            acciones.appendChild(elementoSalida);
        } else {
            const destino =
                document.querySelector(".info-superior") ||
                cabecera ||
                document.body;

            destino.appendChild(acciones);
        }

        acciones.appendChild(boton);

        document.body.appendChild(panel);

        const barraMusica = panel.querySelector(
            "#sonic-barra-musica"
        );

        const barraEfectos = panel.querySelector(
            "#sonic-barra-efectos"
        );

        const valorMusica = panel.querySelector(
            "#sonic-valor-musica"
        );

        const valorEfectos = panel.querySelector(
            "#sonic-valor-efectos"
        );

        const muteMusica = panel.querySelector(
            "#sonic-mute-musica"
        );

        const muteEfectos = panel.querySelector(
            "#sonic-mute-efectos"
        );

        const cerrar = panel.querySelector(
            "#sonic-cerrar-menu"
        );

        let abierto = false;

        function actualizarInterfaz() {
            barraMusica.value = estado.musica;
            barraEfectos.value = estado.efectos;

            valorMusica.textContent = estado.muteMusica
                ? "Silenciada"
                : `${estado.musica}%`;

            valorEfectos.textContent = estado.muteEfectos
                ? "Silenciados"
                : `${estado.efectos}%`;

            for (const [botonMute, silencioso, tipo] of [
                [muteMusica, estado.muteMusica, "música"],
                [muteEfectos, estado.muteEfectos, "efectos"]
            ]) {
                botonMute.classList.toggle(
                    "activo",
                    silencioso
                );

                botonMute.setAttribute(
                    "aria-pressed",
                    String(silencioso)
                );

                botonMute.setAttribute(
                    "aria-label",
                    silencioso
                        ? `Activar ${tipo}`
                        : `Silenciar ${tipo}`
                );

                botonMute.title = silencioso
                    ? `Activar ${tipo}`
                    : `Silenciar ${tipo}`;
            }
        }

        function actualizarSonido() {
            const volumenMusica = estado.muteMusica
                ? 0
                : estado.musica;

            const volumenEfectos = estado.muteEfectos
                ? 0
                : estado.efectos;

            localStorage.setItem(
                CLAVES.musica,
                String(estado.musica)
            );

            localStorage.setItem(
                CLAVES.efectos,
                String(estado.efectos)
            );

            localStorage.setItem(
                CLAVES.muteMusica,
                estado.muteMusica ? "1" : "0"
            );

            localStorage.setItem(
                CLAVES.muteEfectos,
                estado.muteEfectos ? "1" : "0"
            );

            localStorage.setItem("sonic_silencio", "0");

            localStorage.setItem(
                "sonic_volumen",
                String(volumenMusica)
            );

            localStorage.setItem(
                "sonic_volumen_efectos",
                String(volumenEfectos)
            );

            const barraAnterior = document.querySelector(
                "#sonic-menu-volumen, #sonic-volumen"
            );

            if (barraAnterior) {
                barraAnterior.value = String(volumenMusica);

                barraAnterior.dispatchEvent(
                    new Event("input", {
                        bubbles: true
                    })
                );
            }

            window.dispatchEvent(
                new Event("sonic:preferencias")
            );

            window.SonicUI?.actualizarVolumenEfectos?.();

            actualizarInterfaz();
        }

        function posicionarPanel() {
            const rect = boton.getBoundingClientRect();

            const ancho = Math.min(
                330,
                window.innerWidth - 24
            );

            const izquierda = Math.max(
                12,
                Math.min(
                    rect.right - ancho,
                    window.innerWidth - ancho - 12
                )
            );

            const superior = rect.bottom + 10;

            const arriba = Math.min(
                superior,
                window.innerHeight - 100
            );

            panel.style.left = `${izquierda}px`;
            panel.style.right = "auto";
            panel.style.top = `${arriba}px`;

            panel.style.maxHeight = `${
                Math.max(100, window.innerHeight - arriba - 12)
            }px`;
        }

        function cambiarMenu(mostrar) {
            abierto = Boolean(mostrar);

            if (abierto) {
                posicionarPanel();
            }

            panel.classList.toggle("abierto", abierto);

            panel.setAttribute(
                "aria-hidden",
                String(!abierto)
            );

            if (abierto) {
                panel.removeAttribute("inert");
            } else {
                panel.setAttribute("inert", "");
            }

            boton.setAttribute(
                "aria-expanded",
                String(abierto)
            );

            boton.setAttribute(
                "aria-label",
                abierto
                    ? "Cerrar opciones de sonido"
                    : "Abrir opciones de sonido"
            );

            if (abierto) {
                cerrar.focus();
            } else {
                boton.focus();
            }
        }

        barraMusica.addEventListener("input", () => {
            estado.musica = Number(barraMusica.value);

            if (estado.musica > 0) {
                estado.muteMusica = false;
            }

            actualizarSonido();
        });

        barraEfectos.addEventListener("input", () => {
            estado.efectos = Number(barraEfectos.value);

            if (estado.efectos > 0) {
                estado.muteEfectos = false;
            }

            actualizarSonido();
        });

        muteMusica.addEventListener("click", () => {
            estado.muteMusica = !estado.muteMusica;
            actualizarSonido();
        });

        muteEfectos.addEventListener("click", () => {
            estado.muteEfectos = !estado.muteEfectos;
            actualizarSonido();

            if (!estado.muteEfectos) {
                window.SonicUI?.reproducir?.("carta");
            }
        });

        boton.addEventListener("click", () => {
            cambiarMenu(!abierto);
        });

        cerrar.addEventListener("click", () => {
            cambiarMenu(false);
        });

        document.addEventListener("keydown", evento => {
            if (evento.key !== "Escape") {
                return;
            }

            if (
                !abierto &&
                document.getElementById("sonic-fin")
            ) {
                return;
            }

            evento.preventDefault();
            cambiarMenu(!abierto);
        });

        document.addEventListener("pointerdown", evento => {
            if (
                abierto &&
                !panel.contains(evento.target) &&
                !boton.contains(evento.target)
            ) {
                cambiarMenu(false);
            }
        });

        window.addEventListener("resize", () => {
            if (abierto) {
                posicionarPanel();
            }
        });

        window.addEventListener(
            "scroll",
            () => {
                if (abierto) {
                    posicionarPanel();
                }
            },
            true
        );

        actualizarSonido();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            iniciarMenu
        );
    } else {
        iniciarMenu();
    }
})();
