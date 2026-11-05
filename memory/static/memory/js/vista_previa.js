
(() => {
    "use strict";

    const id = document.body.dataset.partidaId;
    const tablero = document.querySelector(".tablero");

    if (!id || !tablero) return;

    bloqueado = true;

    const mensaje = document.getElementById("mensaje-juego");
    const staticBase = document.body.dataset.staticBase || "/static/";
    const tapa = document.body.dataset.tapa;
    const cartas = [...tablero.querySelectorAll(".carta")];
    const controlador = new AbortController();

    let vencimiento = 0;

    function restaurar() {
        controlador.abort();

        cartas.forEach(carta => {
            if (!carta.classList.contains("sonic-previa")) {
                return;
            }

            const imagen = carta.querySelector("img");

            if (imagen) {
                imagen.src = tapa;
                imagen.alt = "Carta boca abajo";
                imagen.style.objectFit = "cover";
                imagen.style.background = "transparent";
            }

            carta.classList.remove(
                "sonic-previa",
                "volteada"
            );
        });

        if (mensaje?.dataset.vistaPrevia === "1") {
            mensaje.textContent = "";
            delete mensaje.dataset.vistaPrevia;
        }

        bloqueado = false;
    }

    async function iniciar() {
        try {
            const respuesta = await fetch(
                `/partidas/${id}/vista-previa/`,
                {
                    credentials: "same-origin",
                    cache: "no-store"
                }
            );

            if (!respuesta.ok) {
                throw new Error(`HTTP ${respuesta.status}`);
            }

            const datos = await respuesta.json();

            if (!datos.activa || datos.restante_ms <= 0) {
                return;
            }

            vencimiento = Date.now() + datos.restante_ms;

            if (mensaje) {
                mensaje.dataset.vistaPrevia = "1";
                mensaje.textContent =
                    "¡Memoriza la ubicación de las cartas!";
            }

            cartas.forEach(async carta => {
                const posicion = Number(
                    carta.dataset.posicion
                );

                try {
                    const respuestaCarta = await fetch(
                        `/partidas/${id}/vista-previa/${posicion}/`,
                        {
                            credentials: "same-origin",
                            cache: "no-store",
                            signal: controlador.signal
                        }
                    );

                    if (!respuestaCarta.ok) return;

                    const info = await respuestaCarta.json();

                    if (Date.now() >= vencimiento) return;

                    const imagen = carta.querySelector("img");

                    if (!imagen) return;

                    imagen.src = info.imagen.startsWith("/")
                        ? info.imagen
                        : staticBase + info.imagen;

                    imagen.alt = info.nombre;
                    imagen.style.objectFit = "contain";
                    imagen.style.background = "rgba(8,12,25,.96)";

                    carta.classList.add(
                        "sonic-previa",
                        "volteada"
                    );

                } catch (error) {
                    if (error.name !== "AbortError") {
                        console.warn(
                            "No se pudo mostrar la carta:",
                            error
                        );
                    }
                }
            });

            await new Promise(resolve => {
                setTimeout(
                    resolve,
                    Math.max(0, vencimiento - Date.now())
                );
            });

        } catch (error) {
            console.warn(
                "Vista previa no disponible:",
                error
            );
        } finally {
            restaurar();
        }
    }

    iniciar();
})();
