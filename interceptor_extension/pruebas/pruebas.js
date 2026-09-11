// Banco de pruebas de la lógica pura del puente. Se ejecuta SIN Chrome:
//
//     node pruebas/pruebas.js
//
// Cubre lo que se rompe en silencio y no se ve hasta que la usuaria está
// delante de un directo: el filtro de host (que el websocket de la mensajería
// privada NO se cuele), el ida y vuelta a base64, el agrupado en lotes con su
// tope de memoria, el contador seq y la lista blanca de cookies.
"use strict";

const path = require("path");
const fs = require("fs");
const assert = require("assert");

const RAIZ = path.join(__dirname, "..");
const L = require(path.join(RAIZ, "logica.js"));

// ---------------------------------------------------------------------
// Corredor mínimo (nada de dependencias: la extensión no tiene build)
// ---------------------------------------------------------------------
let pasadas = 0;
const fallos = [];

function prueba(nombre, fn) {
  try {
    fn();
    pasadas++;
    console.log("  OK   " + nombre);
  } catch (e) {
    fallos.push({ nombre: nombre, error: e });
    console.log("  FALLA " + nombre);
    console.log("        " + (e && e.message ? e.message : e));
  }
}

function grupo(titulo) {
  console.log("\n" + titulo);
}

// Reloj falso: el agrupador recibe sus temporizadores por parámetro justo para
// que aquí no haya que esperar de verdad ni un milisegundo.
function crearReloj() {
  let ahora = 0;
  let siguienteId = 0;
  const tareas = new Map();
  return {
    programar: function (fn, ms) {
      const id = ++siguienteId;
      tareas.set(id, { fn: fn, cuando: ahora + ms });
      return id;
    },
    cancelar: function (id) {
      tareas.delete(id);
    },
    avanzar: function (ms) {
      ahora += ms;
      const vencidas = Array.from(tareas.entries())
        .filter(function (par) {
          return par[1].cuando <= ahora;
        })
        .sort(function (a, b) {
          return a[1].cuando - b[1].cuando;
        });
      vencidas.forEach(function (par) {
        tareas.delete(par[0]);
        par[1].fn();
      });
    },
    pendientes: function () {
      return tareas.size;
    },
  };
}

// =====================================================================
grupo("1. Filtro de host del websocket del webcast");

const WS_WEBCAST =
  "wss://webcast-ws.tiktok.com/webcast/im/ws_proxy/ws_reuse_supplement/" +
  "?room_id=7412345678901234567&compress=gzip&identity=audience&ws_direct=1&X-Bogus=DFSzabc";
const WS_MENSAJERIA = "wss://im-ws-sg.tiktok.com/ws/v2?aid=1988&device_id=123";

prueba("acepta el websocket real del webcast", function () {
  assert.strictEqual(L.esWebSocketDelWebcast(WS_WEBCAST), true);
});

prueba("acepta la ruta vieja /webcast/im/ws/", function () {
  assert.strictEqual(
    L.esWebSocketDelWebcast("wss://webcast-ws.tiktok.com/webcast/im/ws/?room_id=1"),
    true
  );
});

prueba("acepta hosts regionales tipo webcast16-ws-useast1a", function () {
  assert.strictEqual(
    L.esWebSocketDelWebcast("wss://webcast16-ws-useast1a.tiktok.com/webcast/im/ws/"),
    true
  );
});

prueba("DESCARTA im-ws-sg (mensajería privada), que es el que se cuela", function () {
  assert.strictEqual(L.esWebSocketDelWebcast(WS_MENSAJERIA), false);
});

prueba("un filtro laxo por 'im' o 'ws' dejaría pasar im-ws-sg: el nuestro no", function () {
  // Demostración, no adorno: se reconstruye el filtro ingenuo para dejar por
  // escrito que sí se traga la mensajería privada, y que el nuestro no.
  const ingenuo = function (u) {
    return /tiktok\.com/i.test(u) && /(im|ws)/i.test(u);
  };
  assert.strictEqual(ingenuo(WS_MENSAJERIA), true, "el ingenuo sí lo deja pasar");
  assert.strictEqual(L.esWebSocketDelWebcast(WS_MENSAJERIA), false);
});

