(() => {
    const raiz = document.body;
    const id = raiz.dataset.partidaId;
    const base = raiz.dataset.staticBase || "/static/";
    if (!id) return;

    const prefijo = `/partidas/${id}/`;
    const reloj = document.getElementById("tiempo-juego");
    const fallos = document.getElementById("fallos-actuales");
    const mensaje = document.getElementById("mensaje-juego");
    const cartas = Array.from(document.querySelectorAll(".carta"));
    const finEstados = new Set(["GANADA", "PERDIDA", "TIEMPO_AGOTADO", "ABANDONADA"]);

    let estado = "EN_CURSO";
    let cierreMostrado = false;
    let finLocal = Date.now() + (Number.parseInt(reloj?.textContent || "0", 10) || 0) * 1000;
    let sonidoHabilitado = true;
    let silencio = localStorage.getItem("sonic_silencio") === "1";
    let volumen = Number(localStorage.getItem("sonic_volumen") ?? "65") / 100;
    volumen = Math.min(1, Math.max(0, volumen));

    const musicaNormal = new Audio(`${base}memory/audio/musica/partida.mp3`);
    const musicaAlerta = new Audio(`${base}memory/audio/musica/ahogamiento.mp3`);
    musicaNormal.loop = true;
    musicaAlerta.loop = true;
    [musicaNormal, musicaAlerta].forEach(audio => {
        audio.preload = "auto";
        audio.volume = silencio ? 0 : volumen;
        audio.addEventListener("error", () => {
            console.warn("No se pudo cargar el audio:", audio.src);
        });
    });

    const controles = document.createElement("div");
    controles.className = "sonic-controles-audio";
    controles.innerHTML = `
        <button id="sonic-sonido" type="button">${silencio ? "Activar sonido" : "Silenciar"}</button>
        <label for="sonic-volumen">Música</label>
        <input id="sonic-volumen" type="range" min="0" max="100" value="${Math.round(volumen * 100)}" aria-label="Volumen de música">
    `;
    const estilos = document.createElement("style");
    estilos.textContent = `
        .sonic-controles-audio {display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:12px;margin:16px auto;padding:12px;color:#fff;background:#091a34;border:1px solid #1771c9;border-radius:12px;max-width:450px}
        .sonic-controles-audio button {background:#ffd52a;color:#101929;border:0;border-radius:8px;padding:9px 12px;font-weight:bold;cursor:pointer}
        .sonic-controles-audio input {width:125px}
        #sonic-fin {position:fixed;inset:0;z-index:999;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.84);padding:20px}
        #sonic-fin .sonic-panel-fin {background:#0b1b39;border:2px solid #3285e9;border-radius:20px;padding:30px;text-align:center;max-width:420px;width:100%;color:white}
        #sonic-fin a {display:inline-block;margin-top:20px;padding:12px 18px;background:#ffd52a;color:#0b1b39;border-radius:10px;text-decoration:none;font-weight:bold}
    `;
    document.head.appendChild(estilos);
    document.querySelector(".zona-juego")?.appendChild(controles);

    function actualizarVolumen() {
        [musicaNormal, musicaAlerta].forEach(a => a.volume = silencio ? 0 : volumen);
        document.getElementById("sonic-sonido").textContent = silencio ? "Activar sonido" : "Silenciar";
    }

    document.getElementById("sonic-sonido").addEventListener("click", () => {
        silencio = !silencio;
        localStorage.setItem("sonic_silencio", silencio ? "1" : "0");
        actualizarVolumen();
        window.dispatchEvent(new Event("sonic:preferencias"));
        reproducirSegunTiempo();
    });
    document.getElementById("sonic-volumen").addEventListener("input", e => {
        volumen = Number(e.target.value) / 100;
        localStorage.setItem("sonic_volumen", String(e.target.value));
        actualizarVolumen();
    });

    function activarEnInteraccion() {
        sonidoHabilitado = true;
        reproducirSegunTiempo();
    }
    document.addEventListener("pointerdown", activarEnInteraccion, {capture: true});
    document.addEventListener("keydown", activarEnInteraccion, {capture: true});

    function segundosVisibles() {
        return Math.max(0, Math.ceil((finLocal - Date.now()) / 1000));
    }

    function reproducirSegunTiempo() {
        if (!sonidoHabilitado || estado !== "EN_CURSO") return;
        const s = segundosVisibles();
        const usarAlerta = s <= 15;
        const actual = usarAlerta ? musicaAlerta : musicaNormal;
        const otro = usarAlerta ? musicaNormal : musicaAlerta;
        otro.pause();
        if (s === 0) { actual.pause(); return; }
        musicaNormal.playbackRate = s <= 30 ? 1.25 : 1;
        if (actual.paused && !silencio) {
            actual.play().catch(err => {
                sonidoHabilitado = false;
                console.info("El navegador bloqueó la música; se activará con el próximo clic:", err.message);
            });
        }
        if (silencio) actual.pause();
    }

    function mostrarFinal(datos) {
        if (cierreMostrado || window.SonicUI?.modalAbierto()) return;
        cierreMostrado = true;
        estado = datos.estado;
        if (datos.estado === "GANADA") window.SonicUI?.reproducir("victoria");
        if (["PERDIDA", "TIEMPO_AGOTADO"].includes(datos.estado)) window.SonicUI?.reproducir("derrota");
        [musicaNormal, musicaAlerta].forEach(a => a.pause());
        cartas.forEach(carta => { carta.disabled = true; carta.style.cursor = "not-allowed"; });
        const titulos = {
            GANADA: "¡Ganaste!", PERDIDA: "Se acabaron los intentos",
            TIEMPO_AGOTADO: "Se acabó el tiempo", ABANDONADA: "Partida abandonada"
        };
        const panel = document.createElement("div");
        panel.id = "sonic-fin";
        const tarjeta = document.createElement("div");
        tarjeta.className = "sonic-panel-fin";
        const titulo = document.createElement("h2");
        titulo.textContent = titulos[datos.estado] || "Partida terminada";
        const resumen = document.createElement("p");
        resumen.textContent = `Fallos: ${datos.fallos}. Puntaje: ${datos.puntaje || 0}.`;
        const volver = document.createElement("a");
        volver.href = "/";
        volver.textContent = "Volver al menú";
        tarjeta.append(titulo, resumen, volver);
        panel.appendChild(tarjeta);
        document.body.appendChild(panel);
    }

    function reconstruirCartas(datos) {
        if (typeof window.mostrarPersonaje !== "function") return;
        for (const cartaInfo of (datos.emparejadas || [])) {
            const carta = cartas.find(c => Number(c.dataset.posicion) === cartaInfo.posicion);
            if (carta) {
                window.mostrarPersonaje(cartaInfo);
                carta.classList.add("emparejada");
            }
        }
        for (const cartaInfo of (datos.visibles || [])) {
            window.mostrarPersonaje(cartaInfo);
        }
    }

    let consultando = false;
    async function actualizarDesdeServidor() {
        if (consultando || cierreMostrado) return;
        consultando = true;
        try {
            const respuesta = await fetch(`${prefijo}estado/`, {cache: "no-store"});
            if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
            const datos = await respuesta.json();
            estado = datos.estado;
            finLocal = Date.now() + datos.tiempo_restante * 1000;
            if (fallos) fallos.textContent = datos.fallos;
            reconstruirCartas(datos);
            if (finEstados.has(datos.estado)) mostrarFinal(datos);
            reproducirSegunTiempo();
        } catch (error) {
            console.warn("No se pudo sincronizar la partida:", error);
        } finally {
            consultando = false;
        }
    }

    setInterval(() => {
        if (cierreMostrado) return;
        const s = segundosVisibles();
        if (reloj) {
            reloj.textContent = `${s}s`;
            reloj.style.color = s <= 15 ? "#ff5266" : s <= 30 ? "#ffc533" : "white";
        }
        if (s === 0) {
            cartas.forEach(c => c.disabled = true);
            if (mensaje) mensaje.textContent = "Verificando el final de la partida...";
        }
        reproducirSegunTiempo();
    }, 250);

    setInterval(actualizarDesdeServidor, 2000);
    actualizarDesdeServidor();

    const salir = document.querySelector("a.btn-salir");
    if (salir) salir.addEventListener("click", async e => {
        if (estado !== "EN_CURSO") return;
        e.preventDefault();
        if (!confirm("¿Abandonar la partida? Contará como derrota.")) return;
        const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
        try {
            await fetch(`${prefijo}abandonar/`, {
                method: "POST", headers: {"X-CSRFToken": csrf || ""}, credentials: "same-origin"
            });
            location.href = salir.href;
        } catch (_) {
            if (mensaje) mensaje.textContent = "No se pudo abandonar. Inténtalo otra vez.";
        }
    });
})();
