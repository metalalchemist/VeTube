// Service worker: la única pieza que habla con VeTube, y ahora también la que
// captura las tramas.
//
// POR QUÉ LA API DE DEPURACIÓN (chrome.debugger) Y NO UN CONTENT SCRIPT:
// para leer las tramas del websocket hay que estar en el contexto de la página
// (mundo MAIN). Pero la CSP de TikTok (script-src sin 'self' ni 'unsafe-inline')
// BLOQUEA los content scripts del mundo MAIN: la documentación de Chrome lo dice
// explícito ("cuando un content script se inyecta en el mundo MAIN, se aplica la
// CSP de la página"), y se comprobó en campo (el inyector nunca arrancaba). La
// API de depuración lee las tramas igual que las DevTools
// (Network.webSocketFrameReceived), SIN inyectar nada en la página, así que es
// inmune a la CSP. Precio: Chrome muestra una barra "está depurando este
// navegador" mientras haya una pestaña de TikTok, y hace falta el permiso
// "debugger".
//
// POR QUÉ EL POST SALE DE AQUÍ: una página de tiktok.com no puede hacer fetch a
// http://127.0.0.1 (Local Network Access lo corta). El service worker sí llega,
// con las host_permissions de la extensión.
"use strict";

importScripts("logica.js");
const L = globalThis.__vetubeLogica;

const BASE = "http://127.0.0.1:8790";
const VERSION_CONTRATO = 2;
const PROTO_DEPURADOR = "1.3";

// El worker muere si un fetch tarda más de 30 s. Con 5 s vamos sobrados para un
// servidor local.
const MS_TIMEOUT = 5000;
// Si VeTube no responde, no gastamos 5 s por lote: se marca caído un rato.
const MS_ENFRIAMIENTO = 3000;

// Agrupado de tramas del lado del worker (antes lo hacía el content script).
const MS_LOTE = 250;
const MAX_LOTE = 20;

// ---------------------------------------------------------------------
// Estado que sobrevive a las siestas del worker
// ---------------------------------------------------------------------
// El worker de MV3 se duerme a los ~30 s de ocio y pierde sus variables. Lo que
// no puede reiniciarse (el contador seq, que el lado Python usa para detectar
// lotes perdidos) vive en chrome.storage.session.
const CLAVE = "estado";

function estadoVacio() {
  return {
    sesiones: {}, // clave -> {unique_id, room_id, ws_url, abiertaMs, tabId}
    seq: {}, // clave -> siguiente seq a usar
    paginas: {}, // tabId -> {unique_id, esDirecto, socketVisto, cuandoMs}
    contadores: {
      tramasEnviadas: 0,
      lotesEnviados: 0,
      lotesFallidos: 0,
      tramasDescartadas: 0,
      ultimaTramaMs: 0,
    },
    vetube: { ok: false, version: 0, ultimoChequeoMs: 0, ultimoError: "" },
    // Diagnóstico de la captura por depurador, para que el popup lo muestre.
    diag: {
      modo: "debugger",
      adjuntas: 0, // pestañas de TikTok con el depurador adjunto
      wsWebcast: 0, // websockets del webcast vistos
      framesWebcast: 0, // tramas del webcast leídas
      ultimoError: "",
    },
    caidoHastaMs: 0,
  };
}

let estado = null;
let cargando = null;

async function cargarEstado() {
  if (estado) return estado;
  if (!cargando) {
    cargando = chrome.storage.session
      .get(CLAVE)
      .then(function (r) {
        estado = Object.assign(estadoVacio(), (r && r[CLAVE]) || {});
        if (!estado.diag || estado.diag.modo !== "debugger") {
          estado.diag = estadoVacio().diag;
        }
        return estado;
      })
      .catch(function () {
        estado = estadoVacio();
        return estado;
      });
  }
  return cargando;
}

function guardarEstado() {
  return chrome.storage.session.set({ [CLAVE]: estado }).catch(function () {
    /* si falla, lo peor que pasa es que el seq se reinicie tras una siesta */
  });
}