prueba("el filtro del prototipo anterior se cuela con un ?from=webcast; el nuestro no", function () {
  // El filtro viejo miraba la URL entera, así que cualquier parámetro de la
  // query con la palabra "webcast" lo convencía. Mirando el HOST eso ya no
  // puede pasar.
  const viejo = function (u) {
    return /tiktok\.com/i.test(u) && /webcast|\/im\/ws/i.test(u);
  };
  const trampa = "wss://im-ws-sg.tiktok.com/ws/v2?aid=1988&from=webcast";
  assert.strictEqual(viejo(trampa), true, "el filtro viejo se lo traga");
  assert.strictEqual(L.esWebSocketDelWebcast(trampa), false);
});

prueba("descarta im-ws-sg.tiktokv.com (otro dominio de TikTok)", function () {
  assert.strictEqual(L.esWebSocketDelWebcast("wss://im-ws-sg.tiktokv.com/ws/v2"), false);
});

prueba("descarta el truco del sufijo: webcast-ws.evil-tiktok.com", function () {
  assert.strictEqual(
    L.esWebSocketDelWebcast("wss://webcast-ws.evil-tiktok.com/webcast/im/ws/"),
    false
  );
});

prueba("descarta hosts que no empiezan por 'webcast'", function () {
  assert.strictEqual(L.esWebSocketDelWebcast("wss://ws.tiktok.com/webcast/im/ws/"), false);
  assert.strictEqual(L.esWebSocketDelWebcast("wss://mywebcast.tiktok.com/webcast/im/ws/"), false);
});

prueba("descarta esquemas que no son ws/wss", function () {
  assert.strictEqual(
    L.esWebSocketDelWebcast("https://webcast-ws.tiktok.com/webcast/im/ws/"),
    false
  );
});

prueba("no revienta con basura", function () {
  [null, undefined, "", "no una url", 42, {}].forEach(function (v) {
    assert.strictEqual(L.esWebSocketDelWebcast(v), false, "con " + String(v));
  });
});

prueba("esRutaDeWebcast reconoce las dos rutas y descarta /ws/v2", function () {
  assert.strictEqual(L.esRutaDeWebcast(WS_WEBCAST), true);
  assert.strictEqual(L.esRutaDeWebcast("wss://webcast-ws.tiktok.com/webcast/im/ws/"), true);
  assert.strictEqual(L.esRutaDeWebcast(WS_MENSAJERIA), false);
});

// =====================================================================
grupo("2. Identidad del directo");

prueba("saca el room_id de la query", function () {
  assert.strictEqual(L.sacarRoomId(WS_WEBCAST), "7412345678901234567");
  assert.strictEqual(L.sacarRoomId("wss://webcast-ws.tiktok.com/x"), "");
  assert.strictEqual(L.sacarRoomId("basura"), "");
});

prueba("saca el @usuario de la ruta", function () {
  assert.strictEqual(L.sacarUniqueIdDeRuta("/@usuario/live"), "usuario");
  assert.strictEqual(L.sacarUniqueIdDeRuta("/@usuario.con.puntos/live"), "usuario.con.puntos");
  assert.strictEqual(L.sacarUniqueIdDeRuta("/es/@otro/live"), "otro");
  assert.strictEqual(L.sacarUniqueIdDeRuta("/@usuario"), "usuario");
  assert.strictEqual(L.sacarUniqueIdDeRuta("/foryou"), "");
  assert.strictEqual(L.sacarUniqueIdDeRuta(""), "");
});

prueba("reconoce si la ruta es la de un directo", function () {
  assert.strictEqual(L.esRutaDeDirecto("/@usuario/live"), true);
  assert.strictEqual(L.esRutaDeDirecto("/@usuario/video/123"), false);
  assert.strictEqual(L.esRutaDeDirecto("/foryou"), false);
});

// =====================================================================
grupo("3. Conversión a base64");

prueba("ida y vuelta con el buffer vacío", function () {
  const b64 = L.arrayBufferABase64(new Uint8Array(0));
  assert.strictEqual(b64, "");
  assert.strictEqual(L.base64AUint8(b64).length, 0);
});

