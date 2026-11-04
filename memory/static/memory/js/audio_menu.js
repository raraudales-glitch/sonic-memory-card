(() => {
  'use strict';
  const sonido = new Audio('/static/memory/audio/musica/menu.mp3');
  sonido.loop = true;
  sonido.preload = 'auto';
  let volumen = Math.max(0, Math.min(100, Number(localStorage.getItem('sonic_volumen') ?? 65)));
  let silenciado = localStorage.getItem('sonic_silencio') === '1';
  let pausadoPorUsuario = false;
  sonido.volume = silenciado ? 0 : volumen / 100;

  const panel = document.querySelector('.panel') || document.querySelector('main') || document.body;
  const fila = document.createElement('div');
  fila.style.cssText = 'display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;margin:18px auto;color:white';
  const boton = document.createElement('button');
  boton.type = 'button';
  boton.style.cssText = 'border:0;background:#ffdc2b;color:#10203e;border-radius:8px;padding:11px;font-weight:800;cursor:pointer';
  const deslizador = document.createElement('input');
  deslizador.type = 'range';
  deslizador.min = '0'; deslizador.max = '100';
  deslizador.value = String(volumen);
  deslizador.style.width = '140px';
  deslizador.setAttribute('aria-label', 'Volumen de la música');
  const aviso = document.createElement('span');
  aviso.style.cssText = 'font:12px Arial,sans-serif;color:#b9d9ff';

  function actualizarBoton() {
    boton.textContent = silenciado ? 'Activar música' : (sonido.paused ? 'Reproducir música' : 'Pausar música');
  }
  async function iniciar() {
    if (silenciado || pausadoPorUsuario || volumen === 0) { actualizarBoton(); return; }
    sonido.volume = volumen / 100;
    if (!sonido.paused) { actualizarBoton(); return; }
    try {
      await sonido.play();
      aviso.textContent = '';
    } catch (error) {
      aviso.textContent = 'El navegador puede pedir un clic para activar el audio.';
      console.info('Autoplay no disponible: se activará en el primer clic o tecla.', error.name);
    }
    actualizarBoton();
  }

  boton.addEventListener('click', () => {
    if (silenciado) {
      silenciado = false; pausadoPorUsuario = false;
      localStorage.setItem('sonic_silencio', '0');
      iniciar();
      return;
    }
    if (sonido.paused) { pausadoPorUsuario = false; iniciar(); }
    else { pausadoPorUsuario = true; sonido.pause(); actualizarBoton(); }
  });
  deslizador.addEventListener('input', () => {
    volumen = Number(deslizador.value);
    localStorage.setItem('sonic_volumen', String(volumen));
    sonido.volume = silenciado ? 0 : volumen / 100;
    if (volumen > 0) iniciar();
  });
  fila.append(boton, deslizador, aviso);
  panel.appendChild(fila);
  actualizarBoton();

  iniciar();
  document.addEventListener('pointerdown', (evento) => { if (!boton.contains(evento.target) && sonido.paused) iniciar(); }, {capture:true});
  document.addEventListener('keydown', (evento) => { if (!boton.contains(evento.target) && sonido.paused) iniciar(); }, {capture:true});
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && sonido.paused && !pausadoPorUsuario) iniciar();
  });
  window.SonicMenuAudio = {iniciar, sonido};
})();
