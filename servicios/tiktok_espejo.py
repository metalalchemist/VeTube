"""Ruta B del firmador local: VeTube no abre ningún websocket, mira el del navegador.

El navegador del usuario, al abrir el directo, ya tiene su websocket firmado y
funcionando. La extensión copia las tramas binarias tal cual llegan y las manda a
servicios/tiktok_interceptor por el puerto local; aquí se traducen a los objetos
que TikTokLive espera y se meten en su flujo de eventos, sin volver a firmar
nada y sin que la sesión del usuario salga de su navegador.

Los acks y los latidos los sigue mandando el navegador por ese mismo socket, así
que VeTube no debe mandar ninguno: el espejo es de solo lectura. Esa es la
diferencia de fondo con la ruta A, donde VeTube abría su propio socket con una
URL firmada que caduca a los 30 segundos y que además el navegador ya consumió.

--------------------------------------------------------------------------------
Dónde enchufa (verificado sobre TikTokLive 7.0.1 instalada)
--------------------------------------------------------------------------------
`TikTokLiveClient` le pide al cliente de websocket exactamente tres cosas, y
nada más, en client.py:

    línea 171  if self._ws.connected:              -> AlreadyConnectedError
    línea 358  await self._ws.disconnect()
    línea 475  async for webcast_response in self._ws.connect(...)
    línea 810  return self._ws.connected           (la propiedad pública)

Con esa superficie tan chica sale más limpio sustituir el objeto entero
(`client._ws = WebsocketEspejo(...)`) que parchear métodos sueltos de
WebcastWSClient y arrastrar su estado sin usar: el contador de seq, el bucle de
ping y el generador de conexión existen solo para hablar por un socket que aquí
no hay. Un espejo que no los tiene no puede mandar un latido por descuido.

La otra sustitución es la del firmador: `client.web.fetch_signed_websocket`, la
única llamada al servidor de firmas (client.py línea 207), que aquí se limita a
esperar a que el navegador aparezca y devolver un estado inicial vacío.
"""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import Callable, Optional

from TikTokLive.client.ws.ws_utils import (
    extract_webcast_push_frame,
    extract_webcast_response_message,
)
from TikTokLive.proto import ProtoMessageFetchResult

from servicios.tiktok_interceptor import (
    CENTINELA_CIERRE,
    ESPERA_CAPTURA_S,
    SIN_TRAMA,
    AlmacenSesiones,
    SesionNavegador,
    normalizar_id,
)

logger = getLogger(__name__)


def decodificar_trama(datos: bytes) -> Optional[ProtoMessageFetchResult]:
    """Una trama binaria del navegador, convertida en lo que espera la librería.

    Devuelve None cuando la trama no trae eventos, que es lo normal en buena
    parte de ellas: solo las de payload_type "msg" llevan mensajes. Las de tipo
    "hb" (el latido que manda el servidor), "ack" e "im_enter_room_resp" son
    transporte, y la propia librería las tira igual (ws_connect.py, dentro de
    __aiter__). También devuelve None si la trama no parsea: una trama rota no
    vale un corte de conexión en mitad de un directo.

    El desempaquetado (gzip o sin comprimir, según la cabecera compress_type) lo
    hace extract_webcast_response_message, o sea la propia librería. Aquí no se
    reimplementa nada del protocolo.
    """
    try:
        trama = extract_webcast_push_frame(datos, logger=logger)
    except Exception:
        logger.debug(
            "Trama descartada: no parsea como WebcastPushFrame (%s bytes)",
            len(datos or b""),
        )
        return None

    if trama.payload_type != "msg":
        logger.debug(
            "Trama de transporte ignorada (tipo=%r, %s bytes de carga)",
            trama.payload_type,
            len(trama.payload or b""),
        )
        return None

    try:
        respuesta = extract_webcast_response_message(trama, logger=logger)
    except Exception:
        logger.warning(
            "Trama 'msg' de %s bytes que no se pudo desempaquetar; se sigue",
            len(trama.payload or b""),
        )
        return None

    # is_first solo lo trae el estado inicial. Si una trama del navegador llegara
    # marcada, la librería emitiría otro ConnectEvent y VeTube volvería a decir
    # "Ingresando al chat" por el lector de pantalla en mitad del chat.
    respuesta.is_first = False
    return respuesta


