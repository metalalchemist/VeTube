// Regenera las imágenes de la extensión y de su ficha en la Chrome Web Store
// con el Chrome instalado, en modo headless y con un perfil temporal (no toca
// el perfil de quien lo corre):
//
//     node interceptor_extension/tienda/generar_imagenes.js
//
// Salidas:
//   iconos/icono16.png ... icono128.png   desde tienda/icono.svg
//   tienda/imagenes/mosaico-440x280.png   mosaico promocional pequeño (obligatorio)
//   tienda/imagenes/captura-1280x800.png  captura de pantalla (hace falta al menos una)
//
// La captura muestra el popup REAL (popup.html + logica.js + popup.js) con un
// estado de ejemplo inyectado en lugar de las API de Chrome, así que si cambia
// el popup basta con volver a correr esto. Si Chrome no está en la ruta de
// siempre, se le puede indicar con la variable de entorno CHROME.
"use strict";

const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

const TIENDA = __dirname;
const RAIZ = path.join(TIENDA, "..");
const IMAGENES = path.join(TIENDA, "imagenes");

function buscarChrome() {
  const candidatos = [
    process.env.CHROME,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    process.env.LOCALAPPDATA &&
      path.join(process.env.LOCALAPPDATA, "Google/Chrome/Application/chrome.exe"),
  ];
  const hallado = candidatos.find(function (c) {
    return c && fs.existsSync(c);
  });
  if (!hallado) throw new Error("No encuentro Chrome. Indicá su ruta en la variable CHROME.");
  return hallado;
}

const CHROME = buscarChrome();
const TEMPORAL = fs.mkdtempSync(path.join(os.tmpdir(), "vetube-imagenes-"));
let paginas = 0;

function url(ruta) {
  return pathToFileURL(ruta).href;
}

// Captura un HTML a PNG. Fondo transparente: lo que la página no pinta queda
// transparente (hace falta para los iconos). --virtual-time-budget deja correr
// los temporizadores del popup antes de la foto. preferredColorScheme=1 fuerza
// el tema claro: si no, el popup sale oscuro cuando Windows usa tema oscuro.
function capturar(html, salida, ancho, alto) {
  const pagina = path.join(TEMPORAL, "pagina" + ++paginas + ".html");
  fs.writeFileSync(pagina, html);
  execFileSync(
    CHROME,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--force-device-scale-factor=1",
      "--default-background-color=00000000",
      "--virtual-time-budget=3000",
      "--blink-settings=preferredColorScheme=1",
      "--user-data-dir=" + path.join(TEMPORAL, "perfil"),
      "--window-size=" + ancho + "," + alto,
      "--screenshot=" + salida,
      url(pagina),
    ],
    { stdio: "pipe", timeout: 60000 }
  );
  const png = fs.readFileSync(salida);
  const medidas = [png.readUInt32BE(16), png.readUInt32BE(20)];
  if (medidas[0] !== ancho || medidas[1] !== alto) {
    throw new Error(salida + " salió de " + medidas.join("x") + " y no de " + ancho + "x" + alto);
  }
  console.log("  " + path.relative(RAIZ, salida) + " (" + ancho + "x" + alto + ")");
}

// ---------------------------------------------------------------------
// 1. Iconos
// ---------------------------------------------------------------------
// El de 128 lleva los 16 px de margen transparente que pide la tienda. Los
// chicos van sin margen (se recorta el lienzo al cuadro 16 16 96 96): a 16 px
// cada píxel cuenta.
function iconos() {
  const svg = fs.readFileSync(path.join(TIENDA, "icono.svg"), "utf8");
  [16, 32, 48, 128].forEach(function (lado) {
    const caja = lado === 128 ? "0 0 128 128" : "16 16 96 96";
    const ajustado = svg.replace(
      /viewBox="[^"]*" width="[^"]*" height="[^"]*"/,
      'viewBox="' + caja + '" width="' + lado + '" height="' + lado + '"'
    );
    capturar(
      '<!doctype html><html><body style="margin:0;background:transparent">' +
        ajustado.replace(/<svg /, '<svg style="display:block" ') +
        "</body></html>",
      path.join(RAIZ, "iconos", "icono" + lado + ".png"),
      lado,
      lado
    );
  });
}

// ---------------------------------------------------------------------
// 2. El popup con un estado de ejemplo
// ---------------------------------------------------------------------
// Imita lo que responde background.js cuando todo anda: VeTube escuchando y un
// directo enganchado. El usuario del directo es inventado.
const ESTADO_DE_EJEMPLO = `
(function () {
  var ahora = Date.now();
  var estado = {
    vetube: { ok: true, version: 2, ultimoChequeoMs: ahora, ultimoError: "" },
    versionEsperada: 2,
    sesiones: [{
      unique_id: "canal_de_ejemplo",
      room_id: "7412345678901234567",
      ws_url: "wss://webcast-ws.tiktok.com/webcast/im/ws_proxy/ws_reuse_supplement/?room_id=7412345678901234567&version_code=270000",
      abiertaMs: ahora - 600000,
      tabId: 1
    }],
    paginas: [],
    contadores: { tramasEnviadas: 1284, lotesEnviados: 231, lotesFallidos: 0, tramasDescartadas: 0, ultimaTramaMs: ahora - 2000 },
    diag: { modo: "debugger", adjuntas: 1, wsWebcast: 1, framesWebcast: 1284, ultimoError: "" },
    ahoraMs: ahora
  };
  Object.defineProperty(window, "chrome", {
    configurable: true,
    writable: true,
    value: {
      runtime: { sendMessage: function () { return Promise.resolve(estado); } },
      tabs: {
        query: function () {
          return Promise.resolve([{ id: 1, url: "https://www.tiktok.com/@canal_de_ejemplo/live" }]);
        },
        reload: function () { return Promise.resolve(); }
      }
    }
  });
})();
`;