prueba("ida y vuelta con los 256 valores de byte", function () {
  const original = new Uint8Array(256);
  for (let i = 0; i < 256; i++) original[i] = i;
  const vuelta = L.base64AUint8(L.arrayBufferABase64(original));
  assert.deepStrictEqual(Array.from(vuelta), Array.from(original));
});

prueba("coincide con Buffer.toString('base64') de Node (oráculo independiente)", function () {
  const datos = Buffer.from("una trama WebcastPushFrame de mentira \x00\x01\xff", "binary");
  const mio = L.arrayBufferABase64(new Uint8Array(datos));
  assert.strictEqual(mio, datos.toString("base64"));
});

prueba("acepta ArrayBuffer y Uint8Array por igual", function () {
  const u8 = new Uint8Array([1, 2, 3, 250, 251]);
  assert.strictEqual(L.arrayBufferABase64(u8), L.arrayBufferABase64(u8.buffer));
});

prueba("aguanta el tamaño real máximo visto en campo (6423 bytes)", function () {
  const grande = new Uint8Array(6423);
  for (let i = 0; i < grande.length; i++) grande[i] = (i * 31) % 256;
  const vuelta = L.base64AUint8(L.arrayBufferABase64(grande));
  assert.strictEqual(vuelta.length, 6423);
  assert.deepStrictEqual(Array.from(vuelta), Array.from(grande));
});

prueba("aguanta un buffer mayor que el trozo interno de 32768", function () {
  const enorme = new Uint8Array(100000);
  for (let i = 0; i < enorme.length; i++) enorme[i] = i % 256;
  const vuelta = L.base64AUint8(L.arrayBufferABase64(enorme));
  assert.strictEqual(vuelta.length, enorme.length);
  assert.strictEqual(vuelta[99999], enorme[99999]);
});

// =====================================================================
grupo("4. Agrupado en lotes");

function agrupadorDePrueba(opciones) {
  const reloj = crearReloj();
  const lotes = [];
  const descartes = [];
  const ag = L.crearAgrupador(
    Object.assign(
      {
        programar: reloj.programar,
        cancelar: reloj.cancelar,
        alDescargar: function (lote) {
          lotes.push(lote);
        },
        alDescartar: function (tiradas, total) {
          descartes.push({ tiradas: tiradas, total: total });
        },
      },
      opciones
    )
  );
  return { ag: ag, reloj: reloj, lotes: lotes, descartes: descartes };
}

prueba("descarga al llegar a maxTramas", function () {
  const t = agrupadorDePrueba({ maxTramas: 3, maxMs: 250 });
  t.ag.agregar("a");
  t.ag.agregar("b");
  assert.strictEqual(t.lotes.length, 0, "todavía no");
  t.ag.agregar("c");
  assert.strictEqual(t.lotes.length, 1);
  assert.deepStrictEqual(t.lotes[0], ["a", "b", "c"]);
});

prueba("descarga al vencer maxMs aunque no se llene", function () {
  const t = agrupadorDePrueba({ maxTramas: 20, maxMs: 250 });
  t.ag.agregar("a");
  t.ag.agregar("b");
  t.reloj.avanzar(249);
  assert.strictEqual(t.lotes.length, 0, "aún no vence");
  t.reloj.avanzar(1);
  assert.strictEqual(t.lotes.length, 1);
  assert.deepStrictEqual(t.lotes[0], ["a", "b"]);
});

prueba("tras descargar por cantidad no queda un temporizador suelto", function () {
  const t = agrupadorDePrueba({ maxTramas: 2, maxMs: 250 });
  t.ag.agregar("a");
  t.ag.agregar("b");
  assert.strictEqual(t.lotes.length, 1);
  t.reloj.avanzar(1000);
  assert.strictEqual(t.lotes.length, 1, "no debe salir un lote vacío después");
  assert.strictEqual(t.reloj.pendientes(), 0);
});

prueba("descargar() con el buffer vacío no llama al callback", function () {
  const t = agrupadorDePrueba({ maxTramas: 5, maxMs: 250 });
  assert.strictEqual(t.ag.descargar(), null);
  assert.strictEqual(t.lotes.length, 0);
});

