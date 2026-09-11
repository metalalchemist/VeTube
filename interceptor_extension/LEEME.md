# Puente del chat de TikTok Live para VeTube

La mitad que vive en el navegador. **Copia las tramas del chat que tu navegador
ya está recibiendo del directo** y se las pasa a VeTube por `127.0.0.1:8790`.

No recalcula ninguna firma, no burla nada y no manda tu sesión a ningún sitio:
la petición firmada la hace tu propio navegador cuando abrís el directo, como
la haría igual sin la extensión. Esto sólo mira y copia.

---

## Por qué existe

El websocket del chat de TikTok exige que la petición vaya firmada.
`TikTokLive` delegaba esa firma en EulerStream, que está caído desde el
2026-09-09, y no hay firmador alternativo aceptable. Pero tu navegador, al
abrir el directo, **ya hace la petición firmada él solo**. La extensión se
engancha a ese websocket ya abierto y reenvía lo que llega.

---

## Ruta A y ruta B

Hay dos formas de aprovechar lo que hace el navegador, y esta extensión hace
las dos, pero sólo una es el camino de verdad.

**Ruta A — pasarle a VeTube la URL ya firmada** (`POST /captura`). Es frágil:
en `ws_connect.py` de TikTokLive está documentado que las URLs firmadas
**caducan a los 30 segundos**, y encima el navegador ya gastó ésa. Se sigue
enviando porque el contrato la incluye y porque de paso le lleva a VeTube las
cookies y el `room_id`, pero no se puede depender de ella.

**Ruta B — copiar las tramas** (`POST /tramas`). **Éste es el camino
principal.** El navegador mantiene su websocket abierto y la extensión añade su
propio oyente a los mensajes que llegan, los pasa a base64 y los reenvía en
lotes. Nunca se reutiliza una firma porque nunca se vuelve a firmar nada: se
aprovecha la conexión que ya está viva.

Las tramas se reenvían **intactas**. Son `WebcastPushFrame` de protobuf y la
extensión no las mira por dentro: eso es cosa del lado Python.

---

## Qué hace cada archivo

| Archivo | Dónde corre | Para qué |
|---|---|---|
| `manifest.json` | — | Declara la extensión (Manifest V3) y sus permisos. |
| `logica.js` | en los tres sitios | Lógica pura: filtro de host, base64, agrupado en lotes, contador `seq`, lista blanca de cookies. Sin DOM, sin `chrome.*`, sin red: por eso se puede probar con Node. |
| `inject.js` | mundo de la página | Envuelve `window.WebSocket` para **escuchar** las tramas del webcast. |
| `content.js` | mundo aislado | Agrupa en lotes, sigue el `@usuario` de la ruta y mantiene despierto al service worker. |
| `background.js` | service worker | La única pieza que habla con VeTube. Reúne las cookies y postea. |
| `popup.html` / `popup.js` | popup | Estado, pensado para leerse con NVDA. |
| `pruebas/pruebas.js` | Node | Banco de pruebas, sin navegador. |

---

## Instalación

1. Abrí `chrome://extensions`.
2. Activá **Modo de desarrollador** (arriba a la derecha).
3. **Cargar descomprimida** y elegí esta carpeta.
4. Si ya tenías un directo abierto, **recargá esa pestaña** (ver más abajo por qué).

No hay que compilar nada: es JavaScript plano, sin dependencias ni build.

---

## Cómo probarla

### Sin navegador (rápido, cada vez que se toque el código)

```
cd "C:\Users\phaza\cosas github\VeTube\interceptor_extension"
node pruebas/pruebas.js
```

Ejercita el filtro de host (incluido que el websocket de la mensajería privada
se descarte), la conversión a base64 de ida y vuelta, el agrupado en lotes con
su tope de memoria, el contador `seq`, la lista blanca de cookies, el manifiesto
y la accesibilidad del popup. Termina con un recuento y sale con código 1 si
algo falla.

### Con un directo de verdad

1. Poné en marcha VeTube (o el receptor de prueba `recibir_captura.py`), que
   escucha en `http://127.0.0.1:8790`.
2. Abrí un directo: `https://www.tiktok.com/@quien_sea/live`.
3. Abrí el popup de la extensión (icono en la barra) y comprobá que dice
   *"Todo en marcha"* y que el contador de tramas sube.
4. Si algo no encaja, el popup trae un cuadro de **diagnóstico** que se puede
   copiar entero y pegar en un informe: lleva el host, la ruta y los **nombres**
   de los parámetros, nunca los valores ni la URL firmada.

---

## Contrato con VeTube

Todo contra `http://127.0.0.1:8790`.