// Todo lo que toca seq o postea pasa por esta cadena, para que dos lotes que
// entran a la vez no lean el mismo seq y lo manden repetido (peor que un hueco).
let cadena = Promise.resolve();
function encolar(tarea) {
  cadena = cadena.then(tarea).catch(function (e) {
    console.warn("[VeTube] error en la cola:", String(e));
  });
  return cadena;
}

function seguro(fn) {
  try {
    return fn();
  } catch (e) {
    return null;
  }
}

// ---------------------------------------------------------------------
// Red
// ---------------------------------------------------------------------
async function postear(ruta, cuerpo) {
  const r = await fetch(BASE + ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
    signal: AbortSignal.timeout(MS_TIMEOUT),
  });
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r;
}

async function comprobarSalud() {
  const st = await cargarEstado();
  try {
    const r = await fetch(BASE + "/salud", { signal: AbortSignal.timeout(2000) });
    const datos = await r.json();
    st.vetube = {
      ok: datos && datos.ok === true,
      version: (datos && datos.version) || 0,
      ultimoChequeoMs: Date.now(),
      ultimoError: "",
    };
  } catch (e) {
    st.vetube = {
      ok: false,
      version: 0,
      ultimoChequeoMs: Date.now(),
      ultimoError: String(e && e.message ? e.message : e),
    };
  }
  await guardarEstado();
  return st.vetube;
}

// ---------------------------------------------------------------------
// Sesiones y lotes (contrato con VeTube: /sesion y /tramas)
// ---------------------------------------------------------------------
function claveDbg(tabId, requestId) {
  return "dbg:" + tabId + ":" + requestId;
}

async function abrirSesion(clave, info) {
  const st = await cargarEstado();
  st.sesiones[clave] = {
    unique_id: info.unique_id || "",
    room_id: info.room_id || "",
    ws_url: info.url || "",
    abiertaMs: Date.now(),
    tabId: info.tabId,
  };
  st.seq[clave] = 0;
  st.diag.wsWebcast = (st.diag.wsWebcast || 0) + 1;
  await guardarEstado();
  try {
    await postear("/sesion", {
      unique_id: info.unique_id || "",
      room_id: info.room_id || "",
      estado: "abierto",
      ws_url: info.url || "",
    });
    console.log("[VeTube] sesión abierta para @" + (info.unique_id || "?"));
  } catch (e) {
    console.warn("[VeTube] /sesion abierto no salió:", String(e));
  }
}

async function cerrarSesion(clave, info) {
  const st = await cargarEstado();
  const previa = st.sesiones[clave];
  delete st.sesiones[clave];
  delete st.seq[clave];
  await guardarEstado();
  const uid = (info && info.unique_id) || (previa && previa.unique_id) || "";
  const room = (info && info.room_id) || (previa && previa.room_id) || "";
  try {
    await postear("/sesion", {
      unique_id: uid,
      room_id: room,
      estado: "cerrado",
      ws_url: "",
    });
  } catch (e) {
    console.warn("[VeTube] /sesion cerrado no salió:", String(e));
  }
}

async function enviarLote(clave, info, tramas) {
  const st = await cargarEstado();
  if (!tramas.length) return;
  if (Date.now() < st.caidoHastaMs) {
    st.contadores.tramasDescartadas += tramas.length;
    await guardarEstado();
    return;
  }
  const seq = st.seq[clave] || 0;
  // Se persiste ANTES de postear: si el worker muere en mitad del envío, al
  // volver arranca en el siguiente seq. Un hueco lo detecta Python; un seq
  // repetido lo confundiría de verdad.
  st.seq[clave] = seq + 1;
  await guardarEstado();
  try {
    await postear("/tramas", {
      unique_id: info.unique_id || "",
      room_id: info.room_id || "",
      seq: seq,
      tramas: tramas,
    });
    st.contadores.tramasEnviadas += tramas.length;
    st.contadores.lotesEnviados += 1;
    st.contadores.ultimaTramaMs = Date.now();
    st.diag.framesWebcast = (st.diag.framesWebcast || 0) + tramas.length;
    if (!st.vetube.ok) st.vetube.ok = true;
    st.caidoHastaMs = 0;
  } catch (e) {
    st.contadores.lotesFallidos += 1;
    st.contadores.tramasDescartadas += tramas.length;
    st.vetube.ok = false;
    st.vetube.ultimoError = String(e && e.message ? e.message : e);
    st.caidoHastaMs = Date.now() + MS_ENFRIAMIENTO;
    console.warn("[VeTube] lote perdido:", st.vetube.ultimoError);
  }
  await guardarEstado();
}

