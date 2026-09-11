"""Pruebas del servidor local del firmador: la mitad que recibe lo del navegador.

Ninguna toca la red de TikTok. Las tramas se fabrican con el protobuf de la
propia librería (ver tests/tramas_sinteticas.py) y el servidor se levanta en
127.0.0.1 con puerto 0, o sea el que el sistema tenga libre, para que las
pruebas no choquen con una VeTube abierta en el 8790.
"""

import logging

import httpx
import pytest

from servicios.tiktok_interceptor import (
    CENTINELA_CIERRE,
    SIN_TRAMA,
    VERSION_CONTRATO,
    AlmacenSesiones,
    Captura,
    ColaTramas,
    ServidorInterceptor,
    SesionNavegador,
)
from tests.tramas_sinteticas import en_base64, trama_hb, trama_msg


@pytest.fixture
def servidor():
    srv = ServidorInterceptor(puerto=0)
    srv.iniciar()
    yield srv
    srv.detener()


@pytest.fixture
def url(servidor):
    return f"http://127.0.0.1:{servidor.puerto}"


# --- el contrato con la extensión -------------------------------------------


def test_salud_publica_la_version_del_contrato(url):
    r = httpx.get(url + "/salud", timeout=5)

    assert r.status_code == 200
    assert r.json() == {"ok": True, "version": VERSION_CONTRATO}


def test_solo_escucha_en_loopback(servidor):
    assert servidor._httpd.server_address[0] == "127.0.0.1"


def test_options_responde_con_cors_y_red_privada(url):
    r = httpx.request("OPTIONS", url + "/tramas", timeout=5)

    assert r.status_code == 204
    assert r.headers["Access-Control-Allow-Origin"] == "*"
    assert "POST" in r.headers["Access-Control-Allow-Methods"]
    # Chrome exige esta cabecera para dejar salir una petición hacia loopback.
    assert r.headers["Access-Control-Allow-Private-Network"] == "true"


def test_ruta_desconocida_da_404(url):
    assert httpx.get(url + "/loquesea", timeout=5).status_code == 404
    assert httpx.post(url + "/loquesea", json={}, timeout=5).status_code == 404


# --- /tramas: la ruta B ------------------------------------------------------


def test_las_tramas_llegan_enteras_a_la_cola(url, servidor):
    unas = [trama_msg("WebcastChatMessage"), trama_hb()]

    r = httpx.post(
        url + "/tramas",
        json={
            "unique_id": "pia",
            "room_id": "7563",
            "seq": 1,
            "tramas": [en_base64(t) for t in unas],
        },
        timeout=5,
    )

    assert r.status_code == 200
    assert r.json() == {"ok": True, "recibidas": 2}
    sesion = servidor.sesiones.obtener("pia")
    assert sesion.room_id == "7563"
    assert sesion.tramas_recibidas == 2
    # El servidor no interpreta nada: los bytes salen tal y como entraron.
    assert sesion.cola.siguiente(0.1) == unas[0]
    assert sesion.cola.siguiente(0.1) == unas[1]


def test_el_arroba_y_las_mayusculas_no_hacen_otra_sesion(url, servidor):
    httpx.post(
        url + "/tramas",
        json={"unique_id": "@PiaPena", "seq": 1, "tramas": [en_base64(trama_hb())]},
        timeout=5,
    )

    assert servidor.sesiones.obtener("piapena") is not None


def test_tramas_sin_la_lista_se_rechazan(url):
    r = httpx.post(url + "/tramas", json={"unique_id": "pia", "seq": 1}, timeout=5)

    assert r.status_code == 400
    assert "tramas" in r.json()["error"]


def test_tramas_que_no_son_lista_se_rechazan(url):
    r = httpx.post(url + "/tramas", json={"tramas": "unatrama"}, timeout=5)

    assert r.status_code == 400


def test_trama_que_no_es_base64_se_rechaza(url, servidor):
    r = httpx.post(url + "/tramas", json={"tramas": ["no es base64!!"]}, timeout=5)

    assert r.status_code == 400
    assert "base64" in r.json()["error"]
    # Y no se encoló nada a medias.
    assert servidor.sesiones.obtener("") is None


def test_trama_que_no_es_texto_se_rechaza(url):
    r = httpx.post(url + "/tramas", json={"tramas": [1234]}, timeout=5)

    assert r.status_code == 400


def test_seq_que_no_es_entero_se_rechaza(url):
    r = httpx.post(url + "/tramas", json={"seq": "ayer", "tramas": []}, timeout=5)

    assert r.status_code == 400
    assert "seq" in r.json()["error"]


def test_cuerpo_que_no_es_json_se_rechaza(url):
    r = httpx.post(
        url + "/tramas",
        content=b"{esto no es json",
        headers={"Content-Type": "application/json"},
        timeout=5,
    )

    assert r.status_code == 400


def test_un_hueco_de_seq_no_corta_la_conexion(url, servidor):
    httpx.post(url + "/tramas", json={"unique_id": "pia", "seq": 1, "tramas": []}, timeout=5)

    r = httpx.post(
        url + "/tramas",
        json={"unique_id": "pia", "seq": 9, "tramas": [en_base64(trama_hb())]},
        timeout=5,
    )

    assert r.status_code == 200
    assert servidor.sesiones.obtener("pia").huecos == 1


def test_el_hueco_de_seq_queda_anotado_en_el_log(caplog):
    sesion = SesionNavegador("pia")
    sesion.anotar_seq(1)

    with caplog.at_level(logging.WARNING, logger="servicios.tiktok_interceptor"):
        continuo = sesion.anotar_seq(7)

    assert continuo is False
    assert "Hueco en la secuencia" in caplog.text
    # Tras el hueco se sigue contando desde donde llegó, no desde donde se esperaba.
    assert sesion.anotar_seq(8) is True


