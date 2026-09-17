"""Firmador local: la mitad de VeTube. Recibe lo que ve el navegador del usuario.

ESTADO: detrás de la opción «tiktok_firmador_local», apagada de fábrica.

--------------------------------------------------------------------------------
La idea
--------------------------------------------------------------------------------
TikTok no deja abrir el websocket del chat sin una petición firmada. Hasta ahora
esa firma la calculaba un servidor externo (EulerStream), que se cae y comparte
cupo. En vez de eso, el navegador del usuario —logueado o no— que abre el directo
YA hace esa petición firmada él solo. Una extensión mira lo que el navegador hace
y se lo pasa a VeTube por este puerto local. La firma nunca se recalcula y la
sesión del usuario no sale de su navegador.

Este módulo es la mitad que vive dentro de VeTube: el servidor local que recibe.
La otra mitad (traducir lo recibido a eventos de TikTokLive) está en
servicios/tiktok_espejo.py.

--------------------------------------------------------------------------------
Las dos rutas
--------------------------------------------------------------------------------
Ruta A (`/captura`, `instalar()`): se copia la URL firmada del websocket y VeTube
abre su propio websocket con ella. Es frágil por dos motivos documentados en la
propia librería: las URLs firmadas caducan a los 30 segundos (ws_connect.py, en
el comentario de __aiter__) y encima el navegador ya la consumió. Se conserva
porque cuesta poco y sirve de plan de emergencia.

Ruta B (`/sesion` + `/tramas`, ver tiktok_espejo): el navegador se queda con su
websocket y la extensión copia las tramas binarias tal cual llegan. VeTube no
abre ningún websocket a TikTok: parsea esas tramas y las mete en el flujo de
eventos de la librería. Los acks y los latidos los sigue mandando el navegador,
así que VeTube no debe mandarlos. Es la ruta principal.

--------------------------------------------------------------------------------
Contrato con la extensión (versión 2)
--------------------------------------------------------------------------------
    GET  /salud    -> 200 {"ok": true, "version": 2}
    POST /captura  -> ruta A. {"unique_id","room_id","ws_url","cookies":{...},"cursor"}
    POST /sesion   -> aviso de estado. {"unique_id","room_id","estado":"abierto"|"cerrado","ws_url"}
    POST /tramas   -> ruta B. {"unique_id","room_id","seq":<entero>,
                               "tramas":["<base64 de la trama binaria>", ...]}
                      respuesta {"ok": true, "recibidas": <n>}

`seq` es monotónico por sesión y solo sirve para detectar huecos: si llega uno no
consecutivo se anota en el log y se sigue, porque perder tramas de un chat en
vivo no es motivo para tirar la conexión.

Nada de esto contacta con TikTok: eso lo hace el navegador del usuario. Este
módulo solo escucha en 127.0.0.1.

--------------------------------------------------------------------------------
Qué NO se registra
--------------------------------------------------------------------------------
Ni valores de cookies, ni sessionid, ni la query firmada. Del websocket solo se
guarda la forma: host, cantidades, longitudes. Es la regla que hace que este
puente sea aceptable en primer lugar.
"""

from __future__ import annotations

import base64
import binascii
import json
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging import getLogger
from typing import Optional
from urllib.parse import urlparse

import httpx
from TikTokLive.proto import ProtoMessageFetchResult

logger = getLogger(__name__)

PUERTO_POR_DEFECTO = 8790
# Versión del contrato con la extensión. Si esto sube, la extensión tiene que
# enterarse: /salud lo publica para que pueda avisar en vez de fallar en silencio.
VERSION_CONTRATO = 2
# Cuánto espera el firmador a que el navegador aparezca antes de rendirse. El
# usuario tiene que abrir el directo con la extensión puesta; darle margen es
# razonable, más aún moviéndose con lector de pantalla.
ESPERA_CAPTURA_S = 120
# Tope de tramas en espera por sesión. Acotado a propósito: si la extensión
# manda y VeTube todavía no consume, de un chat en vivo lo que interesa es lo
# último, no lo primero.
MAX_TRAMAS_EN_COLA = 2000

# Centinelas de ColaTramas.siguiente(): objetos que se comparan por identidad,
# porque una trama vacía (b"") es un valor posible y no debe confundirse.
CENTINELA_CIERRE = object()
SIN_TRAMA = object()