class WebsocketEspejo:
    """Ocupa el sitio del cliente de websocket sin abrir ninguno.

    Cumple la superficie que usa TikTokLiveClient (connected / disconnect /
    connect) leyendo de la cola que llena el servidor local. No manda nada: ni
    acks, ni latidos, ni el mensaje de entrada a la sala. De eso se sigue
    encargando el navegador, que es quien tiene el socket de verdad.
    """

    # Cada cuánto despierta la espera de tramas. Solo marca lo que tarda en
    # notarse un cierre; las tramas que llegan despiertan la cola al instante.
    ESPERA_TRAMA_S = 1.0

    def __init__(
        self,
        sesiones: AlmacenSesiones,
        unique_id: str,
        *,
        timeout: float = ESPERA_CAPTURA_S,
        avisar: Optional[Callable[[str], None]] = None,
    ):
        self._sesiones = sesiones
        self._unique_id = normalizar_id(unique_id)
        self._timeout = timeout
        self._avisar = avisar
        self.sesion: Optional[SesionNavegador] = None
        self._abierto = False
        self._cierre_pedido = False
        self.tramas_vistas = 0
        self.tramas_con_eventos = 0

    # -- la superficie que usa TikTokLiveClient -----------------------------

    @property
    def connected(self) -> bool:
        return self._abierto

    async def disconnect(self) -> None:
        self._cierre_pedido = True
        self._abierto = False
        if self.sesion is not None:
            # Cerrar la cola despierta la espera en el acto: sin esto, detener
            # el chat tardaría lo que queda de ESPERA_TRAMA_S en notarse.
            self.sesion.cola.cerrar()

    async def connect(
        self,
        room_id=None,
        cookies=None,
        user_agent=None,
        initial_webcast_response: Optional[ProtoMessageFetchResult] = None,
        process_connect_events: bool = True,
        compress_ws_events: bool = True,
    ):
        """Generador de ProtoMessageFetchResult, alimentado por el navegador.

        Misma firma y mismo contrato que WebcastWSClient.connect: el bucle de
        client.py (_ws_client_loop) no distingue. cookies, user_agent y
        compress_ws_events se aceptan y se ignoran a propósito: el socket es del
        navegador y ya negoció todo eso por su cuenta.
        """
        sesion = self.sesion
        if sesion is None:
            sesion = await asyncio.to_thread(
                self._sesiones.esperar, self._unique_id, self._timeout
            )
        if sesion is None:
            raise TimeoutError(
                "El navegador no abrió ningún directo. ¿Está la extensión "
                "puesta y el directo abierto en una pestaña?"
            )
        self.sesion = sesion
        self._abierto = not self._cierre_pedido

        logger.info(
            "Espejo enganchado al navegador para @%s (sala %s)",
            sesion.unique_id or "(comodín)",
            sesion.room_id or "desconocida",
        )
        self._aviso("Leyendo el chat desde el navegador.")

        try:
            if initial_webcast_response is not None:
                # Igual que la librería: con la casilla de historial desmarcada,
                # el estado inicial se entrega sin sus mensajes.
                if not process_connect_events:
                    initial_webcast_response.messages = []
                yield initial_webcast_response

            while self._abierto:
                crudo = await asyncio.to_thread(
                    sesion.cola.siguiente, self.ESPERA_TRAMA_S
                )
                if crudo is CENTINELA_CIERRE:
                    break
                if crudo is SIN_TRAMA:
                    # Silencio en el chat, no desconexión: se sigue esperando
                    # mientras el navegador tenga el directo abierto.
                    if not sesion.abierta:
                        break
                    continue

                self.tramas_vistas += 1
                respuesta = decodificar_trama(crudo)
                if respuesta is None:
                    continue
                self.tramas_con_eventos += 1
                yield respuesta
        finally:
            self._abierto = False
            logger.info(
                "Espejo desenganchado de @%s: %s tramas vistas, %s con eventos",
                sesion.unique_id or "(comodín)",
                self.tramas_vistas,
                self.tramas_con_eventos,
            )

    # -- interno -------------------------------------------------------------

    def _aviso(self, texto: str) -> None:
        """Un aviso para el usuario, si quien instaló el espejo pasó por dónde.

        Se hace por callback y no importando wx aquí para que este módulo siga
        siendo importable (y testeable) sin interfaz gráfica.
        """
        if self._avisar is None:
            return
        try:
            self._avisar(texto)
        except Exception:
            logger.debug("Fallo al avisar al usuario", exc_info=True)


