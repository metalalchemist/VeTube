"""Pruebas de la ruta B: las tramas del navegador convertidas en eventos.

Las tramas se fabrican con el protobuf de la propia librería, así que ninguna
prueba habla con TikTok ni guarda capturas reales (que llevan firma dentro).
Los generadores se recorren con asyncio.run para no depender de la configuración
de pytest-asyncio.
"""

import asyncio
import inspect
import re

from TikTokLive.client.ws.ws_client import WebcastWSClient
from TikTokLive.proto import ProtoMessageFetchResult

from servicios.tiktok_espejo import WebsocketEspejo, decodificar_trama, instalar_espejo
from servicios.tiktok_interceptor import AlmacenSesiones
from tests.tramas_sinteticas import trama, trama_hb, trama_msg

# --- decodificar una trama ----------------------------------------------------


def test_trama_msg_sin_comprimir():
    resultado = decodificar_trama(trama_msg("WebcastChatMessage", compress_type="none"))

    assert [m.method for m in resultado.messages] == ["WebcastChatMessage"]
    assert resultado.need_ack is True


def test_trama_msg_en_gzip():
    # En un directo real llegan las dos: compress_type 'none' y 'gzip'.
    resultado = decodificar_trama(
        trama_msg("WebcastMemberMessage", "WebcastLikeMessage", compress_type="gzip")
    )

    assert [m.method for m in resultado.messages] == [
        "WebcastMemberMessage",
        "WebcastLikeMessage",
    ]


def test_trama_msg_sin_cabecera_de_compresion():
    resultado = decodificar_trama(trama_msg("WebcastChatMessage", compress_type=None))

    assert len(resultado.messages) == 1


def test_trama_msg_sin_mensajes_no_es_un_error():
    # Las primeras tramas de una sala llegan así; tirarlas como si fueran basura
    # sería confundir "no hay nada que leer" con "algo se rompió".
    resultado = decodificar_trama(trama_msg())

    assert isinstance(resultado, ProtoMessageFetchResult)
    assert resultado.messages == []


def test_trama_de_latido_se_ignora():
    assert decodificar_trama(trama_hb()) is None


def test_trama_de_ack_se_ignora():
    assert decodificar_trama(trama(b"", payload_type="ack")) is None


def test_trama_vacia_se_ignora():
    assert decodificar_trama(b"") is None


def test_trama_rota_no_revienta():
    # Una trama rota no vale un corte de conexión en mitad de un directo.
    assert decodificar_trama(b"\xff" * 40) is None


def test_las_tramas_del_navegador_no_vuelven_a_anunciar_la_entrada():
    # is_first solo lo trae el estado inicial: si se colara en una trama, VeTube
    # volvería a decir "Ingresando al chat" por el lector de pantalla.
    marcada = bytes(ProtoMessageFetchResult(cursor="1", is_first=True))

    resultado = decodificar_trama(trama(marcada))

    assert resultado.is_first is False


# --- el espejo ----------------------------------------------------------------


def _estado_inicial():
    return ProtoMessageFetchResult(messages=[], cursor="0", is_first=True)


def _recorrer(espejo, inicial):
    """Consume el generador entero. Termina cuando la sesión ya está cerrada."""

    async def corrida():
        return [
            r
            async for r in espejo.connect(
                room_id=7563, initial_webcast_response=inicial
            )
        ]

    return asyncio.run(corrida())


def test_el_espejo_entrega_el_estado_inicial_y_luego_lo_del_navegador():
    sesiones = AlmacenSesiones()
    sesion = sesiones.abrir("pia", room_id="7563")
    sesiones.agregar_tramas(
        "pia",
        "7563",
        1,
        [trama_msg("WebcastChatMessage"), trama_hb(), trama_msg("WebcastGiftMessage")],
    )
    sesiones.cerrar("pia")  # el centinela hace terminar el generador
    espejo = WebsocketEspejo(sesiones, "pia")
    espejo.sesion = sesion
    inicial = _estado_inicial()

    salidas = _recorrer(espejo, inicial)

    assert salidas[0] is inicial
    # El latido queda por el camino: no trae eventos.
    assert [m.method for r in salidas[1:] for m in r.messages] == [
        "WebcastChatMessage",
        "WebcastGiftMessage",
    ]
    assert espejo.tramas_vistas == 3
    assert espejo.tramas_con_eventos == 2
    assert espejo.connected is False


def test_el_espejo_respeta_la_casilla_de_mensajes_anteriores():
    sesiones = AlmacenSesiones()
    sesion = sesiones.abrir("pia")
    sesiones.cerrar("pia")
    espejo = WebsocketEspejo(sesiones, "pia")
    espejo.sesion = sesion
    inicial = ProtoMessageFetchResult(cursor="0", is_first=True)
    inicial.messages = list(decodificar_trama(trama_msg("WebcastChatMessage")).messages)

    async def corrida():
        return [
            r
            async for r in espejo.connect(
                initial_webcast_response=inicial, process_connect_events=False
            )
        ]

    salidas = asyncio.run(corrida())

    assert salidas[0].messages == []