prueba("ignora tramas vacías o que no son texto", function () {
  const t = agrupadorDePrueba({ maxTramas: 5, maxMs: 250 });
  assert.strictEqual(t.ag.agregar(""), false);
  assert.strictEqual(t.ag.agregar(null), false);
  assert.strictEqual(t.ag.agregar(123), false);
  assert.strictEqual(t.ag.estado().enBuffer, 0);
});

prueba("el tope de memoria por cantidad tira lo MÁS VIEJO y avisa", function () {
  const t = agrupadorDePrueba({
    maxTramas: 1000, // que no descargue por cantidad
    maxMs: 999999,
    maxTramasBuffer: 5,
  });
  for (let i = 0; i < 10; i++) t.ag.agregar("t" + i);
  const est = t.ag.estado();
  assert.strictEqual(est.enBuffer, 5);
  assert.strictEqual(est.descartadas, 5);
  assert.ok(t.descartes.length > 0, "tiene que avisar de los descartes");
  const lote = t.ag.descargar();
  assert.deepStrictEqual(lote, ["t5", "t6", "t7", "t8", "t9"], "se quedan las nuevas");
});

prueba("el tope de memoria por bytes también recorta", function () {
  const t = agrupadorDePrueba({
    maxTramas: 1000,
    maxMs: 999999,
    maxTramasBuffer: 10000,
    maxBytesBuffer: 30,
  });
  for (let i = 0; i < 10; i++) t.ag.agregar("0123456789"); // 10 bytes cada una
  assert.ok(t.ag.estado().bytes <= 30, "bytes=" + t.ag.estado().bytes);
  assert.strictEqual(t.ag.estado().enBuffer, 3);
  assert.strictEqual(t.ag.estado().descartadas, 7);
});

prueba("devolver() reinserta por delante y conserva el orden", function () {
  const t = agrupadorDePrueba({ maxTramas: 1000, maxMs: 999999 });
  t.ag.agregar("c");
  t.ag.agregar("d");
  t.ag.devolver(["a", "b"]);
  assert.deepStrictEqual(t.ag.descargar(), ["a", "b", "c", "d"]);
});

prueba("el orden de llegada se conserva de punta a punta", function () {
  const t = agrupadorDePrueba({ maxTramas: 4, maxMs: 250 });
  const entrada = [];
  for (let i = 0; i < 12; i++) {
    entrada.push("trama-" + i);
    t.ag.agregar("trama-" + i);
  }
  const salida = [].concat.apply([], t.lotes);
  assert.deepStrictEqual(salida, entrada);
});

prueba("volumen real de campo: 24 tramas en 10 s salen en lotes y sin perder ninguna", function () {
  // 24 tramas repartidas cada ~416 ms, con maxMs=250: cada trama vence su
  // propio temporizador antes de que llegue la siguiente.
  const t = agrupadorDePrueba({ maxTramas: 20, maxMs: 250 });
  for (let i = 0; i < 24; i++) {
    t.ag.agregar("t" + i);
    t.reloj.avanzar(416);
  }
  const salida = [].concat.apply([], t.lotes);
  assert.strictEqual(salida.length, 24, "no se pierde ninguna");
  assert.strictEqual(t.ag.estado().descartadas, 0);
  assert.ok(t.lotes.length <= 24 && t.lotes.length > 0);
});

prueba("una ráfaga corta se junta en un solo lote", function () {
  const t = agrupadorDePrueba({ maxTramas: 20, maxMs: 250 });
  for (let i = 0; i < 8; i++) {
    t.ag.agregar("r" + i);
    t.reloj.avanzar(10);
  }
  t.reloj.avanzar(250);
  assert.strictEqual(t.lotes.length, 1, "una sola descarga para las 8");
  assert.strictEqual(t.lotes[0].length, 8);
});

// =====================================================================
grupo("5. Contador seq");

prueba("empieza en 0 y sube de uno en uno", function () {
  const s = L.crearContadorSeq();
  assert.strictEqual(s.siguiente(), 0);
  assert.strictEqual(s.siguiente(), 1);
  assert.strictEqual(s.siguiente(), 2);
  assert.strictEqual(s.valor(), 3);
});

prueba("se puede retomar desde un valor guardado (siesta del service worker)", function () {
  const s = L.crearContadorSeq(41);
  assert.strictEqual(s.siguiente(), 41);
  s.fijar(100);
  assert.strictEqual(s.siguiente(), 100);
});

