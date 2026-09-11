# VeTube – puente del chat de TikTok Live (extensión)

Esta es la **mitad que vive en el navegador** del firmador local de VeTube. Lee
las tramas del chat que tu navegador ya recibe del directo y se las pasa a VeTube
por `127.0.0.1:8790`. No recalcula ninguna firma ni manda tu cookie de sesión.

> La explicación completa del firmador (las dos mitades, cómo se usa en VeTube,
> seguridad, diagnóstico) está en `../FIRMADOR_LOCAL.md`. Este archivo cubre solo
> la extensión: cómo instalarla y cómo está hecha.

## Cómo instalarla

1. Abrí `chrome://extensions`.
2. Activá el **"Modo de desarrollador"** (arriba a la derecha).
3. Pulsá **"Cargar descomprimida"** y elegí **esta carpeta** (`interceptor_extension`).
4. Aparece **"VeTube – puente del chat de TikTok Live"**.

Sirve en Chrome y en navegadores basados en Chromium (Edge, Brave, etc.).

## Cómo probarla

1. Abrí VeTube (o el receptor de prueba `../recibir_captura.py`, que levanta el
   mismo servidor local e imprime, sin secretos, qué va llegando).
2. Abrí un directo de TikTok: `https://www.tiktok.com/@usuario/live`.
3. Chrome mostrará la barra *"… está depurando este navegador"*: **es normal**, es
   la señal de que la extensión está leyendo el chat.
4. Mirá el popup de la extensión (su ícono en la barra): dice si VeTube escucha,
   cuántas pestañas tiene enganchadas y cuántas tramas leyó.

Si el directo ya estaba abierto antes de instalar/recargar la extensión, **recargá
esa pestaña**: la extensión tiene que engancharse antes de que se abra el websocket.
Y **no tengas las herramientas de desarrollador (F12) abiertas** en esa pestaña:
usan el mismo canal de depuración y chocan.

## Qué hace cada archivo

- `manifest.json` — declara la extensión (Manifest V3) y sus permisos: `debugger`,
  `storage`, y acceso a `*.tiktok.com` y a `127.0.0.1:8790`.
- `background.js` — el service worker, y el corazón de la captura. Adjunta el
  depurador (`chrome.debugger`) a las pestañas de TikTok, activa el dominio
  `Network` y escucha `Network.webSocketFrameReceived`. Filtra el websocket del
  webcast por host (`webcast-ws.tiktok.com`), agrupa las tramas binarias en lotes
  y las postea a VeTube. Las tramas binarias ya vienen en base64, que es justo lo
  que VeTube espera.
- `logica.js` — lógica pura (filtro de host, base64, agrupado en lotes, contador
  de secuencia). No toca el navegador, para poder probarla con Node.
- `popup.html` / `popup.js` — popup de estado, pensado para lectores de pantalla:
  todo el estado escrito con palabras, sin depender de color ni de iconos.
- `pruebas/pruebas.js` — banco de pruebas de `logica.js`, ejecutable sin navegador
  (`node pruebas/pruebas.js`).

## Por qué la API de depuración

Para leer las tramas del websocket hay que estar en el contexto de la página. Pero
la CSP de TikTok (su `script-src` no incluye `'self'` ni `'unsafe-inline'`)
**bloquea los content scripts del mundo MAIN** — la documentación de Chrome lo dice
explícito: *"cuando un content script se inyecta en el mundo MAIN, se aplica la CSP
de la página"*. Por eso la captura no se hace inyectando código en la página, sino
con la API de depuración, que lee las tramas igual que las herramientas de
desarrollador y es inmune a la CSP.

## Notas de seguridad

- `sessionid` (la llave completa de tu cuenta) **nunca** se envía. La lista de
  cookies permitidas se limita a lo inocuo, y de hecho el chat de un directo
  público funciona sin login.
- La extensión solo habla con `127.0.0.1:8790`. Ningún tercero.
- No modifica ni bloquea el tráfico de la página: solo lo observa.
