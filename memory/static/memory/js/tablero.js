(() => {
    const {dataset} = document.body;
    const tablero = document.querySelector(".tablero");
    const cartas = [...tablero.querySelectorAll(".carta")];
    const mensaje = document.getElementById("mensaje-juego");
    const reintentar = document.getElementById("reintentar-jugada");
    const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;
    let fase = "inicio";
    let secuencia = 0;
    let visibles = 0;
    let movimiento;
    let siguiente;
    let revision = 0;
    let consulta = false;
    let esperaHasta = 0;

    async function pedir(url, opciones) {
        const controlador = new AbortController();
        const limite = setTimeout(() => controlador.abort(), 6000);
        try {
            const respuesta = await fetch(url, {
                cache: "no-store",
                credentials: "same-origin",
                ...opciones,
                signal: controlador.signal,
            });
            if (respuesta.status >= 500) throw new Error("Error del servidor");
            return await respuesta.json();
        } finally {
            clearTimeout(limite);
        }
    }

    function enviar(url, datos) {
        return pedir(url, {
            method: "POST",
            headers: {"X-CSRFToken": csrf, "Content-Type": "application/json"},
            body: JSON.stringify(datos),
        });
    }

    function rutaImagen(imagen) {
        const ruta = new URL(imagen, new URL(dataset.staticBase, location.href));
        if (imagen.startsWith("memory/images/personajes/")) ruta.searchParams.set("v", "2");
        return ruta.href;
    }

    function pintar(carta, info, pareja = false) {
        if (info) {
            const imagen = carta.querySelector(".carta-personaje");
            imagen.alt = info.nombre;
            const ruta = rutaImagen(info.imagen);
            if (imagen.getAttribute("src") !== ruta) imagen.src = ruta;
        }
        carta.classList.toggle("volteada", Boolean(info));
        carta.classList.toggle("emparejada", pareja);
        const nombre = `Carta ${Number(carta.dataset.posicion) + 1}`;
        carta.setAttribute("aria-label", info ? `${nombre}, ${info.nombre}` : nombre);
    }

    function habilitada(carta) {
        if (carta.classList.contains("volteada") || carta.classList.contains("pendiente")) return false;
        if (performance.now() < esperaHasta) return false;
        return fase === "lista" || (fase === "enviando" && visibles === 0 && !siguiente);
    }

    function actualizarControles() {
        for (const carta of cartas) carta.setAttribute("aria-disabled", String(!habilitada(carta)));
        reintentar.hidden = fase !== "sin-conexion";
    }

    function publicar(datos) {
        document.dispatchEvent(new CustomEvent("sonic:estado", {detail: datos}));
    }

    function liberar() {
        fase = "lista";
        actualizarControles();
        if (esperaHasta > performance.now()) {
            setTimeout(actualizarControles, esperaHasta - performance.now() + 10);
        }
    }

    function reconstruir(datos) {
        const emparejadas = new Map(datos.emparejadas.map(info => [info.posicion, info]));
        const abiertas = new Map(datos.visibles.map(info => [info.posicion, info]));
        for (const [posicion, carta] of cartas.entries()) {
            pintar(carta, emparejadas.get(posicion) || abiertas.get(posicion), emparejadas.has(posicion));
        }
    }

    async function sincronizar() {
        if (consulta || !["lista", "recuperando"].includes(fase)) return;
        consulta = true;
        const version = revision;
        try {
            let datos = await pedir(dataset.estadoUrl);
            if (datos.cierre_pendiente) datos = await enviar(dataset.cierreUrl);
            if (!datos.ok || datos.cierre_pendiente) throw new Error("Estado pendiente");
            if (version !== revision || datos.ultima_secuencia < secuencia) return;

            const inicial = fase !== "lista";
            if (inicial || secuencia !== datos.ultima_secuencia) reconstruir(datos);
            secuencia = datos.ultima_secuencia;
            visibles = datos.visibles.length;
            esperaHasta = performance.now() + datos.espera_ms;
            if (datos.estado === "EN_CURSO") {
                if (inicial) mensaje.textContent = visibles ? "Selecciona otra carta" : "";
                liberar();
            } else {
                fase = "fin";
                actualizarControles();
            }
            publicar(datos);
        } catch {
            if (version === revision && fase !== "lista") sinConexion();
        } finally {
            consulta = false;
            if (version !== revision && fase === "recuperando") sincronizar();
        }
    }

    function sinConexion() {
        fase = "sin-conexion";
        mensaje.textContent = "No se pudo confirmar la conexión. Reintenta para continuar.";
        actualizarControles();
    }

    function iniciarMovimiento(carta) {
        movimiento = {posicion: Number(carta.dataset.posicion), seq_num: secuencia + 1};
        procesar();
    }

    async function procesar() {
        const carta = cartas[movimiento.posicion];
        fase = "enviando";
        revision += 1;
        mensaje.textContent = "Validando jugada…";
        actualizarControles();

        let datos;
        try {
            datos = await enviar(dataset.accionUrl, movimiento);
        } catch {
            sinConexion();
            return;
        }
        const enCola = siguiente;
        siguiente = undefined;
        carta.classList.remove("pendiente");

        if (!datos.ok) {
            movimiento = undefined;
            enCola?.classList.remove("pendiente");
            fase = "recuperando";
            mensaje.textContent = datos.error || "No se pudo validar la jugada.";
            actualizarControles();
            await sincronizar();
            return;
        }

        secuencia = movimiento.seq_num;
        movimiento = undefined;
        visibles = datos.tipo === "primera" ? 1 : 0;
        if (datos.tipo === "primera") {
            pintar(carta, datos.carta);
            mensaje.textContent = "Selecciona otra carta";
        } else {
            const pareja = datos.tipo === "pareja";
            for (const info of datos.cartas) pintar(cartas[info.posicion], info, pareja);
            if (pareja) {
                mensaje.textContent = "¡Pareja encontrada! " + datos.personaje.nombre;
                sonido("acierto");
                window.SonicUI?.mostrarPareja?.({...datos.personaje, imagen: rutaImagen(datos.personaje.imagen)});
            } else {
                mensaje.textContent = "No son pareja";
                sonido("error");
                fase = "comparando";
                actualizarControles();
                await new Promise(resolve => setTimeout(resolve, datos.espera_ms));
                for (const info of datos.cartas) pintar(cartas[info.posicion]);
                mensaje.textContent = "";
            }
        }

        publicar(datos);
        if (datos.estado !== "EN_CURSO") {
            enCola?.classList.remove("pendiente");
            fase = "fin";
            actualizarControles();
        } else if (enCola) {
            iniciarMovimiento(enCola);
        } else {
            liberar();
        }
    }

    function sonido(nombre) {
        window.SonicUI?.reproducir?.(nombre);
    }

    tablero.addEventListener("click", evento => {
        const carta = evento.target.closest(".carta");
        if (!carta || !habilitada(carta)) return;

        carta.classList.add("pendiente");
        if (fase === "enviando") {
            siguiente = carta;
            actualizarControles();
        } else {
            iniciarMovimiento(carta);
        }
        sonido("carta");
    });

    function recuperar() {
        if (fase !== "sin-conexion") return;
        if (movimiento) procesar();
        else {
            fase = "recuperando";
            actualizarControles();
            sincronizar();
        }
    }

    reintentar.addEventListener("click", recuperar);
    window.addEventListener("online", recuperar);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) sincronizar();
    });

    async function decodificarPrevia(imagenes, ms) {
        let limite;
        try {
            await Promise.race([
                Promise.all(imagenes.map(imagen => imagen.decode())),
                new Promise((_, rechazar) => {
                    limite = setTimeout(() => rechazar(new Error("Imágenes de vista previa pendientes")), ms);
                }),
            ]);
        } finally {
            clearTimeout(limite);
        }
    }

    async function animarPrevia(duracion) {
        const giros = cartas.map(carta => carta.querySelector(".carta-giro"));
        const estilo = getComputedStyle(giros[0]);
        const tramo = Math.min(0.5, parseFloat(estilo.transitionDuration) * 1000 / duracion);
        const cerrada = "rotateY(0deg)";
        const abierta = "rotateY(180deg)";
        const fotogramas = tramo > 0 ? [
            {transform: cerrada, offset: 0, easing: estilo.transitionTimingFunction},
            {transform: abierta, offset: tramo},
            {transform: abierta, offset: 1 - tramo, easing: estilo.transitionTimingFunction},
            {transform: cerrada, offset: 1},
        ] : [{transform: abierta}, {transform: abierta}];

        const inicio = document.timeline.currentTime;
        const animaciones = giros.map(giro => {
            const animacion = giro.animate(fotogramas, {duration: duracion});
            animacion.startTime = inicio;
            return animacion;
        });
        await Promise.allSettled(animaciones.map(animacion => animacion.finished));
    }

    async function mostrarPrevia() {
        const rutas = JSON.parse(document.getElementById("imagenes-previa").textContent);
        mensaje.textContent = "Preparando vista previa…";
        const precarga = rutas.map(ruta => {
            const imagen = new Image();
            imagen.src = rutaImagen(ruta);
            return imagen;
        });
        await decodificarPrevia(precarga, 30000);

        const solicitud = performance.now();
        const datos = await enviar(dataset.previaUrl);
        if (!datos.activa) return;
        if (datos.cartas.length !== cartas.length) throw new Error("Vista previa incompleta");

        const caras = datos.cartas.map(info => {
            const imagen = cartas[info.posicion].querySelector(".carta-personaje");
            imagen.src = rutaImagen(info.imagen);
            return imagen;
        });
        try {
            const disponible = datos.restante_ms - (performance.now() - solicitud);
            if (disponible <= 0) return;
            await decodificarPrevia(caras, disponible);

            tablero.classList.add("animando-previa");
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            if (performance.now() - solicitud >= datos.restante_ms) return;

            mensaje.textContent = "¡Memoriza las cartas descubiertas!";
            await animarPrevia(datos.restante_ms);
        } finally {
            tablero.classList.remove("animando-previa");
            for (const imagen of caras) imagen.removeAttribute("src");
        }
        mensaje.textContent = "";
        liberar();
    }

    async function iniciar() {
        if (dataset.previa === "true") {
            try {
                await mostrarPrevia();
            } catch {
                mensaje.textContent = "Vista previa no disponible.";
            }
        }
        if (fase === "inicio") fase = "recuperando";
        await sincronizar();
        setInterval(() => {
            if (!document.hidden) sincronizar();
        }, 5000);
    }

    iniciar();
})();