def normalizar_id(valor) -> str:
    """@Usuario, Usuario y usuario son el mismo directo."""
    return str(valor or "").lstrip("@").strip().lower()


# ---------------------------------------------------------------------------
# Ruta A: la URL firmada
# ---------------------------------------------------------------------------


class Captura:
    """Una conexión firmada tal y como la observó el navegador."""

    def __init__(self, datos: dict):
        self.unique_id = normalizar_id(datos.get("unique_id"))
        self.room_id = str(datos.get("room_id", "")) or None
        self.ws_url = str(datos.get("ws_url", ""))
        self.cursor = str(datos.get("cursor", "") or "0")
        self.recibida_en = time.time()
        # Cookies: se aceptan como diccionario o como cabecera "a=1; b=2".
        self.cookies: dict[str, str] = {}
        if isinstance(datos.get("cookies"), dict):
            self.cookies = {str(k): str(v) for k, v in datos["cookies"].items()}
        elif datos.get("cookie_header"):
            for trozo in str(datos["cookie_header"]).split(";"):
                if "=" in trozo:
                    k, _, v = trozo.partition("=")
                    self.cookies[k.strip()] = v.strip()

    def es_valida(self) -> bool:
        return self.ws_url.startswith("wss://") and "tiktok" in self.ws_url

    def coincide_con(self, unique_id: str) -> bool:
        # Sin unique_id en la captura, se acepta como comodín: el interceptor
        # más simple puede no saber el nombre y mandar solo la URL.
        if not self.unique_id:
            return True
        return self.unique_id == normalizar_id(unique_id)


class AlmacenCapturas:
    """Guarda la última captura de cada directo, con espera bloqueante."""

    def __init__(self):
        self._lock = threading.Lock()
        self._por_usuario: dict[str, Captura] = {}
        self._evento = threading.Event()

    def guardar(self, captura: Captura) -> None:
        with self._lock:
            self._por_usuario[captura.unique_id] = captura
        self._evento.set()
        logger.info(
            "Captura del interceptor recibida (usuario=%r, room=%s)",
            captura.unique_id or "(comodín)",
            captura.room_id,
        )

    def esperar(self, unique_id: str, timeout: float) -> Optional[Captura]:
        """Bloquea hasta que haya una captura para ese usuario, o None si vence."""
        limite = time.time() + timeout
        while time.time() < limite:
            with self._lock:
                for cap in self._por_usuario.values():
                    # Un unique_id de consulta vacío es comodín: acepta cualquier
                    # captura válida. (coincide_con maneja el comodín del lado de
                    # la captura; aquí faltaba el del lado de la consulta.)
                    if cap.es_valida() and (
                        not unique_id or cap.coincide_con(unique_id)
                    ):
                        return cap
            self._evento.wait(timeout=1.0)
            self._evento.clear()
        return None


# ---------------------------------------------------------------------------
# Ruta B: las tramas del websocket del navegador
# ---------------------------------------------------------------------------


class ColaTramas:
    """Cola acotada que cruza del hilo del servidor HTTP al del bucle asyncio.

    No se usa queue.Queue porque interesa descartar por la izquierda: cuando se
    llena, lo que sobra son las tramas viejas, no las que acaban de llegar. Un
    chat en vivo leído en voz alta con retraso es peor que un chat con huecos.
    """

    def __init__(self, maximo: int = MAX_TRAMAS_EN_COLA):
        self._cond = threading.Condition()
        self._tramas: deque = deque(maxlen=maximo)
        self._cerrada = False
        self.descartadas = 0

    def publicar(self, datos: bytes) -> None:
        with self._cond:
            if self._cerrada:
                return
            if len(self._tramas) == self._tramas.maxlen:
                self.descartadas += 1
            self._tramas.append(datos)
            self._cond.notify()

    def cerrar(self) -> None:
        with self._cond:
            self._cerrada = True
            self._cond.notify_all()

    @property
    def cerrada(self) -> bool:
        with self._cond:
            return self._cerrada

    def pendientes(self) -> int:
        with self._cond:
            return len(self._tramas)

    def siguiente(self, timeout: float):
        """La próxima trama, SIN_TRAMA si venció la espera, CENTINELA_CIERRE al final.

        Las tramas ya encoladas se entregan aunque la cola esté cerrada: cerrar
        significa «el navegador se fue», no «tirá lo que quedaba».
        """
        with self._cond:
            if not self._tramas and not self._cerrada:
                self._cond.wait(timeout)
            if self._tramas:
                return self._tramas.popleft()
            if self._cerrada:
                return CENTINELA_CIERRE
            return SIN_TRAMA


