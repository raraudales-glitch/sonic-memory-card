
(() => {
    "use strict";

    const CLAVES = {
        musica: "sonic_panel_musica_vol",
        efectos: "sonic_panel_efectos_vol",
        muteMusica: "sonic_panel_musica_mute",
        muteEfectos: "sonic_panel_efectos_mute"
    };

    function leerVolumen(clave, anterior, defecto) {
        const valor = localStorage.getItem(clave)
            ?? localStorage.getItem(anterior);

        if (valor === null) return defecto;

        const numero = Number(valor);

        return Number.isFinite(numero)
            ? Math.min(100, Math.max(0, numero))
            : defecto;
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

        const estilo = document.createElement("style");

        estilo.textContent = `
            .sonic-audio-menu,
            .sonic-controles-audio,
            .sonic-volumen-efectos {
                display: none !important;
            }

            #sonic-boton-menu {
                position: fixed;
                top: 15px;
                right: 16px;
                width: 47px;
                height: 47px;
                z-index: 10001;

                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 5px;

                background: #081d45;
                border: 2px solid #ffdf00;
                border-radius: 12px;
                cursor: pointer;

                box-shadow: 0 0 15px #006bff55;
            }

            #sonic-boton-menu span {
                width: 23px;
                height: 3px;
                background: #ffdf00;
                border-radius: 4px;
            }

            #sonic-boton-menu:hover {
                background: #103a78;
            }

            #sonic-panel-sonido {
                position: fixed;
                top: 75px;
                right: 16px;
                width: 330px;
                max-width: calc(100vw - 32px);
                padding: 22px;

                background: rgba(5, 20, 50, 0.98);
                border: 2px solid #ffdf00;
                border-radius: 18px;

                box-shadow: 0 15px 40px #0009;
                z-index: 10000;
                color: white;
                font-family: Arial, sans-serif;

                transform: translateX(120%);
                opacity: 0;
                visibility: hidden;
                pointer-events: none;

                transition:
                    transform .3s ease,
                    opacity .3s ease,
                    visibility .3s;
            }

            #sonic-panel-sonido.abierto {
                transform: translateX(0);
                opacity: 1;
                visibility: visible;
                pointer-events: auto;
            }

            .sonic-panel-cabecera {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 25px;
            }

            .sonic-panel-cabecera h2 {
                color: #ffdf00;
                font-size: 24px;
                margin: 0;
            }

            #sonic-cerrar-menu {
                width: 35px;
                height: 35px;
                background: #17396a;
                border: 1px solid #5485bc;
                border-radius: 8px;
                color: white;
                font-size: 22px;
                cursor: pointer;
            }

            .sonic-grupo-sonido {
                margin-bottom: 25px;
            }

            .sonic-etiqueta-sonido {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
            }

            .sonic-etiqueta-sonido label {
                font-weight: bold;
                font-size: 16px;
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

            .sonic-control-sonido input {
                width: 100%;
                min-width: 0;
                flex: 1;
                accent-color: #ffdf00;
                cursor: pointer;
            }

            .sonic-boton-mute {
                width: 42px;
                height: 38px;
                flex-shrink: 0;

                background: #ffdf00;
                color: #081d45;
                font-size: 18px;
                font-weight: 900;

                border: none;
                border-radius: 9px;
                cursor: pointer;
            }

            .sonic-boton-mute.activo {
                background: #b52339;
                color: white;
                border: 1px solid #ff7487;
            }

            .sonic-boton-mute:hover {
                filter: brightness(1.12);
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
                #sonic-boton-menu {
                    top: 8px;
                    right: 8px;
                }

                #sonic-panel-sonido {
                    top: 65px;
                    right: 8px;
                    max-width: calc(100vw - 16px);
                }
            }
        `;

        document.head.appendChild(estilo);

        const boton = document.createElement("button");

        boton.id = "sonic-boton-menu";
        boton.type = "button";
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
        panel.setAttribute("aria-label", "Opciones de sonido");

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
                        type="range"
                        id="sonic-barra-musica"
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
                        title="Silenciar música"
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
                        type="range"
                        id="sonic-barra-efectos"
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
                        title="Silenciar efectos"
                    >M</button>
                </div>
            </div>

            <p class="sonic-panel-ayuda">
                M: silenciar o activar cada canal.
                Esc: abrir o cerrar este menú.
                El juego continúa mientras configuras el sonido.
            </p>
        `;

        document.body.append(boton, panel);

        const barraMusica =
            document.getElementById("sonic-barra-musica");

        const barraEfectos =
            document.getElementById("sonic-barra-efectos");

        const muteMusica =
            document.getElementById("sonic-mute-musica");

        const muteEfectos =
            document.getElementById("sonic-mute-efectos");

        function actualizarInterfaz() {

            barraMusica.value = estado.musica;
            barraEfectos.value = estado.efectos;

            document.getElementById(
                "sonic-valor-musica"
            ).textContent = estado.muteMusica
                ? "Silenciada"
                : `${estado.musica}%`;

            document.getElementById(
                "sonic-valor-efectos"
            ).textContent = estado.muteEfectos
                ? "Silenciados"
                : `${estado.efectos}%`;

            muteMusica.classList.toggle(
                "activo",
                estado.muteMusica
            );

            muteEfectos.classList.toggle(
                "activo",
                estado.muteEfectos
            );

            muteMusica.setAttribute(
                "aria-pressed",
                String(estado.muteMusica)
            );

            muteEfectos.setAttribute(
                "aria-pressed",
                String(estado.muteEfectos)
            );

            muteMusica.title = estado.muteMusica
                ? "Activar música"
                : "Silenciar música";

            muteEfectos.title = estado.muteEfectos
                ? "Activar efectos"
                : "Silenciar efectos";
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

                barraAnterior.value =
                    String(volumenMusica);

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

        barraMusica.addEventListener(
            "input",
            () => {
                estado.musica = Number(
                    barraMusica.value
                );

                if (estado.musica > 0) {
                    estado.muteMusica = false;
                }

                actualizarSonido();
            }
        );

        barraEfectos.addEventListener(
            "input",
            () => {
                estado.efectos = Number(
                    barraEfectos.value
                );

                if (estado.efectos > 0) {
                    estado.muteEfectos = false;
                }

                actualizarSonido();
            }
        );

        muteMusica.addEventListener(
            "click",
            () => {
                estado.muteMusica =
                    !estado.muteMusica;

                actualizarSonido();
            }
        );

        muteEfectos.addEventListener(
            "click",
            () => {
                estado.muteEfectos =
                    !estado.muteEfectos;

                actualizarSonido();

                if (!estado.muteEfectos) {
                    window.SonicUI?.reproducir?.("carta");
                }
            }
        );

        let abierto = false;

        function cambiarMenu(valor) {

            abierto = valor;

            panel.classList.toggle(
                "abierto",
                abierto
            );

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
                panel.querySelector(
                    "#sonic-cerrar-menu"
                ).focus();
            } else {
                boton.focus();
            }
        }

        boton.addEventListener(
            "click",
            () => cambiarMenu(!abierto)
        );

        document.getElementById(
            "sonic-cerrar-menu"
        ).addEventListener(
            "click",
            () => cambiarMenu(false)
        );

        document.addEventListener(
            "keydown",
            evento => {

                if (evento.key !== "Escape") {
                    return;
                }

                if (document.getElementById("sonic-fin")) {
                    return;
                }

                evento.preventDefault();

                cambiarMenu(!abierto);
            }
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
