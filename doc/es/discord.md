# VeTube y Discord: guía paso a paso

VeTube puede leer en tiempo real los mensajes de un canal de texto de un servidor de Discord. Para hacerlo por la vía oficial, Discord exige usar un «bot»: una cuenta especial que tú mismo creas gratis, una sola vez, en unos 10 minutos. Esta guía explica todo el proceso y está pensada para usuarios de lectores de pantalla (sin capturas de pantalla, con los nombres exactos de cada botón).

Nota: el portal de desarrolladores de Discord está solo en inglés, por eso los nombres de sus botones aparecen aquí en inglés. La aplicación de chat de Discord sí está traducida.

## Lo que necesitas
- Una cuenta de Discord.
- Permiso para invitar bots al servidor que quieres leer (permiso «Gestionar servidor»). Si no lo tienes, al final del paso 4 puedes enviar el enlace de invitación a un administrador para que lo abra él.

## Paso 1: crear la aplicación
1. Abre https://discord.com/developers/applications e inicia sesión.
2. Pulsa el botón «New Application».
3. Escribe un nombre (por ejemplo «VeTube»), acepta los términos y pulsa «Create».

## Paso 2: obtener el token del bot
1. En la página de tu aplicación, ve a la sección «Bot» del menú de la izquierda.
2. Pulsa el botón «Reset Token» y confirma con «Yes, do it!». Si tienes verificación en dos pasos, se te pedirá el código.
3. Aparece el token nuevo con un botón «Copy» para copiarlo al portapapeles. Pégalo temporalmente en un lugar seguro, por ejemplo el Bloc de notas.

Importante: el token es como la contraseña de tu bot. No lo compartas ni lo publiques. Si se filtra, vuelve a esta página y pulsa «Reset Token» para generar otro; el anterior deja de funcionar.

## Paso 3: activar «Message Content Intent»
Sin esta opción, Discord no deja que el bot lea el contenido de los mensajes.
1. En la misma sección «Bot», baja hasta «Privileged Gateway Intents».
2. Activa el interruptor «Message Content Intent».
3. Pulsa «Save Changes» en la barra que aparece.

## Paso 4: invitar el bot a tu servidor
1. Ve a la sección «OAuth2» del menú de la izquierda y busca «URL Generator».
2. En la lista «Scopes», marca la casilla «bot».
3. En «Bot Permissions», que aparece debajo, marca «View Channels» y «Read Message History».
4. Al final de la página, en «Generated URL», pulsa «Copy».
5. Abre esa URL en tu navegador, elige el servidor en el cuadro combinado y pulsa «Continuar» y luego «Autorizar». (Si no tienes permiso para invitar bots, envía esa URL a un administrador del servidor.)

## Paso 5: copiar el enlace del canal
1. En Discord, localiza el canal de texto que quieres leer.
2. Abre su menú contextual: clic derecho, o tecla de aplicaciones o Mayús+F10 con el lector de pantalla.
3. Elige «Copiar enlace». El enlace tiene esta forma: https://discord.com/channels/1234567890/0987654321

## Paso 6: pegar en VeTube
1. Abre VeTube, pega el enlace del canal en el cuadro de texto principal y pulsa «Acceder» o Intro.
2. La primera vez, VeTube te pedirá el token del bot: pégalo y pulsa «Aceptar». Quedará guardado y no se te volverá a pedir.
3. ¡Listo! Los mensajes del canal empezarán a llegar. Los mensajes del dueño del servidor y de quienes pueden moderar aparecen en la categoría «Moderadores»; el resto, en «General».

## Solución de problemas
- «El token no es válido»: copia el token completo desde el portal (paso 2). Ante la duda, genera uno nuevo con «Reset Token».
- «Al bot le falta activar Message Content Intent»: revisa el paso 3 y guarda los cambios.
- «No se encontró el canal»: comprueba que invitaste el bot a ese mismo servidor (paso 4) y que copiaste el enlace del canal correcto (paso 5).
- El chat conecta pero no llegan mensajes: asegúrate de que el bot puede ver ese canal. En canales privados hay que darle acceso o un rol que lo tenga.