class SesionNavegador:
    """Lo que el navegador tiene abierto ahora mismo para un directo.

    El websocket del webcast se reutiliza entre salas (la ruta real termina en
    /ws_reuse_supplement/), así que cambiar de directo NO abre un socket nuevo:
    por eso room_id puede cambiar sin que la sesión se cierre.
    """

    def __init__(self, unique_id: str, room_id: Optional[str] = None):
        self.unique_id = normalizar_id(unique_id)
        self.room_id = str(room_id) if room_id else None
        self.estado = "abierto"
        self.abierta_en = time.time()
        self.tramas_recibidas = 0
        self.huecos = 0
        self.host_ws: Optional[str] = None
        self._seq_esperado: Optional[int] = None
        self.cola = ColaTramas()

    def anotar_seq(self, seq: Optional[int]) -> bool:
        """Registra el número de secuencia. False si hubo hueco (no es un error)."""
        if seq is None:
            return True
        continuo = self._seq_esperado is None or seq == self._seq_esperado
        if not continuo:
            self.huecos += 1
            logger.warning(
                "Hueco en la secuencia de tramas de @%s: esperaba %s y llegó %s "
                "(se sigue igual, %s huecos en esta sesión)",
                self.unique_id or "(comodín)",
                self._seq_esperado,
                seq,
                self.huecos,
            )
        self._seq_esperado = seq + 1
        return continuo

    def publicar(self, tramas) -> None:
        for trama in tramas:
            self.cola.publicar(trama)
        self.tramas_recibidas += len(tramas)

    def cerrar(self) -> None:
        self.estado = "cerrado"
        self.cola.cerrar()

    def reabrir(self, room_id: Optional[str] = None) -> None:
        """Cola nueva al reabrir: la anterior ya entregó su centinela de cierre."""
        if self.estado == "cerrado":
            self.cola = ColaTramas()
            self._seq_esperado = None
        self.estado = "abierto"
        self.abierta_en = time.time()
        if room_id:
            self.room_id = str(room_id)

    @property
    def abierta(self) -> bool:
        return self.estado == "abierto"


class AlmacenSesiones:
    """Las sesiones de navegador vivas, por usuario, con espera bloqueante."""

    def __init__(self):
        self._lock = threading.Lock()
        self._por_usuario: dict[str, SesionNavegador] = {}
        self._evento = threading.Event()

    def _obtener_o_crear(self, unique_id: str, room_id=None) -> SesionNavegador:
        clave = normalizar_id(unique_id)
        sesion = self._por_usuario.get(clave)
        if sesion is None:
            sesion = SesionNavegador(clave, room_id)
            self._por_usuario[clave] = sesion
        elif room_id:
            sesion.room_id = str(room_id)
        return sesion

    def abrir(self, unique_id: str, room_id=None, host_ws=None) -> SesionNavegador:
        with self._lock:
            sesion = self._obtener_o_crear(unique_id, room_id)
            sesion.reabrir(room_id)
            if host_ws:
                sesion.host_ws = host_ws
        self._evento.set()
        logger.info(
            "El navegador abrió el directo de @%s (sala %s, host %s)",
            sesion.unique_id or "(comodín)",
            sesion.room_id or "desconocida",
            sesion.host_ws or "sin informar",
        )
        return sesion

    def cerrar(self, unique_id: str) -> Optional[SesionNavegador]:
        with self._lock:
            sesion = self._por_usuario.get(normalizar_id(unique_id))
        if sesion is None:
            return None
        sesion.cerrar()
        logger.info(
            "El navegador cerró el directo de @%s tras %s tramas",
            sesion.unique_id or "(comodín)",
            sesion.tramas_recibidas,
        )
        return sesion

    def agregar_tramas(
        self, unique_id: str, room_id, seq: Optional[int], tramas
    ) -> SesionNavegador:
        """Encola tramas. Abre la sesión sola si la extensión no avisó por /sesion."""
        with self._lock:
            sesion = self._obtener_o_crear(unique_id, room_id)
            if not sesion.abierta:
                sesion.reabrir(room_id)
        sesion.anotar_seq(seq)
        sesion.publicar(tramas)
        self._evento.set()
        return sesion

    def obtener(self, unique_id: str) -> Optional[SesionNavegador]:
        """La sesión de ese usuario; con unique_id vacío, cualquiera abierta."""
        clave = normalizar_id(unique_id)
        with self._lock:
            if clave:
                sesion = self._por_usuario.get(clave)
                if sesion is not None:
                    return sesion
                # Comodín del lado de la extensión: puede no saber el nombre del
                # dueño del directo y mandar las tramas sin él.
                return self._por_usuario.get("")
            for sesion in self._por_usuario.values():
                if sesion.abierta:
                    return sesion
            return None

    def esperar(self, unique_id: str, timeout: float) -> Optional[SesionNavegador]:
        """Bloquea hasta que haya una sesión abierta para ese usuario."""
        limite = time.time() + timeout
        while True:
            sesion = self.obtener(unique_id)
            if sesion is not None and sesion.abierta:
                return sesion
            if time.time() >= limite:
                return None
            self._evento.wait(timeout=1.0)
            self._evento.clear()

    def resumen(self):
        """Forma, no secretos: lo que puede enseñarse en una consola o en la UI."""
        with self._lock:
            sesiones = list(self._por_usuario.values())
        return [
            {
                "unique_id": s.unique_id or "(comodín)",
                "room_id": s.room_id,
                "estado": s.estado,
                "tramas": s.tramas_recibidas,
                "huecos": s.huecos,
                "en_cola": s.cola.pendientes(),
                "descartadas": s.cola.descartadas,
            }
            for s in sesiones
        ]