prueba("nunca repite: 500 tiradas dan 500 valores distintos y crecientes", function () {
  const s = L.crearContadorSeq();
  let previo = -1;
  for (let i = 0; i < 500; i++) {
    const v = s.siguiente();
    assert.strictEqual(v, previo + 1);
    previo = v;
  }
});

prueba("la clave de sesión separa dos salas del MISMO socket reutilizado", function () {
  // Es el caso ws_reuse_supplement: el socket es el mismo, el directo no.
  const a = L.claveDeSesion("ws1-abc", "primerdirecto");
  const b = L.claveDeSesion("ws1-abc", "segundodirecto");
  assert.notStrictEqual(a, b, "cada directo tiene que ser su propia sesión");
  assert.strictEqual(a, L.claveDeSesion("ws1-abc", "primerdirecto"));
});

prueba("simulación: al cambiar de sala el seq de la nueva sesión arranca en 0", function () {
  const seqs = {};
  function siguienteSeq(clave) {
    if (!seqs[clave]) seqs[clave] = L.crearContadorSeq();
    return seqs[clave].siguiente();
  }
  const salaA = L.claveDeSesion("ws1", "unoa");
  const salaB = L.claveDeSesion("ws1", "dosb");
  assert.strictEqual(siguienteSeq(salaA), 0);
  assert.strictEqual(siguienteSeq(salaA), 1);
  assert.strictEqual(siguienteSeq(salaB), 0, "sala nueva, cuenta nueva");
  assert.strictEqual(siguienteSeq(salaA), 2, "la vieja sigue donde estaba");
});

// =====================================================================
grupo("6. Lista blanca de cookies (regla de seguridad)");

const COOKIES_DE_MENTIRA = [
  { name: "ttwid", value: "1%7Cabc" },
  { name: "tt-target-idc", value: "useast2a" },
  { name: "sessionid", value: "NO-DEBE-SALIR-NUNCA" },
  { name: "sessionid_ss", value: "NO-DEBE-SALIR-NUNCA" },
  { name: "sid_tt", value: "NO-DEBE-SALIR-NUNCA" },
  { name: "sid_guard", value: "NO-DEBE-SALIR-NUNCA" },
  { name: "uid_tt", value: "NO-DEBE-SALIR-NUNCA" },
  { name: "msToken", value: "irrelevante" },
  { name: "tt_csrf_token", value: "irrelevante" },
];

prueba("deja pasar exactamente ttwid y tt-target-idc", function () {
  const salida = L.filtrarCookies(COOKIES_DE_MENTIRA);
  assert.deepStrictEqual(Object.keys(salida).sort(), ["tt-target-idc", "ttwid"]);
});

prueba("NINGUNA credencial de sesión sale, ni por asomo", function () {
  const salida = L.filtrarCookies(COOKIES_DE_MENTIRA);
  const serializado = JSON.stringify(salida);
  assert.ok(
    serializado.indexOf("NO-DEBE-SALIR-NUNCA") === -1,
    "se coló una credencial: " + serializado
  );
  ["sessionid", "sessionid_ss", "sid_tt", "sid_guard", "uid_tt"].forEach(function (n) {
    assert.strictEqual(salida[n], undefined, n + " no puede estar");
  });
});

prueba("la lista blanca en sí no contiene nada de sesión", function () {
  assert.deepStrictEqual(L.COOKIES_PERMITIDAS.slice().sort(), ["tt-target-idc", "ttwid"]);
  L.COOKIES_PERMITIDAS.forEach(function (n) {
    assert.ok(!/session|sid|token|auth/i.test(n), "cookie sospechosa en la lista: " + n);
  });
});

prueba("no revienta sin cookies", function () {
  assert.deepStrictEqual(L.filtrarCookies([]), {});
  assert.deepStrictEqual(L.filtrarCookies(null), {});
});

// =====================================================================
grupo("7. Manifiesto y archivos");

const manifiesto = JSON.parse(
  fs.readFileSync(path.join(RAIZ, "manifest.json"), "utf8")
);