// Agrupador en memoria del worker. clave -> {tramas, timer, info}
const lotes = new Map();

function acumularTrama(clave, info, b64) {
  let lote = lotes.get(clave);
  if (!lote) {
    lote = { tramas: [], timer: null, info: info };
    lotes.set(clave, lote);
  }
  lote.info = info;
  lote.tramas.push(b64);
  if (lote.tramas.length >= MAX_LOTE) {
    descargarLote(clave);
  } else if (!lote.timer) {
    lote.timer = setTimeout(function () {
      descargarLote(clave);
    }, MS_LOTE);
  }
}

function descargarLote(clave) {
  const lote = lotes.get(clave);
  if (!lote) return;
  if (lote.timer) {
    clearTimeout(lote.timer);
    lote.timer = null;
  }
  const tramas = lote.tramas;
  lote.tramas = [];
  if (!tramas.length) return;
  const info = lote.info || {};
  encolar(function () {
    return enviarLote(clave, info, tramas);
  });
}

// ---------------------------------------------------------------------
// Captura por API de depuración
// ---------------------------------------------------------------------
const adjuntas = new Set(); // tabIds con el depurador adjunto
const wsPorTab = new Map(); // tabId -> Map(requestId -> {url, esWebcast, room_id, unique_id, tabId})

function esTikTok(url) {
  return typeof url === "string" && /^https?:\/\/([^/]+\.)?tiktok\.com\//i.test(url);
}

function marcarError(texto) {
  encolar(async function () {
    const st = await cargarEstado();
    st.diag.ultimoError = texto;
    st.diag.adjuntas = adjuntas.size;
    await guardarEstado();
  });
}

function adjuntar(tabId) {
  if (tabId == null || adjuntas.has(tabId)) return;
  adjuntas.add(tabId); // optimista; se revierte si falla
  chrome.debugger.attach({ tabId: tabId }, PROTO_DEPURADOR, function () {
    if (chrome.runtime.lastError) {
      adjuntas.delete(tabId);
      // Caso típico: ya hay unas DevTools abiertas en esa pestaña.
      marcarError(String(chrome.runtime.lastError.message || chrome.runtime.lastError));
      return;
    }
    chrome.debugger.sendCommand({ tabId: tabId }, "Network.enable", {}, function () {
      void chrome.runtime.lastError;
      encolar(async function () {
        const st = await cargarEstado();
        st.diag.adjuntas = adjuntas.size;
        await guardarEstado();
      });
    });
  });
}

function limpiarSesionesDeTab(tabId) {
  const mapa = wsPorTab.get(tabId);
  if (!mapa) return;
  mapa.forEach(function (info, requestId) {
    const clave = claveDbg(tabId, requestId);
    descargarLote(clave);
    if (info.esWebcast) {
      encolar(function () {
        return cerrarSesion(clave, info);
      });
    }
  });
  wsPorTab.delete(tabId);
}

// Adjuntar a las pestañas de TikTok que ya estén abiertas al arrancar el worker.
chrome.tabs.query({ url: "*://*.tiktok.com/*" }, function (tabs) {
  if (chrome.runtime.lastError) return;
  (tabs || []).forEach(function (t) {
    adjuntar(t.id);
  });
});

// Adjuntar a las pestañas que naveguen a TikTok. Al empezar a cargar una página
// nueva se cierran las sesiones viejas de esa pestaña (otro directo, u otra
// cosa): sus tramas ya no vienen.
chrome.tabs.onUpdated.addListener(function (tabId, info, tab) {
  const url = (tab && tab.url) || info.url || "";
  if (!esTikTok(url)) return;
  if (info.status === "loading") limpiarSesionesDeTab(tabId);
  adjuntar(tabId);
});