# ---------------------------------------------------------------------------
# El servidor
# ---------------------------------------------------------------------------


class _ErrorPeticion(Exception):
    """Payload que no cumple el contrato. Se responde 400 con el motivo."""


def _decodificar_tramas(valor):
    """Las tramas base64 del payload, ya en binario. Lanza si algo no cuadra."""
    if not isinstance(valor, list):
        raise _ErrorPeticion("'tramas' tiene que ser una lista")
    tramas = []
    for i, elemento in enumerate(valor):
        if not isinstance(elemento, str):
            raise _ErrorPeticion(f"la trama {i} no es una cadena base64")
        try:
            # validate=True para que un alfabeto raro falle en vez de colarse
            # como bytes truncados en silencio.
            tramas.append(base64.b64decode(elemento, validate=True))
        except (binascii.Error, ValueError) as e:
            raise _ErrorPeticion(f"la trama {i} no es base64 válido: {e}") from e
    return tramas


def _leer_seq(valor) -> Optional[int]:
    """El número de secuencia, tolerando que venga como texto."""
    if valor is None:
        return None
    if isinstance(valor, bool):  # bool es int en Python, y aquí no significa nada
        raise _ErrorPeticion("'seq' tiene que ser un entero")
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor.strip())
    raise _ErrorPeticion("'seq' tiene que ser un entero")


