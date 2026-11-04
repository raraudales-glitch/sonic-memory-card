
(() => {
    "use strict";

    const raiz = document.body;
    const id = raiz.dataset.partidaId;
    const base = raiz.dataset.staticBase || "/static/";

    if (!id) return;

    const prefijo = `/partidas/${id}/`;

    const reloj = document.getElementById("tiempo-juego");
    const fallos = document.getElementById("fallos-actuales");
    const mensaje = document.getElementById("mensaje-juego");
    const cartas = Array.from(
        document.querySelectorAll(".carta")
    );

    const estadosFinales = new Set([
        "GANADA",
        "PERDIDA",
        "TIEMPO_AGOTADO",
        "ABANDONADA"
    ]);

    let estado = "EN_CURSO";
    let ultimoIntentoAudio = 0;
    let cierreMostrado = false;
    let finPendiente = false;

    let finLocal = Date.now() +
        (Number.parseInt(reloj?.textContent || "0", 10) || 0)
        * 1000;

    let sonidoHabilitado = true;

    let silencio = localStorage.getItem(
        "sonic_silencio"
    ) === "1";

    let volumen = Number(
        localStorage.getItem("sonic_volumen") ?? "65"
    ) / 100;

    volumen = Math.min(1, Math.max(0, volumen));

    const musicaNormal = new Audio(
        `${base}memory/audio/musica/partida.mp3`
    );

    const musicaAlerta = new Audio(
        `${base}memory/audio/musica/ahogamiento.mp3`
    );

    musicaNormal.loop = true;
    musicaAlerta.loop = true;

    [musicaNormal, musicaAlerta].forEach(audio => {
        audio.preload = "auto";
        audio.volume = silencio ? 0 : volumen;

        audio.addEventListener("error", () => {
            console.warn(
                "No se pudo cargar el audio:",
                audio.src
            );
        });
    });

    const controles = document.createElement("div");
    controles.className = "sonic-controles-audio";

    controles.innerHTML = `
        <button id="sonic-sonido" type="button">
            ${silencio ? "Activar sonido" : "Silenciar"}
        </button>

        <label for="sonic-volumen">Música</label>

        <input
            id="sonic-volumen"
            type="range"
            min="0"
            max="100"
            value="${Math.round(volumen * 100)}"
            aria-label="Volumen de música"
        >
    `;

    const estilos = document.createElement("style");

    estilos.textContent = `
        .sonic-controles-audio {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            margin: 16px auto;
            padding: 12px;
            color: #fff;
            background: #091a34;
            border: 1px solid #1771c9;
            border-radius: 12px;
            max-width: 450px;
        }

        .sonic-controles-audio button {
            background: #ffd52a;
            color: #101929;
            border: 0;
            border-radius: 8px;
            padding: 9px 12px;
            font-weight: bold;
            cursor: pointer;
        }

        .sonic-controles-audio input {
            width: 125px;
        }

        #sonic-fin {
            position: fixed;
            inset: 0;
            z-index: 999;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(0,0,0,.84);
            padding: 20px;
        }

        #sonic-fin .sonic-panel-fin {
            background: #0b1b39;
            border: 2px solid #3285e9;
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            max-width: 420px;
            width: 100%;
            color: white;
            box-shadow: 0 0 35px rgba(0,110,255,.4);
        }

        #sonic-fin h2 {
            color: #ffdf00;
            font-size: 30px;
            margin-bottom: 20px;
        }

        #sonic-fin p {
            margin: 10px 0;
            line-height: 1.6;
        }

        #sonic-fin a {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 18px;
            background: #ffd52a;
            color: #0b1b39;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
        }
    `;

    document.head.appendChild(estilos);

    document.querySelector(
        ".zona-juego"
    )?.appendChild(controles);

    function actualizarVolumen() {
        [musicaNormal, musicaAlerta].forEach(audio => {
            audio.volume = silencio ? 0 : volumen;
        });

        document.getElementById(
            "sonic-sonido"
        ).textContent = silencio
            ? "Activar sonido"
            : "Silenciar";
    }

    document.getElementById(
        "sonic-sonido"
    ).addEventListener("click", () => {
        silencio = !silencio;

        localStorage.setItem(
            "sonic_silencio",
            silencio ? "1" : "0"
        );

        actualizarVolumen();

        window.dispatchEvent(
            new Event("sonic:preferencias")
        );

        reproducirSegunTiempo();
    });

    document.getElementById(
        "sonic-volumen"
    ).addEventListener("input", evento => {
        volumen = Number(evento.target.value) / 100;

        localStorage.setItem(
            "sonic_volumen",
            String(evento.target.value)
        );

        actualizarVolumen();
    });

    function intentarConGesto() {
        sonidoHabilitado = true;
        ultimoIntentoAudio = 0;
        reproducirSegunTiempo();
    }

    document.addEventListener(
        "pointerdown",
        intentarConGesto,
        { capture: true }
    );

    document.addEventListener(
        "keydown",
        intentarConGesto,
        { capture: true }
    );

    window.addEventListener(
        "sonic:preferencias",
        () => {
            silencio = localStorage.getItem(
                "sonic_silencio"
            ) === "1";

            volumen = Math.min(
                1,
                Math.max(
                    0,
                    Number(
                        localStorage.getItem(
                            "sonic_volumen"
                        ) ?? "65"
                    ) / 100
                )
            );

            actualizarVolumen();

            ultimoIntentoAudio = 0;
            reproducirSegunTiempo();
        }
    );

    function segundosVisibles() {
        return Math.max(
            0,
            Math.ceil(
                (finLocal - Date.now()) / 1000
            )
        );
    }

    function reproducirSegunTiempo() {
        if (
            !sonidoHabilitado ||
            estado !== "EN_CURSO"
        ) {
            return;
        }

        const segundos = segundosVisibles();

        const usarAlerta = segundos <= 15;

        const actual = usarAlerta
            ? musicaAlerta
            : musicaNormal;

        const otro = usarAlerta
            ? musicaNormal
            : musicaAlerta;

        otro.pause();

        if (segundos === 0) {
            actual.pause();
            return;
        }

        musicaNormal.playbackRate =
            segundos <= 30 ? 1.25 : 1;

        if (
            actual.paused &&
            !silencio &&
            Date.now() - ultimoIntentoAudio > 1200
        ) {
            ultimoIntentoAudio = Date.now();

            actual.play().catch(error => {
                console.warn(
                    "Audio bloqueado:",
                    error.message
                );
            });
        }

        if (silencio) {
            actual.pause();
        }
    }

    function mostrarFinal(datos) {
        if (cierreMostrado || finPendiente) {
            return;
        }

        finPendiente = true;
        estado = datos.estado;

        [musicaNormal, musicaAlerta].forEach(audio => {
            audio.pause();
        });

        cartas.forEach(carta => {
            carta.disabled = true;
            carta.style.cursor = "not-allowed";
        });

        const inicioEspera = Date.now();

        function cuandoCierreFrase() {
            const fraseVisible = Boolean(
                document.querySelector(
                    ".sonic-toast-pareja.mostrar"
                )
            );

            if (
                fraseVisible &&
                Date.now() - inicioEspera < 4500
            ) {
                setTimeout(cuandoCierreFrase, 200);
                return;
            }

            pintarResultado(datos);
        }

        cuandoCierreFrase();
    }

    function pintarResultado(datos) {
        if (cierreMostrado) return;

        cierreMostrado = true;

        if (datos.estado === "GANADA") {
            window.SonicUI?.reproducir?.("victoria");
        }

        if (
            datos.estado === "PERDIDA" ||
            datos.estado === "TIEMPO_AGOTADO"
        ) {
            window.SonicUI?.reproducir?.("derrota");
        }

        const titulos = {
            GANADA: "¡GANASTE!",
            PERDIDA: "Se acabaron los intentos",
            TIEMPO_AGOTADO: "Se acabó el tiempo",
            ABANDONADA: "Partida abandonada"
        };

        const panel = document.createElement("div");
        panel.id = "sonic-fin";
        panel.setAttribute("role", "dialog");
        panel.setAttribute("aria-modal", "true");

        const tarjeta = document.createElement("div");
        tarjeta.className = "sonic-panel-fin";

        const titulo = document.createElement("h2");
        titulo.textContent =
            titulos[datos.estado] || "Partida terminada";

        const resumen = document.createElement("p");

        resumen.textContent =
            `Fallos: ${datos.fallos ?? 0}. ` +
            `Puntaje: ${datos.puntaje ?? 0}.`;

        const volver = document.createElement("a");
        volver.href = "/";
        volver.textContent = "Volver al menú";

        tarjeta.append(
            titulo,
            resumen,
            volver
        );

        panel.appendChild(tarjeta);
        document.body.appendChild(panel);
    }

    function reconstruirCartas(datos) {
        if (
            typeof window.mostrarPersonaje !== "function"
        ) {
            return;
        }

        for (const info of (datos.emparejadas || [])) {
            const carta = cartas.find(
                c => Number(c.dataset.posicion) ===
                    info.posicion
            );

            if (carta) {
                window.mostrarPersonaje(info);
                carta.classList.add("emparejada");
            }
        }

        for (const info of (datos.visibles || [])) {
            window.mostrarPersonaje(info);
        }
    }

    let consultando = false;

    async function actualizarDesdeServidor() {
        if (
            consultando ||
            cierreMostrado ||
            finPendiente
        ) {
            return;
        }

        consultando = true;

        try {
            const respuesta = await fetch(
                `${prefijo}estado/`,
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );

            if (!respuesta.ok) {
                throw new Error(
                    `HTTP ${respuesta.status}`
                );
            }

            const datos = await respuesta.json();

            estado = datos.estado;

            finLocal =
                Date.now() +
                datos.tiempo_restante * 1000;

            if (fallos) {
                fallos.textContent = datos.fallos;
            }

            reconstruirCartas(datos);

            if (estadosFinales.has(datos.estado)) {
                mostrarFinal(datos);
            }

            reproducirSegunTiempo();

        } catch (error) {
            console.warn(
                "No se pudo sincronizar la partida:",
                error
            );

        } finally {
            consultando = false;
        }
    }

    setInterval(() => {
        if (cierreMostrado || finPendiente) return;

        const segundos = segundosVisibles();

        if (reloj) {
            reloj.textContent = `${segundos}s`;

            reloj.style.color =
                segundos <= 15
                    ? "#ff5266"
                    : segundos <= 30
                        ? "#ffc533"
                        : "white";
        }

        if (segundos === 0) {
            cartas.forEach(carta => {
                carta.disabled = true;
            });

            if (mensaje) {
                mensaje.textContent =
                    "Verificando el final de la partida...";
            }
        }

        reproducirSegunTiempo();

    }, 250);

    setInterval(actualizarDesdeServidor, 2000);

    actualizarDesdeServidor();
    reproducirSegunTiempo();

    const salir = document.querySelector(
        "a.btn-salir"
    );

    if (salir) {
        salir.addEventListener("click", async evento => {
            if (estado !== "EN_CURSO") return;

            evento.preventDefault();

            if (
                !confirm(
                    "¿Abandonar la partida? Contará como derrota."
                )
            ) {
                return;
            }

            const csrf = document.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value;

            try {
                await fetch(
                    `${prefijo}abandonar/`,
                    {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": csrf || ""
                        },
                        credentials: "same-origin"
                    }
                );

                location.href = salir.href;

            } catch (error) {
                if (mensaje) {
                    mensaje.textContent =
                        "No se pudo abandonar. Inténtalo otra vez.";
                }
            }
        });
    }
})();
