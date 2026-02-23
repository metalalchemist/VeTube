# vetube
Lee y gestiona de manera accesible el chat de tus propios directos o en los de tus creadores favoritos.
[demostración del producto en funcionamiento](https://youtu.be/4XawJoBymPs)
## sitios soportados:
- youtube (extrenos y directos en curso y pasados)
- twich.tv(directos en curso y pasados)
- tiktok(directos en curso)
- kick (directos en curso)
- la sala dejuegos(chat de las diversas mesas)
## Características
- Modo automático: Lee los mensajes de chat en tiempo real utilizando la voz sapy5
- Interfaz invisible: Gestiona los chats desde cualquier ventana utilizando simples comandos de teclado. Es necesario tener un lector de pantalla activo.
- Lectores soportados:
  - NVDA
  - JAWS
  - Window-Eyes
  - SuperNova
  - System Access
  - PC Talker
  - ZDSR
- Posibilidad de configurar según las necesidades del usuario.
  - activa o desactiva los sonidos del programa.
  - activa o desactiva la lectura automática. 
  - configura el listado de los mensajes en la interfaz invisible.
  - Configura las preferencias de la voz sapy.
  - personaliza los atajos de teclado globales
- mantén múltiples capturas de chats.
- cambia de modalidad de lectura de chats fácilmente: decide si quieres leer todos los chats o solo los de alguna categoría en específico.
- guarda tus envivos en una sección de favoritos. repite cuantas veces  desees el chat sin necesidad de ir a buscar el enlace nuevamente.
- archiva unmensaje: útil para tener recordatorios.
- traduce el chat de un streaming al idiomma que  gustes.

## Atajos de teclado.
### Usando interfaz invisible.
| acción                    | combinación de teclas |
| ------------------------- | ----------- |
| Silencia la voz sapy      | control+p           |
| iniciar/cancelar la captura de un nuevo en vivo      | alt shift h            |
| ir al en vivo anterior      | control alt shift flecha izquierda            |
| ir al siguiente en vivo     | control alt shift flecha derecha            |
| buffer anterior      | alt shift flecha izquierda            |
| buffer siguiente      | alt shift flecha derecha            |
| Elemento anterior      | alt shift flecha arriba           |
| Elemento siguiente      | alt shift flecha abajo           |
| Elemento inicial      | alt shift inicio           |
| Elemento final      | alt shift fin           |
| archiva un mensaje      | alt shift a           |
| Copia el mensaje actual      | alt shift c           |
| Borra un buffer previamente creado      | alt shift d           |
| añade el mensaje al buffer de favoritos      | alt shift f           |
| Activa o desactiva la lectura automática      | alt shift r           |
| desactiva los sonidos del programa      | alt shift p           |
| buscar una palabra entre  los mensajes      | alt shift b           |
| muestra el mensaje actual en un cuadro de texto      | alt shift v           |
| invocar el editor de teclado de vetube      | alt shift k           |
| pausa o reanuda la reproducción de un en vivo      | control shift p           |
| adelantar la reproducción del en vivo      | control shift flecha derecha           |
| atrazar la reproducción del en vivo      | control shift flecha izquierda           |
| subir el volumen      | control shift flecha arriba           |
| bajar el volumen      | control shift flecha abajo           |
| detener y liberar el reproductor      | control shift s           |

### En el historial  del chat:
| acción                    | combinación de teclas |
| ------------------------- | ----------- |
| Reproducir mensaje seleccionado      | espacio           |

### En la sección de favoritos:
| acción                    | combinación de teclas |
| ------------------------- | ----------- |
| acceder a un enlace seleccionado      | espacio           |

## futuras actualizaciones:
He agregado para  futuras actualizaciones próximas
- Posibilidad de mostrar información de la persona que está chateando desde la interfaz invisible:
  - Nombre del canal del usuario
  - Entre muchas cosas mas.

## Colaborar en la traducción
Si deseas colaborar traduciendo VeTube a tu idioma, necesitarás instalar las herramientas de internacionalización.

1.  **Instalar Babel:**
    ```bash
    pip install Babel
    ```
    *Nota: Asegúrate de instalar el paquete `Babel` (mayúscula B recomendada en PyPI, aunque pip no distingue), evita paquetes incorrectos de tamaño diminuto.*

2.  **Extraer textos para actualizar la plantilla (.pot):**
    Si de nuevas cadenas se han añadido al código, actualiza el archivo plantilla:
    ```bash
    pybabel extract -F babel.cfg -o vetube.pot .
    ```

3.  **Iniciar una nueva traducción:**
    Si vas a traducir a un nuevo idioma (ejemplo `it` para italiano):
    ```bash
    pybabel init -i vetube.pot -d locales -l it -D vetube
    ```

4.  **Actualizar traducciones existentes:**
    Si ya existe el idioma y has actualizado el `.pot`, sincroniza los archivos `.po`:
    ```bash
    pybabel update -i vetube.pot -d locales -D vetube
    ```

5.  **Compilar traducciones:**
    Para que el programa reconozca los cambios, compila los archivos `.po` a `.mo`:
    ```bash
    pybabel compile -d locales -D vetube
    ```

# agradecimientos:
Agradesco a:

[4everzyanya](https://www.youtube.com/c/4everzyanya/),

Principal tester del proyecto.

[Johan G](https://github.com/JohanAnim),

Quien ayudó  ha crear la interfaz gráfica para el proyecto y a corregir  ciertos bugs menores.

Se que gracias a ustedes esta aplicación seguirá mejorando y cada una de sus ideas y colaboraciones serán bienvenidas a este proyecto que iremos construyendo entre todos.

Para ideas, bugs y sugerencias Puedes escribirme a 
cesar.verastegui17@gmail.com
## Links de descarga.
Con tu apoyo contribuyes a que este programa siga en crecimiento.

[¿Te unes a nuestra causa?](https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U)

[descarga el programa para 64 bits](https://github.com/metalalchemist/VeTube/releases/download/v3.7/VeTube-x64.zip)
[descarga el programa para 32 bits](https://github.com/metalalchemist/VeTube/releases/download/v3.7/VeTube-x86.zip)
