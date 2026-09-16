# Política de privacidad de la extensión «VeTube – puente del chat de TikTok Live»

*English version below.*

Última actualización: 16 de septiembre de 2026.

Esta extensión forma parte de [VeTube](https://github.com/metalalchemist/VeTube), un programa libre (licencia GPL-3.0) para leer de forma accesible el chat de los directos. Su único propósito es pasarle a VeTube, que corre en tu misma computadora, el chat de los directos de TikTok que abrís en el navegador.

## Qué datos maneja

- **El contenido del chat de los directos de TikTok.** Cuando tenés abierta una página de `tiktok.com`, la extensión lee con la API de depuración de Chrome las tramas que tu navegador recibe por la conexión del chat del directo (el *websocket* del *webcast*). Esas tramas traen lo que se ve en el chat: mensajes, nombres de usuario de quienes participan, regalos, «me gusta» y avisos similares.
- **Los datos del directo abierto.** El usuario (`@usuario`) del directo, que sale de la dirección de la pestaña; el identificador de la sala; y la dirección de esa conexión del chat.
- **El estado de funcionamiento.** Contadores (cuántas tramas se enviaron o se descartaron), el último error y qué directos están enganchados, para mostrarlos en la ventana emergente de la extensión.

## Qué hace con esos datos

- Envía el contenido del chat y los datos del directo **solo a VeTube, en tu propia computadora**, por la dirección local `http://127.0.0.1:8790`. Esa dirección no sale de tu máquina.
- Guarda el estado de funcionamiento en el almacenamiento de sesión del navegador (`chrome.storage.session`), que vive en memoria y se borra al cerrar el navegador.
- No guarda el contenido del chat: lo retiene en memoria apenas unos instantes para agruparlo antes de enviarlo, y si VeTube no está escuchando, lo descarta.

## Qué no hace

- No envía nada a servidores de quienes desarrollan la extensión ni a ningún tercero. No usa analítica, publicidad ni rastreo.
- No lee cookies ni contraseñas, y nunca envía tu cookie de sesión de TikTok ni ninguna credencial.
- No lee tu historial de navegación. Solo se engancha a pestañas de `tiktok.com`, y de todo el tráfico de esas pestañas solo usa la conexión del chat de los directos; el resto no lo envía ni lo guarda.
- No modifica ni bloquea las páginas: solo observa.
- No ejecuta código descargado de internet.
- No vende ni transfiere datos a nadie, ni los usa para ningún fin distinto de pasarle el chat a VeTube.

Mientras la extensión está enganchada a una pestaña, Chrome muestra la barra «… está depurando este navegador». Es el aviso del propio Chrome de que se está usando la API de depuración.

Lo que VeTube haga después con el chat (por ejemplo, leerlo en voz alta) depende de su configuración y se describe en la documentación de VeTube.

## Cambios y contacto

Si esta política cambia, la versión nueva se publica en este mismo archivo con la fecha actualizada. Para preguntas, abrí un *issue* en <https://github.com/metalalchemist/VeTube/issues>.

---

# Privacy policy for the "VeTube – puente del chat de TikTok Live" extension

Last updated: September 16, 2026.

This extension is part of [VeTube](https://github.com/metalalchemist/VeTube), a free program (GPL-3.0 license) for reading live-stream chats accessibly. Its single purpose is to pass the chat of the TikTok live streams you open in your browser to VeTube, which runs on your own computer.

## Data it handles

- **TikTok live chat content.** While a `tiktok.com` page is open, the extension uses Chrome's debugger API to read the frames your browser receives over the live stream's chat connection (the webcast websocket). Those frames carry what the chat shows: messages, usernames of participants, gifts, likes and similar notices.
- **Data about the open live stream.** The streamer's `@username`, taken from the tab's address; the room identifier; and the address of that chat connection.
- **Operating status.** Counters (how many frames were sent or dropped), the last error and which live streams are connected, shown in the extension's popup.

## What it does with that data

- It sends the chat content and the live stream data **only to VeTube on your own computer**, through the local address `http://127.0.0.1:8790`. That address never leaves your machine.
- It keeps the operating status in the browser's session storage (`chrome.storage.session`), which lives in memory and is cleared when the browser closes.
- It does not store chat content: it holds it in memory only for a moment to batch it before sending, and drops it if VeTube is not listening.

## What it does not do

- It does not send anything to the developers' servers or to any third party. No analytics, advertising or tracking.
- It does not read cookies or passwords, and never sends your TikTok session cookie or any credential.
- It does not read your browsing history. It only attaches to `tiktok.com` tabs, and of all the traffic in those tabs it only uses the live chat connection; nothing else is sent or stored.
- It does not modify or block pages: it only observes.
- It does not run code downloaded from the internet.
- It does not sell or transfer data to anyone, nor use it for any purpose other than passing the chat to VeTube.

While the extension is attached to a tab, Chrome shows the "… is debugging this browser" bar. That is Chrome's own notice that the debugger API is in use.

What VeTube does with the chat afterwards (for example, reading it aloud) depends on its settings and is described in VeTube's documentation.

## Changes and contact

If this policy changes, the new version is published in this same file with an updated date. For questions, open an issue at <https://github.com/metalalchemist/VeTube/issues>.
