# Publicar la extensión en la Chrome Web Store

Qué va en cada pestaña y campo del [panel de desarrollador de la Chrome Web Store](https://chrome.google.com/webstore/devconsole), listo para copiar y pegar. Los nombres de pestañas y campos están en inglés, como en la documentación de Google; si el panel está en español, pueden aparecer traducidos.

## Quién la publica

La ficha de la extensión la publica y la mantiene [piapenia](https://github.com/piapenia) desde su cuenta de desarrollador, en coordinación con metalalchemist. Los cambios a la extensión se integran en este repositorio como siempre; para que lleguen a quienes la instalaron desde la tienda, piapenia sube la versión nueva (ver «Después de publicar»).

## Antes de empezar

- **Cuenta de desarrollador:** Google pide tener activada la verificación en dos pasos y un correo de contacto verificado, y declarar si quien publica actúa como comerciante (*trader*) o no (*non-trader*), por la ley de servicios digitales de la Unión Europea. Esa declaración es personal: depende de la situación de quien publica, no de la extensión.
- **Versión de VeTube:** la extensión solo sirve con una VeTube que traiga el firmador local (`servicios/tiktok_interceptor.py`). La v3.96 no lo trae: está en `master` desde el 11 de septiembre de 2026. Si la revisión termina antes de que salga esa versión, conviene no publicar todavía (ver «Enviar a revisión», más abajo).
- **Pruebas:** `node interceptor_extension\pruebas\pruebas.js` tiene que terminar en «Todo en verde». Entre otras cosas, comprueba los límites que la tienda aplica al manifiesto.
- **Imágenes:** si cambiaron el popup o el ícono, `node interceptor_extension\tienda\generar_imagenes.js` las regenera.
- **Paquete:** `interceptor_extension\tienda\empaquetar.cmd` deja `vetube-extension.zip` en esta carpeta. Ese es el archivo que se sube.

## Pestaña Package

Subir `vetube-extension.zip`. El título y el resumen de la ficha salen del manifiesto (`name` y `description`) y no se pueden editar desde el panel: para cambiarlos hay que subir una versión nueva, con un `version` mayor.

## Pestaña Store listing

### Description

```text
Lee con tu lector de pantalla el chat de los directos de TikTok que abrís en Chrome, a través de VeTube.

VeTube es un programa libre para Windows que lee en voz alta el chat de directos de YouTube, Twitch, TikTok, Kick y otras plataformas, pensado también para quienes usan lector de pantalla. Esta extensión es su puente con TikTok desde el navegador.

Para qué sirve
Para leer el chat de un directo de TikTok, VeTube normalmente depende de un servicio externo que a menudo falla. Con esta extensión, el chat llega desde tu propio navegador, que ya tiene el directo abierto: la extensión copia los mensajes que Chrome ya está recibiendo y se los pasa a VeTube.

Cómo se usa
1. Abrí el directo de TikTok en Chrome. Chrome muestra la barra «… está depurando este navegador»: es normal y es la señal de que la extensión está leyendo el chat.
2. En VeTube, escribí el mismo @usuario del directo.
3. En «Capturar el chat de:», elegí «TikTok (navegador, experimental)» y pulsá Acceder.

El ícono de la extensión abre una ventana de estado pensada para lectores de pantalla: dice con palabras si VeTube está escuchando, a qué directo está enganchada y cuántos mensajes pasó.

Privacidad
- Todo queda en tu computadora: la extensión solo habla con VeTube, en la dirección local 127.0.0.1.
- No lee cookies ni contraseñas, y nunca envía tu sesión de TikTok.
- No envía nada a terceros, no usa analítica ni publicidad y no modifica las páginas.

Requisitos
- VeTube instalado y abierto, en una versión que incluya la opción «TikTok (navegador, experimental)».
- Si el directo ya estaba abierto antes de instalar la extensión, recargá la pestaña.
- No tengas abiertas las herramientas de desarrollador (F12) en la pestaña del directo: usan el mismo canal que la extensión.

Es software libre (GPL-3.0). Código y documentación: https://github.com/metalalchemist/VeTube
```

### Resto de la pestaña

- **Category:** grupo *Make Chrome yours* («Personaliza Chrome»), categoría *Accessibility* («Accesibilidad»).
- **Language:** Español (Latinoamérica). Los textos usan voseo, igual que el resto de VeTube en español.
- **Store icon:** `interceptor_extension/iconos/icono128.png`.
- **Screenshots:** `interceptor_extension/tienda/imagenes/captura-1280x800.png`.
- **Small promo tile:** `interceptor_extension/tienda/imagenes/mosaico-440x280.png`.
- **Marquee promo tile:** ninguno (es opcional).
- **YouTube video:** la documentación de Google no aclara si es obligatorio. Si el panel lo exige al enviar, habrá que grabar uno.
- **Homepage URL:** `https://github.com/metalalchemist/VeTube`
- **Support URL:** `https://github.com/metalalchemist/VeTube/issues`
- **Mature content:** no.

## Pestaña Privacy

### Single purpose

```text
Pasa a VeTube, un programa de accesibilidad que corre en la misma computadora, el chat de los directos de TikTok que la persona abre en Chrome, para que VeTube lo lea en voz alta o con un lector de pantalla.
```

### Permission justification

**debugger**

```text
La extensión lee las tramas del chat del directo que el navegador ya recibe por su websocket (evento Network.webSocketFrameReceived). No hay otra forma de hacerlo: la política de seguridad de contenido (CSP) de TikTok bloquea los content scripts del mundo MAIN, que serían la alternativa. El depurador solo se engancha a pestañas de tiktok.com, solo se usan las tramas del chat del directo, y no se envía ni se modifica nada en la página.
```

**storage**

```text
Guarda en chrome.storage.session el estado de funcionamiento (contadores, último error, directos enganchados) para que sobreviva cuando Chrome suspende el service worker y para mostrarlo en la ventana emergente. No guarda el contenido del chat.
```

**Host permission** (`https://*.tiktok.com/*` y `http://127.0.0.1:8790/*`)

```text
tiktok.com: para saber qué pestañas son de TikTok, engancharles el depurador y leer el @usuario del directo desde la dirección de la pestaña. 127.0.0.1:8790: es VeTube, en la misma computadora; el service worker le envía ahí el chat. No se contacta ningún otro servidor.
```

### Remote code

No, la extensión no usa código remoto. Todo el código viaja en el paquete.

### Data usage

- Marcar **Website content** («Contenido de sitios web»): son los mensajes del chat del directo. No marcar ninguna otra categoría: la extensión no lee credenciales, ni historial, ni ubicación, ni datos de pago.
- Marcar las tres certificaciones: no se venden ni transfieren datos a terceros, no se usan para fines ajenos al propósito único, y no se usan para evaluar solvencia ni para préstamos.

### Privacy policy

`https://github.com/metalalchemist/VeTube/blob/master/interceptor_extension/PRIVACIDAD.md`

Esa dirección funciona recién cuando `PRIVACIDAD.md` esté integrado en `master`.

## Pestaña Distribution

- **Payments:** gratis.
- **Visibility:** *Public* la muestra en las búsquedas de la tienda. *Unlisted* la deja instalable solo para quien tenga el enlace, por ejemplo desde la documentación de VeTube.
- **Regions:** todas.

## Pestaña Test instructions (opcional)

```text
This extension is a companion for VeTube, a free Windows desktop app that reads live-stream chats aloud (https://github.com/metalalchemist/VeTube). It forwards TikTok live chat frames to VeTube on http://127.0.0.1:8790 and talks to no other server.

To check it without VeTube:
1. Install the extension and open any TikTok live stream (https://www.tiktok.com/@<user>/live).
2. Chrome shows the "is debugging this browser" bar: that is the debugger attaching, which is expected.
3. Open the extension popup (its text is in Spanish). It reports that VeTube is not listening, that the webcast websocket is connected to the stream, and how many frames were dropped because VeTube is not running.

To check it end to end, run VeTube from source (master branch), choose "TikTok (navegador, experimental)" in "Capturar el chat de:", type the same @user, and press Acceder. The chat is then read aloud by VeTube.
```

## Enviar a revisión

- Google suele revisar en pocos días, pero puede tardar algunas semanas. El permiso `debugger` y que la cuenta sea nueva pueden alargar la revisión.
- Al enviar hay una casilla para publicar automáticamente al aprobarse. Si VeTube todavía no publicó una versión con el firmador local, desmarcarla: la extensión queda aprobada y hay **30 días** para publicarla a mano. Pasado ese plazo, vuelve a borrador y hay que enviarla de nuevo.
- Si la rechazan, llega un correo con la política incumplida y cómo apelar.

## Después de publicar

- Cambiar la sección «Cómo instalarla» de `doc/*/tiktok_navegador.md` (hoy dice que la extensión no está en la tienda; son 8 idiomas) y de `interceptor_extension/LEEME.md`, con el enlace a la ficha.
- En cada actualización: subir `version` en `manifest.json`, correr las pruebas, volver a armar el ZIP y subirlo en la pestaña Package.