# --- /sesion -----------------------------------------------------------------


def test_abrir_y_cerrar_la_sesion(url, servidor):
    abrir = httpx.post(
        url + "/sesion",
        json={
            "unique_id": "pia",
            "room_id": "7563",
            "estado": "abierto",
            "ws_url": "wss://webcast-ws.tiktok.com/webcast/im/ws_proxy/"
            "ws_reuse_supplement/?room_id=7563",
        },
        timeout=5,
    )
    assert abrir.status_code == 200
    sesion = servidor.sesiones.obtener("pia")
    assert sesion.abierta
    # De la ws_url solo se guarda el host: la query lleva la firma.
    assert sesion.host_ws == "webcast-ws.tiktok.com"

    cerrar = httpx.post(
        url + "/sesion", json={"unique_id": "pia", "estado": "cerrado"}, timeout=5
    )

    assert cerrar.status_code == 200
    assert not sesion.abierta
    assert sesion.cola.cerrada


def test_estado_de_sesion_invalido_se_rechaza(url):
    r = httpx.post(url + "/sesion", json={"unique_id": "pia", "estado": "quizas"}, timeout=5)

    assert r.status_code == 400


def test_reabrir_una_sesion_cerrada_da_una_cola_nueva():
    sesiones = AlmacenSesiones()
    sesion = sesiones.abrir("pia", room_id="1")
    cola_vieja = sesion.cola
    sesiones.cerrar("pia")

    sesiones.abrir("pia", room_id="2")

    assert sesion.cola is not cola_vieja
    assert not sesion.cola.cerrada
    assert sesion.room_id == "2"


def test_esperar_devuelve_la_sesion_abierta_sin_nombre():
    sesiones = AlmacenSesiones()
    sesiones.abrir("pia")

    # unique_id vacío en la consulta es comodín: sirve cualquier sesión abierta.
    assert sesiones.esperar("", timeout=0.1) is not None


def test_esperar_se_rinde_si_el_navegador_no_aparece():
    assert AlmacenSesiones().esperar("pia", timeout=0.2) is None


# --- la cola que cruza de hilo -----------------------------------------------


def test_la_cola_avisa_cuando_no_llego_nada():
    assert ColaTramas().siguiente(0.05) is SIN_TRAMA


def test_la_cola_entrega_lo_pendiente_antes_del_centinela():
    cola = ColaTramas()
    cola.publicar(b"una")
    cola.cerrar()

    # Cerrar significa "el navegador se fue", no "tirá lo que quedaba".
    assert cola.siguiente(0.05) == b"una"
    assert cola.siguiente(0.05) is CENTINELA_CIERRE


def test_la_cola_llena_descarta_las_viejas():
    cola = ColaTramas(maximo=2)

    for i in range(4):
        cola.publicar(bytes([i]))

    # De un chat en vivo interesa lo último: se pierden la 0 y la 1.
    assert cola.siguiente(0.05) == b"\x02"
    assert cola.siguiente(0.05) == b"\x03"
    assert cola.descartadas == 2


# --- /captura: la ruta A ------------------------------------------------------

WS_FIRMADA = "wss://webcast-ws.tiktok.com/webcast/im/ws/?room_id=1&X-Bogus=x"


def test_captura_con_cookies_como_diccionario(url, servidor):
    r = httpx.post(
        url + "/captura",
        json={
            "unique_id": "@Pia",
            "room_id": "7563",
            "ws_url": WS_FIRMADA,
            "cookies": {"ttwid": "valor", "tt-target-idc": "otro"},
        },
        timeout=5,
    )

    assert r.status_code == 200
    captura = servidor.almacen.esperar("pia", timeout=1)
    assert sorted(captura.cookies) == ["tt-target-idc", "ttwid"]
    assert captura.room_id == "7563"


def test_captura_con_cookies_como_cabecera():
    captura = Captura(
        {
            "unique_id": "pia",
            "ws_url": WS_FIRMADA,
            "cookie_header": "ttwid=valor; tt-target-idc=otro ; roto",
        }
    )

    assert captura.cookies == {"ttwid": "valor", "tt-target-idc": "otro"}


def test_captura_sin_ws_url_se_rechaza(url):
    r = httpx.post(url + "/captura", json={"unique_id": "pia"}, timeout=5)

    assert r.status_code == 400


def test_captura_de_otro_sitio_se_rechaza(url):
    r = httpx.post(
        url + "/captura",
        json={"unique_id": "pia", "ws_url": "wss://ejemplo.com/ws"},
        timeout=5,
    )

    assert r.status_code == 400


# --- /estado: el modo de prueba manual ---------------------------------------


def test_estado_ensena_la_forma_y_ningun_secreto(url, servidor):
    httpx.post(
        url + "/sesion",
        json={"unique_id": "pia", "room_id": "7563", "estado": "abierto"},
        timeout=5,
    )
    httpx.post(
        url + "/tramas",
        json={"unique_id": "pia", "seq": 1, "tramas": [en_base64(trama_hb())]},
        timeout=5,
    )

    cuerpo = httpx.get(url + "/estado", timeout=5).json()

    assert cuerpo["sesiones"] == [
        {
            "unique_id": "pia",
            "room_id": "7563",
            "estado": "abierto",
            "tramas": 1,
            "huecos": 0,
            "en_cola": 1,
            "descartadas": 0,
        }
    ]
