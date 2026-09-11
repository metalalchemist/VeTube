// Popup de estado. Pensado para leerse con NVDA: todo lo que importa está
// escrito con palabras, no con colores ni con iconos, y el resumen se anuncia
// una sola vez (al abrir y al pulsar "Actualizar estado"), nunca en bucle.
"use strict";

const L = globalThis.__vetubeLogica;

const $ = function (id) {
  return document.getElementById(id);
};

// Anunciar en la región viva. Se vacía y se vuelve a poner con un respiro para
// forzar una mutación: si el texto nuevo fuese idéntico al viejo, algunos
// lectores no dirían nada y la usuaria se quedaría sin saber si el botón hizo
// algo o no.
function anunciar(texto) {
  const el = $("resumen");
  el.textContent = "";
  setTimeout(function () {
    el.textContent = texto;
  }, 60);
}

function hace(ahoraMs, cuandoMs) {
  if (!cuandoMs) return null;
  const s = Math.max(0, Math.round((ahoraMs - cuandoMs) / 1000));
  if (s < 60) return "hace " + s + " segundo" + (s === 1 ? "" : "s");
  const m = Math.round(s / 60);
  return "hace " + m + " minuto" + (m === 1 ? "" : "s");
}

function pintarLista(lineas) {
  const ul = $("detalle");
  ul.textContent = "";
  lineas.forEach(function (linea) {
    const li = document.createElement("li");
    li.textContent = linea;
    ul.appendChild(li);
  });
}

async function pestanaActiva() {
  try {
    const pestanas = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    return pestanas && pestanas[0] ? pestanas[0] : null;
  } catch (e) {
    return null;
  }
}

// La url de la pestaña sólo llega si la extensión tiene permiso de host para
// ella; como sólo lo pedimos para tiktok.com, en cualquier otra página esto
// devuelve null y el popup no se entera de por dónde anda la usuaria. Es la
// consecuencia buena de pedir permisos mínimos.
function rutaDePestana(pestana) {
  if (!pestana || !pestana.url) return null;
  try {
    return new URL(pestana.url).pathname;
  } catch (e) {
    return null;
  }
}

