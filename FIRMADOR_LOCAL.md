# Firmador local: leer el chat de TikTok desde el navegador

Esta es la documentación del **firmador local**, una forma de leer el chat de los
directos de TikTok en VeTube **sin depender de ningún servidor de firmas externo**.

Está pensada para leerse de arriba abajo: primero qué problema resuelve, después
cómo instalarlo y usarlo, y al final cómo funciona por dentro y qué hacer si algo
no anda.

---

## El problema

Para leer el chat de un directo, TikTok exige que la petición al *websocket* del
chat vaya **firmada**. La librería que usa VeTube (`TikTokLive`) no calcula esa
firma: se la pide a un servicio externo, **EulerStream**. Ese servicio:

- se cae seguido (cuando se cae, VeTube no puede leer **ningún** directo de TikTok),
- comparte un cupo limitado entre todos sus usuarios,
- es un tercero al que, en algunos modos, habría que entregarle datos de sesión.

No hay una API oficial de chat en vivo de TikTok, así que no se puede evitar la
firma… **salvo** que la haga el propio navegador.

---

## La idea

Cuando abrís un directo de TikTok en tu navegador, el navegador **ya** hace la
petición firmada y **ya** recibe el chat: los mensajes le llegan por un websocket.
El firmador local no reinventa la firma ni manda tu sesión a nadie: simplemente
**copia los mensajes que tu navegador ya está recibiendo** y se los pasa a VeTube.

En una frase: *VeTube lee por encima del hombro de tu navegador, que es quien
realmente está conectado a TikTok.*

---

## Cómo funciona (las dos mitades)

El firmador local tiene dos partes que hablan entre sí por un puerto local
(`127.0.0.1:8790`), sin salir nunca de tu computadora:

1. **La extensión del navegador** (carpeta `interceptor_extension/`).
   Usa la **API de depuración de Chrome** (la misma que usan las herramientas de
   desarrollador) para leer las tramas del websocket del chat, y las reenvía a
   VeTube. No inyecta nada en la página de TikTok.

2. **La parte de VeTube** (`servicios/tiktok_interceptor.py` y
   `servicios/tiktok_espejo.py`).
   Un pequeño servidor local recibe esas tramas, y un "espejo" reemplaza el
   cliente de websocket de `TikTokLive` por uno que lee de ese servidor en vez de
   conectarse a TikTok. Para el resto de VeTube, el chat llega igual que siempre.

El recorrido de un mensaje, de punta a punta:

    TikTok  →  tu navegador (recibe el chat firmado)  →  la extensión copia la trama
            →  127.0.0.1:8790  →  VeTube la decodifica  →  se lee en voz alta

---

## Instalar la extensión

La extensión **no está en la Chrome Web Store**: viene con VeTube, en la carpeta

    interceptor_extension/

(al lado de este archivo). Para instalarla, una sola vez:

1. Abrí Chrome y andá a `chrome://extensions`.
2. Activá el **"Modo de desarrollador"** (interruptor arriba a la derecha).
3. Pulsá **"Cargar descomprimida"** y elegí la carpeta `interceptor_extension`.
4. Listo: aparece **"VeTube – puente del chat de TikTok Live"** en la lista.

Sirve para Chrome y para navegadores basados en Chromium (Edge, Brave, etc.).

---

## Usarlo en VeTube

En la pantalla de inicio, en el desplegable **"Capturar el chat de:"**, hay dos
opciones para TikTok:

- **"TikTok"** — usa el servicio de firmas de siempre (EulerStream).
- **"TikTok (navegador, experimental)"** — usa el firmador local (este).

Para leer un directo con el firmador local:

1. Abrí el directo en tu navegador (con la extensión ya instalada). Verás que
   Chrome muestra una barra que dice *"… está depurando este navegador"*: **es
   normal y es la señal de que la extensión está leyendo el chat.** Se puede
   ignorar; no la cierres.
2. En VeTube, escribí el **mismo usuario** del directo (el `@usuario`, tal cual,
   con guion bajo y todo si lo tiene).
3. Elegí **"TikTok (navegador, experimental)"** en "Capturar el chat de:".
4. Pulsá **Acceder**.

El chat empieza a leerse. El usuario en VeTube y el del directo abierto en el
navegador **tienen que ser el mismo**.

---

## Qué pasa si EulerStream falla (fallback)

Si elegís **"TikTok"** normal (o "detectar") y la conexión por EulerStream falla,
VeTube te ofrece pasar al navegador con un aviso:

> No se pudo conectar al chat de TikTok por el servicio habitual (suele estar
> caído). Se puede leer desde el navegador. Asegurate de tener la extensión de
> VeTube instalada y este directo abierto en el navegador, y pulsá Aceptar cuando
> esté listo.