prueba("manifest.json es JSON válido y es Manifest V3", function () {
  assert.strictEqual(manifiesto.manifest_version, 3);
  assert.ok(manifiesto.name && manifiesto.version && manifiesto.description);
});

prueba("no pide webRequest (la ruta B no lo necesita)", function () {
  assert.ok(
    (manifiesto.permissions || []).indexOf("webRequest") === -1,
    "webRequest sobra: la URL la da inject.js y las tramas no pasan por ahí"
  );
});

prueba("los permisos son los mínimos: cookies y storage", function () {
  assert.deepStrictEqual((manifiesto.permissions || []).slice().sort(), [
    "cookies",
    "storage",
  ]);
});

prueba("sólo habla con tiktok.com y con 127.0.0.1:8790", function () {
  const hosts = manifiesto.host_permissions || [];
  assert.deepStrictEqual(hosts.slice().sort(), [
    "http://127.0.0.1:8790/*",
    "https://*.tiktok.com/*",
  ]);
  hosts.forEach(function (h) {
    assert.ok(
      /tiktok\.com/.test(h) || /127\.0\.0\.1/.test(h),
      "host de tercero en el manifiesto: " + h
    );
  });
});

prueba("logica.js va antes que inject.js y que content.js en los dos mundos", function () {
  const cs = manifiesto.content_scripts || [];
  assert.strictEqual(cs.length, 2);
  const mundos = cs.map(function (e) {
    return e.world;
  });
  assert.ok(mundos.indexOf("MAIN") !== -1 && mundos.indexOf("ISOLATED") !== -1);
  cs.forEach(function (e) {
    assert.strictEqual(e.run_at, "document_start", "hay que estar antes que TikTok");
    assert.strictEqual(e.js[0], "logica.js", "logica.js tiene que cargarse primero");
  });
});

prueba("todos los archivos que nombra el manifiesto existen", function () {
  const esperados = ["background.js", "popup.html", "popup.js", "logica.js", "inject.js", "content.js"];
  esperados.forEach(function (f) {
    assert.ok(fs.existsSync(path.join(RAIZ, f)), "falta " + f);
  });
  assert.strictEqual(manifiesto.background.service_worker, "background.js");
  assert.strictEqual(manifiesto.action.default_popup, "popup.html");
});

prueba("ningún archivo de la extensión menciona sessionid como cookie a enviar", function () {
  ["background.js", "content.js", "inject.js", "popup.js"].forEach(function (f) {
    const texto = fs.readFileSync(path.join(RAIZ, f), "utf8");
    const lineas = texto.split("\n").filter(function (l) {
      return /sessionid/.test(l) && !/^\s*\/\//.test(l.trim());
    });
    assert.strictEqual(
      lineas.length,
      0,
      f + " menciona sessionid fuera de un comentario: " + lineas.join(" | ")
    );
  });
});