def instalar_espejo(
    client,
    sesiones: AlmacenSesiones,
    *,
    timeout: float = ESPERA_CAPTURA_S,
    avisar: Optional[Callable[[str], None]] = None,
) -> WebsocketEspejo:
    """Deja el cliente de TikTokLive leyendo del navegador en vez de la red.

    Sustituye cuatro cosas, todas por el mismo motivo: que nada del arranque
    dependa de TikTok cuando el navegador ya tiene la respuesta.

      1. client._ws                       -> el espejo (no abre websocket)
      2. client.web.fetch_signed_websocket -> espera al navegador, sin firmar
      3. client.web.fetch_room_id_from_html -> la sala que informó la extensión
      4. client.web.fetch_is_live           -> hay sesión abierta, luego hay directo

    Las dos últimas conservan la implementación original como respaldo, para no
    empeorar el caso en que el navegador todavía no avisó de nada.

    Es el mismo patrón de sustitución que servicios/tiktok.py ya usa en
    _instrumentar_historial.
    """
    id_cliente = normalizar_id(getattr(client, "unique_id", ""))
    espejo = WebsocketEspejo(sesiones, id_cliente, timeout=timeout, avisar=avisar)

    async def fetch_desde_navegador(platform=None, *args, **kwargs):
        """El estado inicial que la librería pide al firmador, sin firmador.

        No lleva push_server ni route_params porque nadie va a construir una
        URL con ellos: el espejo no conecta. is_first sí, que es lo que hace
        que TikTokLive emita el ConnectEvent con el que VeTube anuncia la
        entrada al chat.
        """
        logger.info(
            "Esperando a que el navegador abra el directo de @%s (hasta %ss)...",
            id_cliente,
            int(timeout),
        )
        if avisar is not None:
            avisar(
                "Abrí el directo en el navegador con la extensión puesta. Esperando..."
            )
        # El almacén bloquea con hilos; se saca del hilo del bucle asyncio.
        sesion = await asyncio.to_thread(sesiones.esperar, id_cliente, timeout)
        if sesion is None:
            raise TimeoutError(
                "No llegó ninguna sesión del navegador. ¿Está el directo "
                "abierto en el navegador con la extensión puesta?"
            )
        espejo.sesion = sesion
        return ProtoMessageFetchResult(
            messages=[],
            cursor="0",
            route_params={},
            push_server="",
            history_comment_cursor="0",
            is_first=True,
        )

    room_id_original = client.web.fetch_room_id_from_html
    is_live_original = client.web.fetch_is_live

    # Los nombres de los parámetros son los de la librería a propósito: la
    # llama con palabra clave (fetch_is_live(unique_id=...)) y renombrarlos
    # mandaría el valor a **kwargs sin que nadie lo notara.
    async def room_id_del_navegador(unique_id=None, *args, **kwargs):
        """La sala que informó la extensión, que es la que el usuario está viendo.

        Evita el raspado del HTML del directo, que es justo lo que TikTok
        responde con captcha cuando le da por ahí.
        """
        sesion = sesiones.obtener(unique_id or id_cliente)
        if sesion is not None and sesion.room_id:
            return str(sesion.room_id)
        logger.debug("La extensión no informó la sala; se raspa el HTML como antes")
        return await room_id_original(unique_id or id_cliente, *args, **kwargs)

    async def esta_en_vivo(room_id=None, unique_id=None, *args, **kwargs):
        """Si el navegador tiene el directo abierto, está en vivo: no hay más que mirar."""
        sesion = sesiones.obtener(unique_id or id_cliente)
        if sesion is not None and sesion.abierta:
            return True
        return await is_live_original(
            room_id=room_id, unique_id=unique_id or id_cliente
        )

    client._ws = espejo
    client.web.fetch_signed_websocket = fetch_desde_navegador
    client.web.fetch_room_id_from_html = room_id_del_navegador
    client.web.fetch_is_live = esta_en_vivo

    logger.info("Firmador local (ruta espejo) instalado para @%s", id_cliente)
    return espejo