// El body del popup mide 360 más 14 de relleno a cada lado. En alto se captura
// de más y en la imagen se muestran 600, el máximo real de un popup de Chrome
// (a partir de ahí el popup hace scroll).
const ANCHO_POPUP = 388;
const ALTO_POPUP = 820;
const ALTO_VISIBLE = 600;

function popup(salida) {
  const stub = path.join(TEMPORAL, "estado-de-ejemplo.js");
  fs.writeFileSync(stub, ESTADO_DE_EJEMPLO);
  let html = fs.readFileSync(path.join(RAIZ, "popup.html"), "utf8");
  // <base> para que logica.js y popup.js se carguen desde la extensión, y el
  // estado de ejemplo antes que ellos.
  html = html.replace(/<head>/, '<head><base href="' + url(RAIZ) + '/">');
  if (html.indexOf('<script src="logica.js">') === -1) {
    throw new Error('popup.html ya no carga logica.js como <script src="logica.js">: actualizá este script');
  }
  html = html.replace(
    '<script src="logica.js">',
    '<script src="' + url(stub) + '"></script><script src="logica.js">'
  );
  capturar(html, salida, ANCHO_POPUP, ALTO_POPUP);
}

// ---------------------------------------------------------------------
// 3. Mosaico promocional y captura
// ---------------------------------------------------------------------
// Comillas simples: esto va dentro de un atributo style="...".
const FUENTE = "font-family:'Segoe UI',system-ui,sans-serif;";

function mosaico(icono) {
  capturar(
    `<!doctype html><html lang="es"><body style="margin:0">
<div style="${FUENTE}width:440px;height:280px;box-sizing:border-box;padding:0 36px;background:#0b2a5b;color:#fff;display:flex;align-items:center;gap:22px">
  <img src="${url(icono)}" width="128" height="128" alt="" style="flex:none;margin:-16px">
  <div>
    <div style="font-size:44px;font-weight:700;line-height:1.05">VeTube</div>
    <div style="font-size:21px;line-height:1.3;margin-top:10px">El chat de tus directos de TikTok, en tu lector de pantalla</div>
  </div>
</div></body></html>`,
    path.join(IMAGENES, "mosaico-440x280.png"),
    440,
    280
  );
}

function captura(icono, imagenPopup) {
  const pasos = [
    "Abrí el directo de TikTok en Chrome.",
    "En VeTube, escribí el mismo @usuario.",
    "Elegí «TikTok (navegador, experimental)» y pulsá Acceder.",
  ];
  capturar(
    `<!doctype html><html lang="es"><body style="margin:0">
<div style="${FUENTE}width:1280px;height:800px;box-sizing:border-box;padding:0 72px;background:#eef3fd;color:#0b2a5b;display:flex;align-items:center;gap:64px">
  <div style="flex:1">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:28px">
      <img src="${url(icono)}" width="96" height="96" alt="" style="margin:-12px">
      <span style="font-size:34px;font-weight:700">VeTube</span>
    </div>
    <div style="font-size:46px;font-weight:700;line-height:1.15">Leé el chat de tus directos de TikTok con VeTube</div>
    <ol style="font-size:27px;line-height:1.4;margin:32px 0 0;padding-left:40px">
      ${pasos.map((p) => `<li style="margin-bottom:12px">${p}</li>`).join("")}
    </ol>
    <div style="font-size:23px;line-height:1.4;margin-top:28px;color:#33466b">Todo queda en tu computadora: la extensión solo habla con VeTube, en 127.0.0.1.</div>
  </div>
  <div style="flex:none;width:${ANCHO_POPUP}px;height:${ALTO_VISIBLE}px;overflow:hidden;border-radius:10px;background:#fff;box-shadow:0 12px 36px rgba(11,42,91,.28);border:1px solid #c6d0e0">
    <img src="${url(imagenPopup)}" width="${ANCHO_POPUP}" height="${ALTO_POPUP}" alt="" style="display:block">
  </div>
</div></body></html>`,
    path.join(IMAGENES, "captura-1280x800.png"),
    1280,
    800
  );
}

try {
  fs.mkdirSync(IMAGENES, { recursive: true });
  console.log("Generando imágenes con " + CHROME);
  iconos();
  const imagenPopup = path.join(TEMPORAL, "popup.png");
  popup(imagenPopup);
  const icono = path.join(RAIZ, "iconos", "icono128.png");
  mosaico(icono);
  captura(icono, imagenPopup);
  console.log("Listo.");
} finally {
  // Chrome puede tardar un instante en soltar el perfil: si no se puede
  // borrar ahora, queda en la carpeta temporal del sistema y no molesta.
  try {
    fs.rmSync(TEMPORAL, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 });
  } catch (e) {
    console.log("Aviso: no se pudo borrar " + TEMPORAL);
  }
}