```
GET  /salud    -> 200 {"ok": true, "version": 2}
POST /captura  -> ruta A. {"unique_id","room_id","ws_url","cookies":{...},"cursor"}
POST /sesion   -> aviso de estado. {"unique_id","room_id","estado":"abierto"|"cerrado","ws_url"}
POST /tramas   -> ruta B. {"unique_id","room_id","seq":<entero>,"tramas":["<base64>", ...]}
                  respuesta: {"ok": true, "recibidas": <n>}
```

### Qué significa exactamente `seq`

El contrato pide *"entero monotónico por sesión"*. Aquí **`seq` numera lotes, no
tramas**: el primer `POST /tramas` de una sesión lleva `seq: 0`, el siguiente
`seq: 1`, y así. Con `tramas` siendo una lista, un `seq` por trama sería ambiguo
(¿el de la primera?, ¿el de la última?); numerando el lote, el lado Python tiene
una comprobación trivial: **si el `seq` que llega no es el anterior + 1, se
perdió un lote.**

Y una **sesión** es *(socket interceptado + `@usuario` que se está viendo)*.
Importa por lo que se explica abajo sobre la conexión reutilizada: al cambiar de
directo, el socket es el mismo pero la sesión es otra, así que se manda un
`/sesion cerrado`, un `/sesion abierto` y el `seq` vuelve a empezar en 0.

`unique_id` es el dato **autoritativo**; `room_id` es el mejor esfuerzo y puede
venir viejo (otra vez, la conexión reutilizada).

---

## Lo aprendido

### 1. Una página de tiktok.com no puede llamar a 127.0.0.1

Comprobado en campo: un servidor local responde `200` a `curl`, y la petición
del navegador **ni siquiera se registra en el servidor**. Chrome la corta antes
de emitirla.

Es **Local Network Access (LNA)**: desde Chrome 142 un origen público no alcanza
loopback (`127.0.0.1`, `localhost`, `.local`) sin permiso. Por eso el `POST`
**tiene** que salir del service worker.

**Sobre si hace falta declarar algo en el manifiesto: no.** No existe un permiso
`localNetworkAccess` para extensiones. El criterio de Chrome es que *"mientras
una extensión tenga los host permissions correctos, esto no le afecta"*, y
nuestro `host_permissions` ya incluye `http://127.0.0.1:8790/*`. Con eso basta.

El único matiz, y conviene tenerlo escrito: **hubo un bug** por el que a
extensiones con host permissions correctos les fallaban igualmente las
peticiones a la red local (`crbug.com/435246545`, y otro relacionado, el
`456078996`). Se arregló en Chrome **144**. Esta máquina tiene Chrome **152**,
o sea muy por encima del arreglo. Si alguna vez esto se prueba en un Chrome
entre el 142 y el 143, ése es el primer sospechoso.

### 2. El service worker se duerme, y se resolvió con un latido

El service worker de MV3 se apaga **a los 30 segundos de ocio**. Al despertar,
sus variables globales están en blanco. Dos problemas distintos y dos arreglos:

- **Que no se duerma mientras hay chat.** `content.js` mantiene un puerto de
  larga duración (`chrome.runtime.connect`) y manda un latido cada **20 s**.
  Desde Chrome 114, mandar mensajes por un puerto abierto reinicia el
  temporizador de ocio. El latido sólo corre **mientras hay un directo
  enganchado**: en una pestaña cualquiera de TikTok no se mantiene despierto a
  nadie. En la práctica el propio tráfico ya lo mantiene vivo (un lote cada
  250 ms), pero el latido cubre los ratos en que el chat se queda callado.
- **Que si aun así se muere, no se pierda nada.** Todo el estado que no puede
  reiniciarse —sobre todo el contador `seq`— vive en `chrome.storage.session`,
  no en variables globales. Y el `seq` **se guarda antes de postear**: si el
  worker muere en mitad del envío, al volver arranca en el siguiente. Un hueco
  lo detecta el lado Python; un `seq` repetido lo confundiría de verdad.

Detalle que casi muerde: **el worker también muere si un `fetch` tarda más de
30 s en responder**. Por eso los POST llevan `AbortSignal.timeout(5000)`.

No se usa `chrome.alarms`: su periodo mínimo es de 30 s, justo el borde del ocio,
así que llega tarde por diseño.

### 3. La conexión se reutiliza entre salas

El socket es `.../webcast/im/ws_proxy/ws_reuse_supplement/`, y ese
`ws_reuse_supplement` va en serio: al pasar de un directo a otro **no se abre un
socket nuevo**, el cambio de sala viaja como mensaje por el mismo socket. De ahí
salen dos consecuencias:

- **El `room_id` de la query se queda viejo.** Por eso el dato autoritativo es
  el `@usuario` de `location.pathname`, que `content.js` vigila cada segundo
  para enterarse de las navegaciones del SPA.