async function refrescar(porPeticion) {
  let est = null;
  try {
    est = await chrome.runtime.sendMessage({ tipo: "estado" });
  } catch (e) {
    pintarLista(["No se pudo hablar con la extensión: " + String(e)]);
    anunciar("Error: la extensión no responde. Probá a recargarla desde chrome://extensions.");
    return;
  }
  if (!est) {
    pintarLista(["La extensión no devolvió estado."]);
    anunciar("Error: la extensión no devolvió estado.");
    return;
  }

  const pestana = await pestanaActiva();
  const ruta = rutaDePestana(pestana);
  const enDirecto = ruta ? L.esRutaDeDirecto(ruta) : false;
  const usuarioDeLaPestana = ruta ? L.sacarUniqueIdDeRuta(ruta) : "";

  const sesiones = est.sesiones || [];
  const enganchado = sesiones.length > 0;
  const c = est.contadores || {};
  const v = est.vetube || {};

  // ---- detalle -------------------------------------------------------
  const lineas = [];

  if (v.ok) {
    if (v.version === est.versionEsperada) {
      lineas.push("VeTube escuchando: sí, en el puerto 8790 (contrato versión " + v.version + ").");
    } else {
      lineas.push(
        "VeTube escuchando: sí, pero con el contrato versión " +
          (v.version || "desconocida") +
          " y esta extensión habla la " +
          est.versionEsperada +
          ". Actualizá VeTube o la extensión."
      );
    }
  } else {
    lineas.push(
      "VeTube escuchando: no. " +
        (v.ultimoError ? "Detalle: " + v.ultimoError + "." : "") +
        " Abrí VeTube y poné en marcha el directo de TikTok."
    );
  }

  if (enganchado) {
    const nombres = sesiones
      .map(function (s) {
        return "@" + (s.unique_id || "(sin usuario)");
      })
      .join(", ");
    lineas.push("Websocket del webcast: enganchado a " + nombres + ".");
  } else {
    lineas.push("Websocket del webcast: no enganchado a ningún directo.");
  }

  lineas.push("Tramas enviadas a VeTube: " + (c.tramasEnviadas || 0) + ".");
  lineas.push("Lotes enviados: " + (c.lotesEnviados || 0) + ".");
  lineas.push(
    "Tramas descartadas: " +
      (c.tramasDescartadas || 0) +
      (c.tramasDescartadas ? " (VeTube no las recibió)." : ".")
  );

  const cuando = hace(est.ahoraMs, c.ultimaTramaMs);
  lineas.push("Última trama enviada: " + (cuando ? cuando + "." : "todavía ninguna."));

  const dg0 = est.diag || {};
  lineas.push(
    "Captura por depurador: " + (dg0.adjuntas || 0) + " pestana(s) de TikTok enganchada(s). " +
      "Websockets del webcast vistos: " + (dg0.wsWebcast || 0) + ". " +
      "Tramas del chat leidas: " + (dg0.framesWebcast || 0) + "." +
      (dg0.ultimoError ? " Ultimo aviso del depurador: " + dg0.ultimoError + "." : "")
  );

  pintarLista(lineas);

  // ---- aviso de recarga ---------------------------------------------
  // Caso 5(a): la conexión se reutiliza entre salas, así que si la extensión
  // se cargó (o se actualizó) con el directo ya abierto, ese socket ya existía
  // y el envoltorio no llegó a verlo nacer. No hay forma de engancharse a
  // posteriori: sólo recargar.
  const yaEnganchadaEsta = sesiones.some(function (s) {
    return s.unique_id === usuarioDeLaPestana;
  });
  const hayQueRecargar = enDirecto && !yaEnganchadaEsta;

  $("aviso-recarga").hidden = !hayQueRecargar;
  if (hayQueRecargar) {
    $("texto-aviso").textContent =
      "Estás en el directo de @" +
      (usuarioDeLaPestana || "este usuario") +
      ", pero la extensión no llegó a ver abrirse su websocket. Pasa cuando el " +
      "directo ya estaba abierto antes de que la extensión se enganchara. " +
      "Recargá la página del directo y volverá a engancharse.";
  }

  // ---- resumen hablado ----------------------------------------------
  let resumen;
  if (!v.ok) {
    resumen = "VeTube no responde en el puerto 8790. Abrilo y volvé a comprobar.";
  } else if (hayQueRecargar) {
    resumen = "Hace falta recargar la página del directo para engancharse.";
  } else if (!enganchado) {
    resumen = "VeTube escucha. Todavía no hay ningún directo enganchado: abrí un directo de TikTok.";
  } else {
    resumen =
      "Todo en marcha. Enganchado a @" +
      (sesiones[0].unique_id || "un directo") +
      ", " +
      (c.tramasEnviadas || 0) +
      " tramas enviadas.";
  }
  anunciar(porPeticion ? "Estado actualizado. " + resumen : resumen);

  // ---- diagnóstico ---------------------------------------------------
  // Sin la ws_url completa: lleva la firma X-Bogus. Van los nombres y la
  // forma, que es lo que sirve para depurar y lo que se puede pegar entero en
  // un informe sin regalar nada.
  const diag = [
    "VeTube, puente del chat de TikTok",
    "VeTube escuchando: " + (v.ok ? "sí" : "no") + " (versión " + (v.version || 0) + ", esperada " + est.versionEsperada + ")",
    "Último error de red: " + (v.ultimoError || "ninguno"),
    "Sesiones abiertas: " + sesiones.length,
  ];
  sesiones.forEach(function (s) {
    let host = "?";
    let ruta_ws = "?";
    let params = "?";
    try {
      const u = new URL(s.ws_url);
      host = u.hostname;
      ruta_ws = u.pathname;
      params = Array.from(u.searchParams.keys()).sort().join(",");
    } catch (e) {
      /* sin url utilizable */
    }
    diag.push("  @" + s.unique_id + " room_id=" + (s.room_id || "?"));
    diag.push("    host=" + host + " ruta=" + ruta_ws);
    diag.push("    params=" + params);
  });
  diag.push("Tramas enviadas: " + (c.tramasEnviadas || 0));
  diag.push("Lotes enviados: " + (c.lotesEnviados || 0));
  diag.push("Lotes fallidos: " + (c.lotesFallidos || 0));
  const dgx = est.diag || {};
  diag.push("Captura: por depurador (chrome.debugger)");
  diag.push("Pestanas enganchadas: " + (dgx.adjuntas || 0));
  diag.push("Websockets del webcast vistos: " + (dgx.wsWebcast || 0));
  diag.push("Tramas del chat leidas: " + (dgx.framesWebcast || 0));
  diag.push("Ultimo aviso del depurador: " + (dgx.ultimoError || "ninguno"));
  diag.push("Tramas descartadas: " + (c.tramasDescartadas || 0));
  diag.push("Pestaña actual es un directo: " + (enDirecto ? "sí" : "no"));
  $("diag").value = diag.join("\n");
}

$("actualizar").addEventListener("click", function () {
  refrescar(true);
});

$("recargar").addEventListener("click", async function () {
  const pestana = await pestanaActiva();
  if (!pestana) {
    anunciar("No se encontró la pestaña activa.");
    return;
  }
  try {
    await chrome.tabs.reload(pestana.id);
    window.close(); // el popup ya no pinta nada: la página se está recargando
  } catch (e) {
    anunciar("No se pudo recargar la pestaña: " + String(e));
  }
});

$("copiar").addEventListener("click", async function () {
  try {
    await navigator.clipboard.writeText($("diag").value);
    anunciar("Diagnóstico copiado al portapapeles.");
  } catch (e) {
    // Plan B que no depende de ningún permiso: el texto ya está en un cuadro
    // de sólo lectura, así que se le lleva el foco y se selecciona entero.
    $("diag").focus();
    $("diag").select();
    anunciar(
      "No se pudo copiar automáticamente. El diagnóstico está seleccionado: pulsá Control+C."
    );
  }
});

refrescar(false);