class _Handler(BaseHTTPRequestHandler):
    almacen: AlmacenCapturas = None  # se asignan al crear el servidor
    sesiones: AlmacenSesiones = None

    # El navegador manda desde el service worker de la extensión (una página de
    # tiktok.com no puede llamar a 127.0.0.1: Chrome la corta antes de emitirla).
    # Aun así se responde con CORS permisivo y con la cabecera de red privada,
    # que es la que Chrome exige para dejar salir una petición hacia loopback.
    def _cabeceras_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _responder(self, codigo: int, cuerpo: dict) -> None:
        datos = json.dumps(cuerpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self._cabeceras_cors()
        self.end_headers()
        self.wfile.write(datos)

    def _cuerpo_json(self) -> dict:
        largo = int(self.headers.get("Content-Length", 0) or 0)
        try:
            datos = json.loads(self.rfile.read(largo) or b"{}")
        except json.JSONDecodeError as e:
            raise _ErrorPeticion(f"el cuerpo no es JSON válido: {e}") from e
        if not isinstance(datos, dict):
            raise _ErrorPeticion("el cuerpo tiene que ser un objeto JSON")
        return datos

    def do_OPTIONS(self):  # noqa: N802 (lo exige la clase base)
        self.send_response(204)
        self.send_header("Access-Control-Max-Age", "86400")
        self._cabeceras_cors()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        ruta = self.path.split("?", 1)[0].rstrip("/")
        if ruta == "/salud":
            self._responder(200, {"ok": True, "version": VERSION_CONTRATO})
        elif ruta == "/estado":
            # Fuera del contrato con la extensión: es para mirar desde una
            # consola qué está llegando. Solo forma, nunca valores.
            self._responder(200, {"ok": True, "sesiones": self.sesiones.resumen()})
        else:
            self._responder(404, {"error": "ruta desconocida"})

    def do_POST(self):  # noqa: N802
        ruta = self.path.split("?", 1)[0].rstrip("/")
        rutas = {
            "/captura": self._post_captura,
            "/sesion": self._post_sesion,
            "/tramas": self._post_tramas,
        }
        manejador = rutas.get(ruta)
        if manejador is None:
            self._responder(404, {"error": "ruta desconocida"})
            return
        try:
            manejador(self._cuerpo_json())
        except _ErrorPeticion as e:
            self._responder(400, {"error": str(e)})
        except Exception as e:
            logger.exception("Error procesando %s del interceptor", ruta)
            self._responder(400, {"error": str(e)})

    def _post_captura(self, datos: dict) -> None:
        captura = Captura(datos)
        if not captura.es_valida():
            raise _ErrorPeticion("ws_url ausente o no es de TikTok")
        self.almacen.guardar(captura)
        self._responder(200, {"ok": True})

    def _post_sesion(self, datos: dict) -> None:
        estado = str(datos.get("estado", "")).strip().lower()
        if estado not in ("abierto", "cerrado"):
            raise _ErrorPeticion("'estado' tiene que ser 'abierto' o 'cerrado'")
        unique_id = datos.get("unique_id", "")
        if estado == "abierto":
            # De la ws_url solo se mira el host, para poder distinguir el
            # webcast de la mensajería privada (im-ws-sg.tiktok.com), que es
            # otro websocket y no interesa.
            host = None
            if datos.get("ws_url"):
                host = urlparse(str(datos["ws_url"])).hostname
            self.sesiones.abrir(unique_id, datos.get("room_id"), host_ws=host)
        else:
            self.sesiones.cerrar(unique_id)
        self._responder(200, {"ok": True})

    def _post_tramas(self, datos: dict) -> None:
        if "tramas" not in datos:
            raise _ErrorPeticion("falta 'tramas'")
        tramas = _decodificar_tramas(datos["tramas"])
        seq = _leer_seq(datos.get("seq"))
        self.sesiones.agregar_tramas(
            datos.get("unique_id", ""), datos.get("room_id"), seq, tramas
        )
        self._responder(200, {"ok": True, "recibidas": len(tramas)})

    def log_message(self, *args):
        # Silencia el log a stderr del servidor base; ya usamos logging.
        pass


class ServidorInterceptor:
    """Servidor local al que el interceptor manda lo que ve. Solo 127.0.0.1."""

    def __init__(self, puerto: int = PUERTO_POR_DEFECTO):
        self.almacen = AlmacenCapturas()
        self.sesiones = AlmacenSesiones()
        handler = type(
            "Handler",
            (_Handler,),
            {"almacen": self.almacen, "sesiones": self.sesiones},
        )

        # allow_reuse_address desactivado a propósito: en Windows, con el reuso
        # activo (el valor por defecto de http.server) varios procesos pueden
        # quedar pegados al mismo puerto a la vez y el SO reparte las peticiones
        # entre ellos de forma impredecible. Sin reuso, un segundo arranque
        # falla claro ("puerto en uso") en vez de crear un listener fantasma.
        class _Servidor(ThreadingHTTPServer):
            allow_reuse_address = False
            daemon_threads = True

        self._httpd = _Servidor(("127.0.0.1", puerto), handler)
        self.puerto = self._httpd.server_address[1]
        self._hilo: Optional[threading.Thread] = None

    def iniciar(self) -> None:
        if self._hilo and self._hilo.is_alive():
            return
        self._hilo = threading.Thread(
            target=self._httpd.serve_forever, name="tiktok-interceptor", daemon=True
        )
        self._hilo.start()
        logger.info("Interceptor escuchando en http://127.0.0.1:%s", self.puerto)

    def detener(self) -> None:
        try:
            self._httpd.shutdown()
            self._httpd.server_close()
        except Exception:
            logger.debug("Cierre del interceptor con incidencia menor", exc_info=True)


# Un único servidor por proceso: el puerto es uno solo y el usuario puede
# conectar y desconectar varios chats seguidos sin que haga falta reabrirlo.
_servidor_compartido: Optional[ServidorInterceptor] = None
_lock_compartido = threading.Lock()


def servidor_compartido(puerto: int = PUERTO_POR_DEFECTO) -> ServidorInterceptor:
    """El servidor del proceso, arrancándolo la primera vez que se pide."""
    global _servidor_compartido
    with _lock_compartido:
        if _servidor_compartido is None:
            _servidor_compartido = ServidorInterceptor(puerto=puerto)
            _servidor_compartido.iniciar()
        return _servidor_compartido


def detener_servidor_compartido() -> None:
    """Para el servidor del proceso, si lo hay (al cerrar la app o en tests)."""
    global _servidor_compartido
    with _lock_compartido:
        if _servidor_compartido is not None:
            _servidor_compartido.detener()
            _servidor_compartido = None


# ---------------------------------------------------------------------------
# Ruta A: inyectar la URL firmada en la librería
# ---------------------------------------------------------------------------


def _fetch_result_desde_captura(captura: Captura) -> ProtoMessageFetchResult:
    """Construye el objeto que espera TikTokLive para el estado inicial.

    push_server/route_params quedan de relleno: la URL de verdad se inyecta como
    `uri` (ver instalar), y el generador de conexión la usa verbatim. Lo que sí
    importa aquí es el cursor y una lista de mensajes vacía para arrancar.
    """
    return ProtoMessageFetchResult(
        messages=[],
        cursor=captura.cursor,
        route_params={},
        push_server=captura.ws_url,
        history_comment_cursor="0",
    )


def instalar(client, almacen: AlmacenCapturas, *, timeout: float = ESPERA_CAPTURA_S):
    """Ruta A: sustituye el firmador del cliente por la URL que vio el navegador.

    Deja `client.web.fetch_signed_websocket` de forma que, en vez de llamar a
    EulerStream, espere la captura del navegador y la use. Es el mismo patrón de
    sustitución que servicios/tiktok.py ya emplea con _parse_webcast_response_message.

    Frágil por diseño: la URL firmada caduca a los 30 segundos y el navegador ya
    la consumió (ver el comentario de __aiter__ en ws_connect.py de la librería).
    La ruta buena es la B, en servicios/tiktok_espejo.py.
    """
    unique_id = normalizar_id(getattr(client, "unique_id", ""))

    async def fetch_interceptado(
        platform=None, *args, **kwargs
    ) -> ProtoMessageFetchResult:
        import asyncio

        logger.info(
            "Esperando una captura del interceptor para @%s (hasta %ss)...",
            unique_id,
            int(timeout),
        )
        # El almacén bloquea con hilos; se saca del hilo del bucle asyncio para
        # no congelarlo.
        captura = await asyncio.to_thread(almacen.esperar, unique_id, timeout)
        if captura is None:
            raise TimeoutError(
                "No llegó ninguna captura del interceptor. ¿Está el directo "
                "abierto en el navegador con la extensión puesta?"
            )

        # 1) cookies capturadas -> cookies del cliente web (el websocket las lee de ahí)
        for nombre, valor in captura.cookies.items():
            try:
                client.web.cookies.set(nombre, valor, ".tiktok.com")
            except Exception:
                logger.debug("No se pudo fijar la cookie %r", nombre, exc_info=True)

        # 2) URL capturada -> uri verbatim del websocket (salta build_webcast_uri)
        try:
            client._ws._ws_kwargs["uri"] = captura.ws_url
        except Exception:
            logger.exception("No se pudo inyectar el uri capturado en el websocket")

        # 3) estado inicial para la librería
        return _fetch_result_desde_captura(captura)

    client.web.fetch_signed_websocket = fetch_interceptado
    logger.info("Firmador reemplazado por el interceptor local para @%s", unique_id)


def esta_escuchando(puerto: int = PUERTO_POR_DEFECTO) -> bool:
    """True si hay un ServidorInterceptor vivo en ese puerto (útil para la UI)."""
    try:
        r = httpx.get(f"http://127.0.0.1:{puerto}/salud", timeout=2)
        return r.status_code == 200 and r.json().get("ok") is True
    except Exception:
        return False