def test_el_espejo_termina_cuando_el_navegador_cierra():
    sesiones = AlmacenSesiones()
    sesion = sesiones.abrir("pia")
    espejo = WebsocketEspejo(sesiones, "pia")
    espejo.sesion = sesion

    async def corrida():
        salidas = []
        async for respuesta in espejo.connect(initial_webcast_response=_estado_inicial()):
            salidas.append(respuesta)
            # El usuario cierra la pestaña del directo justo después de entrar.
            sesiones.cerrar("pia")
        return salidas

    assert len(asyncio.run(corrida())) == 1


def test_detener_el_chat_corta_el_espejo_en_el_acto():
    sesiones = AlmacenSesiones()
    sesion = sesiones.abrir("pia")
    espejo = WebsocketEspejo(sesiones, "pia")
    espejo.sesion = sesion

    async def corrida():
        await espejo.disconnect()
        return [
            r async for r in espejo.connect(initial_webcast_response=_estado_inicial())
        ]

    # Solo el estado inicial: no se queda esperando tramas que ya nadie quiere.
    assert len(asyncio.run(corrida())) == 1
    assert espejo.connected is False


def test_el_espejo_se_rinde_si_el_navegador_nunca_aparece():
    espejo = WebsocketEspejo(AlmacenSesiones(), "pia", timeout=0.2)

    async def corrida():
        async for _ in espejo.connect(initial_webcast_response=_estado_inicial()):
            pass

    try:
        asyncio.run(corrida())
    except TimeoutError as e:
        assert "navegador" in str(e)
    else:
        raise AssertionError("tenía que rendirse")


def test_el_espejo_no_puede_mandar_nada():
    # El navegador es quien manda acks y latidos por su propio socket. Si el
    # espejo tuviera con qué mandar, algún día alguien lo usaría.
    for prohibido in ("send", "send_ack", "switch_rooms", "restart_ping_loop"):
        assert not hasattr(WebsocketEspejo, prohibido)


def test_el_espejo_cubre_todo_lo_que_la_libreria_le_pide():
    """Canario: si TikTokLive empieza a pedirle algo más a client._ws, se nota acá."""
    fuente = inspect.getsource(
        __import__("TikTokLive.client.client", fromlist=["client"])
    )
    usados = set(re.findall(r"self\._ws\.(\w+)", fuente))

    assert usados  # si esto falla, cambió el nombre del atributo en la librería
    assert usados <= set(dir(WebsocketEspejo)), usados - set(dir(WebsocketEspejo))
    # Y lo que se cubre es lo mismo que ofrece el cliente de verdad.
    assert usados <= set(dir(WebcastWSClient))


# --- instalar el espejo en un cliente -----------------------------------------


class _WebFalso:
    def __init__(self):
        self.llamadas = []

    async def fetch_signed_websocket(self, platform=None):
        self.llamadas.append("firma")
        raise AssertionError("el firmador externo no debería llamarse nunca")

    async def fetch_room_id_from_html(self, unique_id=None):
        self.llamadas.append("raspado")
        return "999"

    async def fetch_is_live(self, room_id=None, unique_id=None):
        self.llamadas.append("is_live")
        return False


class _ClienteFalso:
    def __init__(self):
        self.unique_id = "@Pia"
        self._ws = object()
        self.web = _WebFalso()


def test_instalar_el_espejo_cambia_los_cuatro_puntos():
    cliente = _ClienteFalso()
    sesiones = AlmacenSesiones()
    sesiones.abrir("pia", room_id="7563")

    espejo = instalar_espejo(cliente, sesiones, timeout=1)

    assert cliente._ws is espejo
    assert cliente.web.fetch_signed_websocket.__name__ == "fetch_desde_navegador"
    assert asyncio.run(cliente.web.fetch_room_id_from_html("pia")) == "7563"
    assert asyncio.run(cliente.web.fetch_is_live(unique_id="pia")) is True
    # Nada de eso pasó por la red.
    assert cliente.web.llamadas == []


def test_sin_sesion_del_navegador_se_vuelve_a_lo_de_antes():
    cliente = _ClienteFalso()

    instalar_espejo(cliente, AlmacenSesiones(), timeout=1)

    assert asyncio.run(cliente.web.fetch_room_id_from_html("pia")) == "999"
    assert asyncio.run(cliente.web.fetch_is_live(unique_id="pia")) is False
    assert cliente.web.llamadas == ["raspado", "is_live"]


def test_el_estado_inicial_del_espejo_anuncia_la_entrada_al_chat():
    cliente = _ClienteFalso()
    sesiones = AlmacenSesiones()
    sesion = sesiones.abrir("pia", room_id="7563")
    avisos = []

    espejo = instalar_espejo(cliente, sesiones, timeout=1, avisar=avisos.append)
    inicial = asyncio.run(cliente.web.fetch_signed_websocket())

    # is_first es lo que hace que TikTokLive emita el ConnectEvent con el que
    # VeTube dice "Ingresando al chat".
    assert inicial.is_first is True
    assert inicial.messages == []
    # Y no lleva URL ninguna: el espejo no conecta a nada.
    assert inicial.push_server == ""
    assert espejo.sesion is sesion
    assert avisos  # al usuario se le avisa que hay que abrir el directo