prueba("ninguna URL de tercero: sólo 127.0.0.1", function () {
  ["background.js", "content.js", "inject.js", "popup.js"].forEach(function (f) {
    const texto = fs.readFileSync(path.join(RAIZ, f), "utf8");
    const urls = texto.match(/https?:\/\/[^\s"'`)]+/g) || [];
    urls.forEach(function (u) {
      assert.ok(
        u.indexOf("127.0.0.1") !== -1,
        f + " apunta a un tercero: " + u
      );
    });
  });
});

// =====================================================================
grupo("8. Accesibilidad del popup (lo que NVDA necesita)");

const HTML = fs.readFileSync(path.join(RAIZ, "popup.html"), "utf8");
const JS_POPUP = fs.readFileSync(path.join(RAIZ, "popup.js"), "utf8");

prueba("la página declara el idioma (NVDA elige la voz por esto)", function () {
  assert.ok(/<html[^>]+lang="es"/.test(HTML), 'falta lang="es" en <html>');
});

prueba("tiene título y un único encabezado de nivel 1", function () {
  assert.ok(/<title>[^<]+<\/title>/.test(HTML), "falta <title>");
  const h1 = HTML.match(/<h1[\s>]/g) || [];
  assert.strictEqual(h1.length, 1, "tiene que haber exactamente un h1");
  assert.ok((HTML.match(/<h2[\s>]/g) || []).length >= 3, "faltan encabezados de sección");
});

prueba("todos los botones son <button> de verdad y tienen texto", function () {
  const botones = HTML.match(/<button[^>]*>[\s\S]*?<\/button>/g) || [];
  assert.ok(botones.length >= 3, "esperaba al menos 3 botones");
  botones.forEach(function (b) {
    const texto = b.replace(/<[^>]*>/g, "").trim();
    assert.ok(texto.length > 0, "botón sin nombre accesible: " + b);
    assert.ok(/type="button"/.test(b), "botón sin type explícito: " + texto);
  });
  // Nada de divs clicables haciendo de botón.
  assert.ok(!/<div[^>]*onclick/i.test(HTML), "hay un div haciendo de botón");
});

prueba("el cuadro de diagnóstico tiene una <label> de verdad asociada", function () {
  const idsControles = (HTML.match(/<(?:textarea|input|select)[^>]*id="([^"]+)"/g) || []).map(
    function (t) {
      return t.match(/id="([^"]+)"/)[1];
    }
  );
  assert.ok(idsControles.length > 0, "no hay controles de formulario que comprobar");
  idsControles.forEach(function (id) {
    const etiqueta = new RegExp('<label[^>]*for="' + id + '"[^>]*>([\\s\\S]*?)</label>');
    const m = HTML.match(etiqueta);
    assert.ok(m, "el control " + id + " no tiene <label for>");
    assert.ok(
      m[1].replace(/<[^>]*>/g, "").trim().length > 0,
      "la label de " + id + " está vacía"
    );
  });
});

prueba("hay una región viva educada para anunciar el estado", function () {
  assert.ok(/role="status"/.test(HTML), 'falta el role="status" del resumen');
  // Y NO puede refrescarse sola con un temporizador: hablaría sin parar.
  assert.ok(
    !/setInterval/.test(JS_POPUP),
    "el popup no debe refrescarse en bucle: marearía al lector de pantalla"
  );
});

prueba("todos los id que usa popup.js existen en popup.html", function () {
  const usados = new Set();
  const re = /\$\("([^"]+)"\)/g;
  let m;
  while ((m = re.exec(JS_POPUP)) !== null) usados.add(m[1]);
  assert.ok(usados.size >= 5, "esperaba más ids en uso, ¿cambió la forma de $()?");
  usados.forEach(function (id) {
    assert.ok(
      new RegExp('id="' + id + '"').test(HTML),
      "popup.js usa el id '" + id + "' y popup.html no lo tiene"
    );
  });
});

prueba("no hay scripts en línea (los prohíbe la CSP de Manifest V3)", function () {
  const enLinea = (HTML.match(/<script(?![^>]*\ssrc=)[^>]*>[\s\S]*?<\/script>/g) || []).filter(
    function (s) {
      return s.replace(/<[^>]*>/g, "").trim().length > 0;
    }
  );
  assert.strictEqual(enLinea.length, 0, "hay script en línea: " + enLinea.join(""));
  assert.ok(
    HTML.indexOf('src="logica.js"') < HTML.indexOf('src="popup.js"'),
    "logica.js tiene que cargarse antes que popup.js"
  );
});

prueba("el estado se comunica con palabras, no sólo con color", function () {
  // Si el resumen o el detalle dependieran de una clase de color, aquí
  // aparecerían cosas como classList.add('rojo'). No hay nada de eso.
  assert.ok(
    !/classList\.(add|remove|toggle)\((['"])(rojo|verde|ok|error|malo|bueno)/.test(JS_POPUP),
    "el estado no puede depender de un color"
  );
  ["escuchando", "enganchado", "Tramas enviadas"].forEach(function (palabra) {
    assert.ok(JS_POPUP.indexOf(palabra) !== -1, "falta el estado escrito: " + palabra);
  });
});

// =====================================================================
console.log("\n=======================================");
console.log("Pruebas pasadas: " + pasadas);
console.log("Pruebas falladas: " + fallos.length);
if (fallos.length > 0) {
  console.log("\nFallos:");
  fallos.forEach(function (f) {
    console.log("  - " + f.nombre);
    console.log("    " + (f.error && f.error.stack ? f.error.stack : f.error));
  });
  process.exit(1);
}
console.log("Todo en verde.");
