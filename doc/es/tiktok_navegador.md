# Leer TikTok desde el navegador: extensión del firmador local

Esta guía explica una forma alternativa de leer el chat de un directo de TikTok en VeTube, pensada para cuando la forma habitual falla. Está pensada para leerse de arriba abajo: primero para qué sirve, después por qué existe, cómo instalarla y usarla, y al final las notas de seguridad.

## Para qué sirve

Para leer el chat de un directo, TikTok exige que la petición al *websocket* del chat vaya **firmada**. VeTube normalmente le pide esa firma a un servicio externo (EulerStream). Cuando ese servicio falla —cosa que pasa con frecuencia—, VeTube no puede leer el chat de **ningún** directo de TikTok por la vía habitual.

La extensión resuelve justo eso: en vez de depender de ese servicio externo, deja que **tu propio navegador** —que ya tiene el directo abierto y ya está recibiendo el chat con una conexión firmada y válida— le pase esos mensajes a VeTube. La extensión no calcula ninguna firma nueva: solo copia los mensajes que tu navegador ya está recibiendo.

En una frase: *VeTube lee por encima del hombro de tu navegador, que es quien realmente está conectado a TikTok.*

## Por qué se creó

No existe una API oficial para leer el chat de un directo de TikTok, así que VeTube (y cualquier programa parecido) depende de un servicio externo que calcule la firma que TikTok exige. Ese servicio, EulerStream:

- se cae con frecuencia (y mientras está caído, nadie puede leer ningún directo de TikTok por esa vía),
- reparte un cupo limitado entre todos sus usuarios,
- es un tercero ajeno a VeTube.

Como no se puede evitar la firma, la extensión nació para resolverlo sin depender de ese tercero: si tu navegador ya está viendo el directo con una conexión firmada y funcionando, no hace falta pedirle la firma a nadie más. Es una alternativa, no un reemplazo definitivo: se usa cuando el servicio habitual falla.

## Cómo instalarla

La extensión **no está en la Chrome Web Store**: viene incluida con VeTube, en la carpeta `interceptor_extension`. Para instalarla, una sola vez:

1. Abre Chrome (o un navegador basado en Chromium, como Edge o Brave) y ve a `chrome://extensions`.
2. Activa el **«Modo de desarrollador»** (interruptor arriba a la derecha).
3. Pulsa **«Cargar descomprimida»** y elige la carpeta `interceptor_extension` (viene junto al programa de VeTube).
4. Listo: aparece **«VeTube – puente del chat de TikTok Live»** en la lista de extensiones.

## Cómo usarla

En la pantalla de inicio de VeTube, en el desplegable **«Capturar el chat de:»**, hay dos opciones para TikTok: **«TikTok»** (el servicio habitual) y **«TikTok (navegador, experimental)»** (esta extensión). Para usar la extensión directamente:

1. Abre el directo en tu navegador (con la extensión ya instalada). Chrome mostrará una barra que dice *«… está depurando este navegador»*: es normal y es la señal de que la extensión está leyendo el chat. No la cierres.
2. En VeTube, escribe el **mismo usuario** del directo (el `@usuario`, tal cual aparece).
3. Elige **«TikTok (navegador, experimental)»** en «Capturar el chat de:» y pulsa **Acceder**.

También puedes dejar que VeTube te la ofrezca sola: si elegís «TikTok» normal y la conexión habitual falla, VeTube te pregunta si querés pasar a leer desde el navegador (con el directo ya abierto ahí). Si aceptás, sigue leyendo sin reiniciar nada.

Requisitos: la extensión tiene que estar cargada **antes** de abrir el directo (si ya estaba abierto, recargá la pestaña), y no tengas las herramientas de desarrollador (F12) abiertas en esa pestaña, porque usan el mismo canal que la extensión.

## Notas de seguridad

- **La extensión solo lee lo que tu navegador ya recibe.** No burla ninguna protección de TikTok: la firma la sigue haciendo TikTok en tu propia sesión, como siempre.
- **Nunca envía tu cookie de sesión** (`sessionid`) ni ninguna credencial de tu cuenta. El chat de un directo público funciona igual sin haber iniciado sesión.
- **Todo queda en tu computadora.** La extensión solo habla con `127.0.0.1:8790` (VeTube, en tu propia máquina); nada se manda a ningún servidor externo ni a ningún tercero.
- **No modifica la página de TikTok** ni interfiere con su seguridad: solo observa el tráfico del chat, del mismo modo que lo verían las herramientas de desarrollador del navegador.

Más detalle técnico (cómo está hecha la extensión, el protocolo que usa para hablar con VeTube, y diagnóstico si algo no anda) está en `FIRMADOR_LOCAL.md` y en `interceptor_extension/LEEME.md`, dentro del código fuente de VeTube.