Si aceptás (con el directo abierto en el navegador), VeTube reintenta leyendo del
navegador, sin reiniciar nada. Si cancelás, da el error de siempre. El aviso se
ofrece una sola vez por conexión.

---

## Requisitos y límites

- **Requiere un navegador Chrome/Chromium** con la extensión cargada.
- **La extensión tiene que estar cargada antes de abrir el directo.** Si el
  directo ya estaba abierto, recargá esa pestaña para que la extensión lo tome.
- **No tengas las herramientas de desarrollador (F12) abiertas en la pestaña del
  directo**: usan el mismo canal de depuración y chocan con la extensión.
- Es **experimental**: sirve como alternativa cuando EulerStream se cae, no como
  reemplazo definitivo.

---

## Seguridad y privacidad

- **La extensión solo lee lo que tu navegador ya recibe.** No burla ninguna
  protección: la firma la hace TikTok en tu propia sesión, como siempre.
- **No sale tu cookie de sesión.** La extensión nunca envía `sessionid` ni ninguna
  credencial de tu cuenta.
- **Todo queda en tu computadora.** La extensión solo habla con `127.0.0.1:8790`
  (VeTube); nada se manda a ningún tercero.
- **No modifica la página de TikTok** ni su seguridad: solo observa el tráfico del
  chat, del mismo modo que lo verían las herramientas de desarrollador.

---

## Si algo no anda (diagnóstico)

La extensión tiene un **popup accesible** (pulsá su ícono en la barra de Chrome).
Pensado para lectores de pantalla, dice en palabras:

- si VeTube está escuchando en el puerto 8790,
- cuántas pestañas de TikTok tiene enganchadas,
- cuántas tramas del chat leyó,
- y un cuadro de "Diagnóstico" que se puede copiar entero (sin datos privados).

Casos típicos:

- **"VeTube escuchando: no"** → VeTube no está abierto, o no iniciaste el chat con
  "TikTok (navegador)".
- **No hay ninguna pestaña enganchada** → abrí el directo, o recargá su pestaña si
  ya estaba abierta antes de instalar/recargar la extensión.
- **VeTube dice que el usuario no existe / no está en vivo** → revisá que el
  `@usuario` en VeTube sea idéntico al del directo abierto en el navegador.

---

## Para desarrolladores

**Archivos de la extensión** (`interceptor_extension/`):

- `manifest.json` — declara la extensión (Manifest V3) y sus permisos: `debugger`,
  `storage` y acceso a `*.tiktok.com` y al puerto local.
- `background.js` — el service worker. Adjunta el depurador a las pestañas de
  TikTok, escucha `Network.webSocketFrameReceived`, filtra el websocket del
  webcast por host, agrupa las tramas en lotes y las postea a VeTube.
- `logica.js` — lógica pura (filtro de host, base64, agrupado, contador de
  secuencia), sin tocar el navegador, para poder testearla con Node.
- `popup.html` / `popup.js` — el popup de estado accesible.
- `pruebas/pruebas.js` — banco de pruebas de la lógica pura, ejecutable con Node
  sin navegador.

**Archivos de VeTube:**

- `servicios/tiktok_interceptor.py` — servidor local. Contrato (todo por
  `http://127.0.0.1:8790`, JSON):
  - `GET  /salud`   → `{"ok": true, "version": 2}`
  - `POST /sesion`  → aviso de apertura/cierre de un directo.
  - `POST /tramas`  → `{"unique_id", "room_id", "seq", "tramas": ["<base64>", …]}`.
    `seq` es un contador por sesión para detectar lotes perdidos.
- `servicios/tiktok_espejo.py` — el "espejo": reemplaza `client._ws` y el paso de
  firma de `TikTokLiveClient` por uno que lee de la cola que llena el servidor
  local. No firma ni abre conexiones a TikTok.
- `servicios/tiktok.py` — instala el espejo según la opción elegida y ofrece el
  fallback al navegador si EulerStream falla.

**Tests** (`tests/test_tiktok_interceptor.py`, `tests/test_tiktok_espejo.py`):
ejercitan el parseo de tramas con protobuf sintético, sin tocar la red real de
TikTok. Se corren con `pytest tests/`.

**Por qué la API de depuración y no un content script:** para leer las tramas hay
que estar en el contexto de la página. Pero la CSP de TikTok (su `script-src` no
incluye `'self'` ni `'unsafe-inline'`) **bloquea los content scripts del mundo
MAIN** — la documentación de Chrome lo dice explícito. La API de depuración lee las
tramas sin inyectar nada en la página, así que es inmune a la CSP.
