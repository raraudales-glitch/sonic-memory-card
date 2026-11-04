(function () {
    const BASE_EFECTOS = "/static/memory/audio/efectos/";

    const sonidos = {
        carta: new Audio(BASE_EFECTOS + "carta.wav"),
        acierto: new Audio(BASE_EFECTOS + "acierto.wav"),
        error: new Audio(BASE_EFECTOS + "error.wav"),
        victoria: new Audio(BASE_EFECTOS + "victoria.wav"),
        derrota: new Audio(BASE_EFECTOS + "derrota.wav"),
    };

    function obtenerVolumenEfectos() {
        const guardado = parseInt(
            localStorage.getItem("sonic_volumen_efectos") || "80",
            10
        );

        const valor = isNaN(guardado) ? 80 : guardado;
        return Math.max(0, Math.min(100, valor)) / 100;
    }

    function actualizarVolumenEfectos() {
        const volumen = obtenerVolumenEfectos();

        Object.values(sonidos).forEach((audio) => {
            audio.volume = volumen;
            audio.preload = "auto";
        });
    }

    function reproducir(nombre) {
        const original = sonidos[nombre];
        if (!original) return;

        actualizarVolumenEfectos();

        try {
            const clon = original.cloneNode();
            clon.volume = original.volume;
            clon.play().catch(() => {});
        } catch (error) {
            console.warn("No se pudo reproducir el efecto:", nombre, error);
        }
    }

    let panel = null;
    let ocultarTimer = null;

    function resolverImagen(ruta) {
        if (!ruta) return "";
        if (ruta.startsWith("http://") || ruta.startsWith("https://") || ruta.startsWith("/")) {
            return ruta;
        }
        return "/static/" + ruta;
    }

    function crearPanel() {
        if (panel) return panel;

        const estilo = document.createElement("style");
        estilo.textContent = `
            .sonic-toast-pareja {
                position: fixed;
                top: 95px;
                right: 20px;
                width: 320px;
                max-width: calc(100vw - 30px);
                background: rgba(8, 24, 68, 0.96);
                border: 2px solid #ffd900;
                border-radius: 18px;
                box-shadow:
                    0 12px 28px rgba(0,0,0,0.35),
                    0 0 20px rgba(0,180,255,0.25);
                padding: 18px 18px 16px;
                z-index: 9999;
                transform: translateX(120%);
                opacity: 0;
                transition: transform 0.35s ease, opacity 0.35s ease;
                pointer-events: none;
            }

            .sonic-toast-pareja.mostrar {
                transform: translateX(0);
                opacity: 1;
            }

            .sonic-toast-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                margin-bottom: 10px;
            }

            .sonic-toast-titulo {
                color: #8fe6ff;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 1px;
                text-transform: uppercase;
            }

            .sonic-toast-cerrar {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                line-height: 1;
                pointer-events: auto;
            }

            .sonic-toast-body {
                display: flex;
                gap: 14px;
                align-items: center;
            }

            .sonic-toast-img {
                width: 96px;
                height: 96px;
                object-fit: contain;
                flex-shrink: 0;
                filter: drop-shadow(0 0 8px rgba(0,255,180,0.35));
            }

            .sonic-toast-info {
                min-width: 0;
                text-align: left;
            }

            .sonic-toast-nombre {
                color: #ffd900;
                font-size: 28px;
                font-weight: 900;
                line-height: 1;
                margin-bottom: 10px;
                text-shadow: 0 0 10px rgba(255,217,0,0.25);
            }

            .sonic-toast-frase {
                color: #ffffff;
                font-size: 16px;
                line-height: 1.35;
                font-style: italic;
                opacity: 0.95;
            }

            @media (max-width: 700px) {
                .sonic-toast-pareja {
                    top: auto;
                    bottom: 16px;
                    right: 12px;
                    left: 12px;
                    width: auto;
                }

                .sonic-toast-body {
                    gap: 10px;
                }

                .sonic-toast-img {
                    width: 78px;
                    height: 78px;
                }

                .sonic-toast-nombre {
                    font-size: 22px;
                }

                .sonic-toast-frase {
                    font-size: 14px;
                }
            }
        `;
        document.head.appendChild(estilo);

        panel = document.createElement("div");
        panel.className = "sonic-toast-pareja";
        panel.innerHTML = `
            <div class="sonic-toast-header">
                <div class="sonic-toast-titulo">¡Pareja encontrada!</div>
                <button type="button" class="sonic-toast-cerrar" aria-label="Cerrar">×</button>
            </div>
            <div class="sonic-toast-body">
                <img class="sonic-toast-img" src="" alt="">
                <div class="sonic-toast-info">
                    <div class="sonic-toast-nombre"></div>
                    <div class="sonic-toast-frase"></div>
                </div>
            </div>
        `;

        document.body.appendChild(panel);

        panel.querySelector(".sonic-toast-cerrar").addEventListener("click", ocultarPanel);

        return panel;
    }

    function ocultarPanel() {
        if (!panel) return;
        panel.classList.remove("mostrar");
    }

    function mostrarPareja(personaje, callback) {
        crearPanel();

        const imagen = panel.querySelector(".sonic-toast-img");
        const nombre = panel.querySelector(".sonic-toast-nombre");
        const frase = panel.querySelector(".sonic-toast-frase");

        imagen.src = resolverImagen(personaje.imagen || "");
        imagen.alt = personaje.nombre || "Personaje";
        nombre.textContent = personaje.nombre || "Personaje";
        frase.textContent = personaje.frase || "";

        panel.classList.add("mostrar");

        clearTimeout(ocultarTimer);
        ocultarTimer = setTimeout(() => {
            ocultarPanel();
        }, 3000);

        if (typeof callback === "function") {
            callback();
        }
    }

    actualizarVolumenEfectos();

    window.SonicUI = window.SonicUI || {};
    window.SonicUI.reproducir = reproducir;
    window.SonicUI.mostrarPareja = mostrarPareja;
    window.SonicUI.actualizarVolumenEfectos = actualizarVolumenEfectos;
})();