chrome.debugger.onEvent.addListener(function (source, metodo, params) {
  const tabId = source.tabId;
  if (tabId == null || !params) return;

  if (metodo === "Network.webSocketCreated") {
    const esWc = !!seguro(function () {
      return L.esWebSocketDelWebcast(params.url);
    });
    let mapa = wsPorTab.get(tabId);
    if (!mapa) {
      mapa = new Map();
      wsPorTab.set(tabId, mapa);
    }
    const info = {
      url: params.url,
      esWebcast: esWc,
      room_id: seguro(function () {
        return L.sacarRoomId(params.url);
      }) || "",
      unique_id: "",
      tabId: tabId,
    };
    mapa.set(params.requestId, info);
    if (esWc) {
      // El @usuario del directo sale de la ruta de la pestaña; se busca aparte
      // porque la url del websocket no siempre lo trae.
      chrome.tabs.get(tabId, function (tab) {
        void chrome.runtime.lastError;
        const ruta = seguro(function () {
          return new URL(tab && tab.url ? tab.url : "").pathname;
        }) || "";
        info.unique_id = seguro(function () {
          return L.sacarUniqueIdDeRuta(ruta);
        }) || "";
        const clave = claveDbg(tabId, params.requestId);
        encolar(function () {
          return abrirSesion(clave, info);
        });
      });
    }
  } else if (metodo === "Network.webSocketFrameReceived") {
    const mapa = wsPorTab.get(tabId);
    const info = mapa && mapa.get(params.requestId);
    if (!info || !info.esWebcast) return;
    const fr = params.response || {};
    // opcode 2 = binaria (WebcastPushFrame). El texto/ping/pong no interesa.
    // Para binarias, payloadData YA viene en base64: justo lo que espera VeTube.
    if (fr.opcode !== 2) return;
    if (typeof fr.payloadData === "string" && fr.payloadData) {
      acumularTrama(claveDbg(tabId, params.requestId), info, fr.payloadData);
    }
  } else if (metodo === "Network.webSocketClosed") {
    const mapa = wsPorTab.get(tabId);
    const info = mapa && mapa.get(params.requestId);
    if (info) {
      const clave = claveDbg(tabId, params.requestId);
      descargarLote(clave);
      if (info.esWebcast) {
        encolar(function () {
          return cerrarSesion(clave, info);
        });
      }
      mapa.delete(params.requestId);
    }
  }
});

chrome.debugger.onDetach.addListener(function (source, reason) {
  if (source.tabId == null) return;
  adjuntas.delete(source.tabId);
  limpiarSesionesDeTab(source.tabId);
  encolar(async function () {
    const st = await cargarEstado();
    st.diag.adjuntas = adjuntas.size;
    st.diag.ultimoError = "depurador desconectado: " + (reason || "?");
    await guardarEstado();
  });
});

chrome.tabs.onRemoved.addListener(function (tabId) {
  adjuntas.delete(tabId);
  limpiarSesionesDeTab(tabId);
  encolar(async function () {
    const st = await cargarEstado();
    if (st.paginas[tabId]) delete st.paginas[tabId];
    st.diag.adjuntas = adjuntas.size;
    await guardarEstado();
  });
});

// ---------------------------------------------------------------------
// Consultas del popup
// ---------------------------------------------------------------------
chrome.runtime.onMessage.addListener(function (msg, sender, responder) {
  if (!msg || msg.tipo !== "estado") return false;
  (async function () {
    const st = await cargarEstado();
    const salud = await comprobarSalud();
    st.diag.adjuntas = adjuntas.size;
    await guardarEstado();
    const sesiones = Object.keys(st.sesiones).map(function (k) {
      return st.sesiones[k];
    });
    const paginas = Object.keys(st.paginas).map(function (k) {
      return st.paginas[k];
    });
    responder({
      vetube: salud,
      versionEsperada: VERSION_CONTRATO,
      sesiones: sesiones,
      paginas: paginas,
      contadores: st.contadores,
      diag: st.diag || {},
      ahoraMs: Date.now(),
    });
  })();
  return true; // respuesta asíncrona
});

console.log("[VeTube] service worker arrancado (captura por depurador)");
