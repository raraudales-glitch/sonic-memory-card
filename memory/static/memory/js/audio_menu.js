(() => {
  'use strict';

  const sonido = new Audio('/static/memory/audio/musica/menu.mp3');
  sonido.loop = true;
  sonido.preload = 'auto';

  async function iniciar() {
    const volumenGuardado = localStorage.getItem('sonic_panel_musica_vol')
      ?? localStorage.getItem('sonic_volumen');
    const silenciado = (localStorage.getItem('sonic_panel_musica_mute')
      ?? localStorage.getItem('sonic_silencio')) === '1';
    const volumen = Number(volumenGuardado ?? 65);
    sonido.volume = silenciado ? 0 : Math.max(0, Math.min(100, Number.isFinite(volumen) ? volumen : 65)) / 100;

    if (sonido.volume === 0 || !sonido.paused) return;
    try {
      await sonido.play();
    } catch (error) {
      if (error.name !== 'NotAllowedError') {
        console.warn('No se pudo reproducir la m?sica del men?.', error);
      }
    }
  }

  iniciar();
  document.addEventListener('pointerdown', iniciar, {capture: true});
  document.addEventListener('keydown', iniciar, {capture: true});
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) iniciar();
  });
  window.addEventListener('sonic:preferencias', iniciar);
})();
