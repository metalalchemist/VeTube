// Lógica pura del puente: nada de aquí toca el DOM, ni chrome.*, ni la red.
//
// ¿Por qué un archivo aparte? Porque la parte que más fácil se rompe en
// silencio (qué websocket se acepta, cómo se agrupan las tramas, cómo avanza
// el contador seq) es justo la que no se puede probar dentro de Chrome sin
// abrir un directo real. Sacándola aquí, `pruebas/pruebas.js` la ejercita con
// Node en un segundo y sin navegador. Eso es parte del diseño, no un extra.
//
// El mismo archivo se carga en tres sitios distintos:
//   - mundo MAIN de la página (inject.js)      -> vía globalThis.__vetubeLogica
//   - mundo aislado del content script         -> vía globalThis.__vetubeLogica
//   - Node, en el banco de pruebas             -> vía module.exports
"use strict";

(function (raiz, fabrica) {
  const api = fabrica();

  // OJO: no se detecta Node con `typeof module === "object"`. La página de
  // TikTok trae bundles que a veces definen un `module` global propio, y si
  // nos colásemos por esa rama la API nunca quedaría publicada y inject.js se
  // quedaría sin lógica. `process.versions.node` sí es exclusivo de Node.
  const enNode =
    typeof process !== "undefined" &&
    !!(process.versions && process.versions.node);

  if (enNode) {
    module.exports = api;
    return;
  }

  // No enumerable: en el mundo MAIN esto vive un instante en el `window` de la
  // página (inject.js lo lee y lo borra acto seguido), así que cuanto menos
  // visible sea para el código de TikTok, mejor.
  try {
    Object.defineProperty(raiz, "__vetubeLogica", {
      value: api,
      configurable: true,
      enumerable: false,
      writable: false,
    });
  } catch (e) {
    raiz.__vetubeLogica = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  // ---------------------------------------------------------------------
  // 1. Filtro de host
  // ---------------------------------------------------------------------

  // Dato de campo: el websocket del chat del directo es
  //   wss://webcast-ws.tiktok.com/webcast/im/ws_proxy/ws_reuse_supplement/...
  // y en la misma pestaña convive otro websocket SIN relación,
  //   wss://im-ws-sg.tiktok.com/ws/v2   (mensajería privada).
  // Un filtro laxo por "im" o por "ws" deja pasar el segundo, que no trae
  // chat del directo y sólo ensuciaría a VeTube. Por eso el filtro es por
  // HOST y exige que la primera etiqueta del dominio empiece por "webcast".
  //
  // Se acepta cualquier `webcast*.tiktok.com` (TikTok reparte por región:
  // webcast16-ws-useast1a.tiktok.com y parecidos) pero nada más.
  function esHostDeTikTok(host) {
    const h = String(host || "").toLowerCase();
    // Comprobación de sufijo de verdad: "evil-tiktok.com" no es tiktok.com.
    return h === "tiktok.com" || h.endsWith(".tiktok.com");
  }

  function esWebSocketDelWebcast(url) {
    let u;
    try {
      u = new URL(String(url));
    } catch (e) {
      return false;
    }
    if (u.protocol !== "wss:" && u.protocol !== "ws:") return false;
    if (!esHostDeTikTok(u.hostname)) return false;
    const primeraEtiqueta = u.hostname.toLowerCase().split(".")[0];
    return primeraEtiqueta.indexOf("webcast") === 0;
  }

  // Señal secundaria, sólo para diagnóstico en el popup: la ruta del webcast.
  // NO se usa para aceptar o descartar, porque TikTok ya cambió la ruta una vez
  // (/webcast/im/ws/ -> /webcast/im/ws_proxy/ws_reuse_supplement/) y no quiero
  // que un cambio así deje a la usuaria sin chat.
  function esRutaDeWebcast(url) {
    try {
      return new URL(String(url)).pathname.indexOf("/webcast/im/ws") === 0;
    } catch (e) {
      return false;
    }
  }

  // ---------------------------------------------------------------------
  // 2. Identidad del directo
  // ---------------------------------------------------------------------

  function sacarRoomId(url) {
    try {
      return new URL(String(url)).searchParams.get("room_id") || "";
    } catch (e) {
      return "";
    }
  }

  // El room_id de la query es el de la sala INICIAL: como la conexión se
  // reutiliza entre salas (ws_reuse_supplement), después de cambiar de directo
  // queda desactualizado. El @usuario de la ruta, en cambio, siempre es el de
  // la sala que se está viendo ahora, así que es el dato autoritativo.
  function sacarUniqueIdDeRuta(pathname) {
    const m = String(pathname || "").match(/\/@([^/?#]+)/);
    if (!m) return "";
    try {
      return decodeURIComponent(m[1]);
    } catch (e) {
      return m[1];
    }
  }

  function esRutaDeDirecto(pathname) {
    return /\/@[^/?#]+\/live/.test(String(pathname || ""));
  }

  // ---------------------------------------------------------------------
  // 3. Base64
  // ---------------------------------------------------------------------
  // Las tramas llegan como Blob (binaryType "blob"); se pasan a ArrayBuffer y
  // de ahí a base64 porque chrome.runtime.sendMessage y los puertos serializan
  // como JSON: un ArrayBuffer o un Uint8Array NO sobreviven ese salto (llegan
  // como {} o como un objeto con claves numéricas). base64 es el único formato
  // que cruza intacto y que además es exactamente lo que pide el contrato.

  const TROZO = 0x8000; // fromCharCode.apply se ahoga con arrays enormes

  function arrayBufferABase64(buf) {
    const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
    let binario = "";
    for (let i = 0; i < bytes.length; i += TROZO) {
      binario += String.fromCharCode.apply(null, bytes.subarray(i, i + TROZO));
    }
    return btoa(binario);
  }

  // Sólo la usan las pruebas (y el diagnóstico), pero vive aquí para que la ida
  // y la vuelta se prueben contra la misma implementación.
  function base64AUint8(texto) {
    const binario = atob(String(texto));
    const salida = new Uint8Array(binario.length);
    for (let i = 0; i < binario.length; i++) salida[i] = binario.charCodeAt(i);
    return salida;
  }

  // ---------------------------------------------------------------------
  // 4. Agrupador de tramas (lotes)
  // ---------------------------------------------------------------------
  // Dato de campo: 24 tramas en ~10 s en un directo mediano, de 132 a 6423
  // bytes. Un POST por trama serían ~2,4 peticiones por segundo a VeTube y un
  // ida y vuelta de puerto por cada una: derroche puro. Se agrupa por tiempo
  // (maxMs) y por cantidad (maxTramas), lo que llegue antes.
  //
  // Los temporizadores se inyectan para que las pruebas puedan usar un reloj
  // falso y no depender de esperas reales.
  function crearAgrupador(opciones) {
    const cfg = Object.assign(
      {
        maxTramas: 20, // descarga al juntar esta cantidad
        maxMs: 250, // ...o al pasar este tiempo desde la primera trama
        maxTramasBuffer: 600, // tope duro de memoria (cantidad)
        maxBytesBuffer: 2 * 1024 * 1024, // tope duro de memoria (bytes de base64)
        alDescargar: function () {},
        alDescartar: function () {},
        programar: function (fn, ms) {
          return setTimeout(fn, ms);
        },
        cancelar: function (id) {
          clearTimeout(id);
        },
      },
      opciones || {}
    );

    let buffer = [];
    let bytes = 0;
    let temporizador = null;
    let descartadas = 0;
    let recibidas = 0;

    function pararTemporizador() {
      if (temporizador !== null) {
        cfg.cancelar(temporizador);
        temporizador = null;
      }
    }

    // Si el buffer se pasa del tope se tiran las tramas MÁS VIEJAS. Para un
    // lector de chat en vivo lo que importa es lo que se está diciendo ahora:
    // guardar lo viejo sólo alarga el retraso hasta hacerlo inservible.
    function podar() {
      let tiradas = 0;
      while (
        buffer.length > cfg.maxTramasBuffer ||
        (bytes > cfg.maxBytesBuffer && buffer.length > 0)
      ) {
        const vieja = buffer.shift();
        bytes -= vieja.length;
        tiradas++;
      }
      if (tiradas > 0) {
        descartadas += tiradas;
        cfg.alDescartar(tiradas, descartadas);
      }
      return tiradas;
    }

    function descargar() {
      pararTemporizador();
      if (buffer.length === 0) return null;
      const lote = buffer;
      buffer = [];
      bytes = 0;
      cfg.alDescargar(lote);
      return lote;
    }

    function agregar(tramaB64) {
      if (typeof tramaB64 !== "string" || tramaB64.length === 0) return false;
      recibidas++;
      buffer.push(tramaB64);
      bytes += tramaB64.length;
      podar();

      if (buffer.length >= cfg.maxTramas) {
        descargar();
      } else if (temporizador === null && buffer.length > 0) {
        temporizador = cfg.programar(function () {
          temporizador = null;
          descargar();
        }, cfg.maxMs);
      }
      return true;
    }

    // Al devolver tramas que no se pudieron entregar (puerto caído, VeTube sin
    // responder) se meten POR DELANTE para no alterar el orden de llegada: el
    // lado Python parsea protobuf y el orden importa.
    function devolver(lote) {
      if (!lote || lote.length === 0) return;
      buffer = lote.concat(buffer);
      for (let i = 0; i < lote.length; i++) bytes += lote[i].length;
      podar();
    }

    function estado() {
      return {
        enBuffer: buffer.length,
        bytes: bytes,
        descartadas: descartadas,
        recibidas: recibidas,
      };
    }

    function vaciar() {
      pararTemporizador();
      buffer = [];
      bytes = 0;
    }

    return {
      agregar: agregar,
      descargar: descargar,
      devolver: devolver,
      estado: estado,
      vaciar: vaciar,
      config: cfg,
    };
  }

  // ---------------------------------------------------------------------
  // 5. Contador seq
  // ---------------------------------------------------------------------
  // El contrato pide un entero monotónico POR SESIÓN. Aquí "seq" numera LOTES,
  // no tramas: con `tramas` siendo una lista, un seq por trama sería ambiguo
  // (¿la primera?, ¿la última?), mientras que numerar el lote le deja al lado
  // Python una comprobación trivial: si el seq que llega no es el anterior + 1,
  // se perdió un lote.
  //
  // Una "sesión" es (socket interceptado + @usuario que se está viendo). Como
  // el socket se reutiliza entre salas, al cambiar de directo se cierra una
  // sesión y se abre otra, y el contador vuelve a 0 para la nueva.
  function crearContadorSeq(inicial) {
    let n = Number(inicial) || 0;
    return {
      siguiente: function () {
        return n++;
      },
      valor: function () {
        return n;
      },
      fijar: function (v) {
        n = Number(v) || 0;
      },
    };
  }

  function claveDeSesion(idSocket, uniqueId) {
    return String(idSocket || "?") + "|" + String(uniqueId || "");
  }

  // ---------------------------------------------------------------------
  // 6. Cookies
  // ---------------------------------------------------------------------
  // Lista blanca cerrada. Está comprobado en campo que con user_is_login=false
  // el directo y su chat funcionan igual, así que no hay ningún motivo para
  // que `sessionid` (la llave completa de la cuenta) salga del navegador.
  const COOKIES_PERMITIDAS = ["ttwid", "tt-target-idc"];

  function filtrarCookies(listaDeCookies) {
    const salida = {};
    const lista = listaDeCookies || [];
    for (let i = 0; i < lista.length; i++) {
      const c = lista[i];
      if (!c || !c.name) continue;
      if (COOKIES_PERMITIDAS.indexOf(c.name) !== -1) salida[c.name] = c.value;
    }
    return salida;
  }

  return {
    esWebSocketDelWebcast: esWebSocketDelWebcast,
    esRutaDeWebcast: esRutaDeWebcast,
    esHostDeTikTok: esHostDeTikTok,
    sacarRoomId: sacarRoomId,
    sacarUniqueIdDeRuta: sacarUniqueIdDeRuta,
    esRutaDeDirecto: esRutaDeDirecto,
    arrayBufferABase64: arrayBufferABase64,
    base64AUint8: base64AUint8,
    crearAgrupador: crearAgrupador,
    crearContadorSeq: crearContadorSeq,
    claveDeSesion: claveDeSesion,
    filtrarCookies: filtrarCookies,
    COOKIES_PERMITIDAS: COOKIES_PERMITIDAS,
  };
});