- **Si la extensión se carga con la página ya abierta, no ve nada.** El socket
  ya existía y no hay forma de engancharse a posteriori. El popup lo detecta
  (está en un directo pero no hay sesión abierta para ese usuario) y muestra el
  aviso con un botón para recargar.

### 4. Hay un segundo websocket que hay que descartar

En la misma pestaña convive `wss://im-ws-sg.tiktok.com/ws/v2`, que es la
mensajería privada y no tiene nada que ver con el chat del directo. El filtro es
**por host**: la primera etiqueta del dominio tiene que empezar por `webcast` y
el dominio tiene que ser `tiktok.com` de verdad (nada de trucos de sufijo tipo
`evil-tiktok.com`).

El filtro del prototipo anterior miraba la URL entera, así que un simple
`?from=webcast` en la query se lo colaba. Hay una prueba que lo deja por
escrito.

### 5. base64 en el mundo de la página, y por qué

`chrome.runtime.sendMessage` y los puertos **serializan como JSON**: un
`ArrayBuffer` o un `Uint8Array` NO sobreviven ese salto (llegan como `{}` o como
un objeto con claves numéricas). Así que hay que pasar a base64 sí o sí; la
única decisión es de qué lado del `postMessage`.

Se hace **en el mundo de la página**, por tres razones:

1. El `Blob` es un objeto de la página y `blob.arrayBuffer()` hay que llamarlo
   ahí de todos modos. Pasar el `Blob` al otro mundo sólo mueve el mismo trabajo
   de sitio.
2. Un content script **corre en el mismo hilo que la página**, así que "pasarlo
   al mundo aislado" no le ahorra ni un milisegundo al hilo principal. No hay
   nada que ganar.
3. Convirtiendo ahí, lo único que cruza el `postMessage` es una **cadena de
   texto**: sin copia estructurada del binario, sin listas de transferencia, sin
   sorpresas entre mundos, y ya en el formato exacto que pide el contrato.

El agrupado en lotes, en cambio, está **en el mundo aislado**, porque el tope de
memoria necesita saber si hay a quién entregarle las tramas: si el worker no
está o VeTube no responde, quien tiene que aguantar y decidir qué se tira es el
content script.

### 6. `webRequest` sobraba: se quitó

El prototipo pedía el permiso `webRequest` para ver el handshake del websocket.
Con la ruta B no sirve de nada: `webRequest` **sólo ve el handshake, nunca las
tramas** que viajan después, y la URL ya la da `inject.js`. Fuera. Los permisos
que quedan son `cookies` (para la lista blanca) y `storage` (para el estado que
sobrevive a las siestas del worker).

### 7. `binaryType` es `"blob"`, y no se toca

Las tramas llegan como `Blob`. Se podría poner `ws.binaryType = "arraybuffer"`
y ahorrarse una conversión, pero eso **cambiaría lo que recibe el manejador de
la propia página** y le rompería el chat a TikTok. Es interferir, así que no.
Por lo mismo, el oyente se añade con `addEventListener` y nunca asignando
`ws.onmessage`, que pisaría el de la página.

---

## Seguridad

- **Nunca se manda `sessionid`** ni ninguna otra credencial de sesión. La lista
  blanca es exactamente `ttwid` y `tt-target-idc`, y hay una prueba que falla si
  alguien la amplía con algo que huela a sesión. Está comprobado en campo que
  con `user_is_login=false` el directo y su chat funcionan igual, así que no hay
  ninguna excusa para ampliarla.
- La extensión **sólo habla con `127.0.0.1:8790`**. Ningún tercero. Hay una
  prueba que revisa cada archivo buscando URLs y falla si aparece otra cosa.
- **No se modifica ni se bloquea el tráfico de la página.** Sólo se observa.
- Permisos mínimos: `cookies`, `storage`, y host permissions para
  `https://*.tiktok.com/*` y el puerto local. Nada más.
- El diagnóstico del popup **no incluye la `ws_url` completa**, porque lleva la
  firma `X-Bogus`: sólo el host, la ruta y los nombres de los parámetros.

---

## Si algo no va

**El popup dice "Hace falta recargar la página del directo".**
La extensión se cargó o se actualizó con el directo ya abierto. El websocket ya
existía y no se puede enganchar a posteriori. Recargá (el botón lo hace).

**El popup dice "VeTube no responde en el puerto 8790".**
VeTube no está abierto, o no llegó a levantar su servidor local. El detalle del
error está en la lista.

**El contador de tramas no sube pero sí hay chat en pantalla.**
Mirá la consola del service worker (`chrome://extensions` → *Service Worker*).
Si aparecen "lote perdido", VeTube está rechazando los POST.

**Salen muchas "Tramas descartadas".**
El buffer se llenó porque VeTube no las recibía. Se tiran las **más viejas** a
propósito: en un chat en vivo lo que importa es lo que se dice ahora.
