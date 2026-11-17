"""Pruebas del conversor de divisas de las donaciones (exchange)."""

import asyncio
import json
import os
import time

import pytest

import exchange as exchange_module
from exchange import Exchange

PRINCIPAL = "open.er-api.com"
RESPALDO = "allratestoday.com"


class RespuestaFalsa:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class ClienteFalso:
    """Sustituye al cliente httpx compartido: responde según la URL pedida."""

    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.peticiones = []

    async def get(self, url, **kwargs):
        self.peticiones.append((url, kwargs))
        for fragmento, respuesta in self.respuestas.items():
            if fragmento in url:
                if isinstance(respuesta, Exception):
                    raise respuesta
                return respuesta
        raise AssertionError(f"petición inesperada: {url}")


def tabla(base, **tasas):
    """Una respuesta con la forma de las dos fuentes: la base vale 1."""
    return {"result": "success", "base_code": base, "rates": {base: 1, **tasas}}


@pytest.fixture
def pendientes(monkeypatch):
    """Las descargas no salen a la red: quedan anotadas aquí, en orden."""
    corrutinas = []
    monkeypatch.setattr(
        exchange_module.network_manager,
        "execute",
        lambda coro, callback=None: corrutinas.append(coro),
    )
    yield corrutinas
    for coro in corrutinas:
        coro.close()


@pytest.fixture
def conversor(tmp_path, monkeypatch, pendientes):
    """Un Exchange recién nacido, como al arrancar VeTube: sin divisa elegida."""
    monkeypatch.chdir(tmp_path)  # divisas/ es relativa al directorio actual
    monkeypatch.setattr(exchange_module.data_store, "divisa", "Por defecto")
    return Exchange()


def descargar(pendientes, monkeypatch, respuestas):
    """Lanza la descarga pendiente más antigua contra un cliente falso."""
    cliente = ClienteFalso(respuestas)
    monkeypatch.setattr(exchange_module.network_manager, "client", cliente)
    asyncio.run(pendientes.pop(0))
    return cliente


def escribir_cache(base, data, antiguedad=0):
    ruta = os.path.join("divisas", f"{base}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f)
    if antiguedad:
        momento = time.time() - antiguedad
        os.utime(ruta, (momento, momento))
    return ruta


def test_sin_divisa_elegida_no_convierte_ni_descarga(conversor, pendientes):
    assert conversor.base_currency is None
    assert conversor.convert(10, "USD") is None
    assert conversor.from_bits(500) is None
    assert pendientes == []


def test_elegir_divisa_despues_de_arrancar_carga_las_tasas(
    conversor, pendientes, monkeypatch
):
    """La regresión: el objeto nace sin divisa y nunca llegaba a tener tasas."""
    conversor.set_base_currency("USD")
    assert len(pendientes) == 1

    descargar(
        pendientes,
        monkeypatch,
        {PRINCIPAL: RespuestaFalsa(data=tabla("USD", COP=4000, EUR=0.8))},
    )

    assert conversor.convert(4000, "COP") == (1.0, "USD")
    assert conversor.convert(8, "eur") == (10.0, "USD")
    with open(os.path.join("divisas", "USD.json"), encoding="utf-8") as f:
        assert json.load(f)["rates"]["COP"] == 4000


def test_mientras_no_llegan_las_tasas_no_se_inventa_el_importe(conversor):
    conversor.set_base_currency("EUR")

    assert conversor.convert(4000, "COP") is None
    assert conversor.from_bits(500) is None
    # Misma divisa: no hace falta ninguna tasa.
    assert conversor.convert(5.0, "EUR") == (5.0, "EUR")


def test_divisa_sin_tasa_devuelve_none(conversor, pendientes, monkeypatch):
    conversor.set_base_currency("USD")
    descargar(
        pendientes, monkeypatch, {PRINCIPAL: RespuestaFalsa(data=tabla("USD", EUR=0.8))}
    )

    assert conversor.convert(500, "ARS") is None


def test_divisas_de_origen_raras(conversor, pendientes, monkeypatch):
    """chat-downloader da None si no entiende el importe; pytchat deja el
    símbolo tal cual, con su espacio duro («ARS\\xa0»)."""
    conversor.set_base_currency("USD")
    descargar(
        pendientes,
        monkeypatch,
        {PRINCIPAL: RespuestaFalsa(data=tabla("USD", ARS=1000))},
    )

    assert conversor.convert(500, None) is None
    assert conversor.convert(500, "") is None
    assert conversor.convert(500, "ARS\xa0") == (0.5, "USD")


def test_bits_y_diamantes_valen_un_centavo_de_dolar(conversor, pendientes, monkeypatch):
    conversor.set_base_currency("EUR")
    descargar(
        pendientes,
        monkeypatch,
        {PRINCIPAL: RespuestaFalsa(data=tabla("EUR", USD=1.25))},
    )

    assert conversor.from_bits(500) == (4.0, "EUR")
    assert conversor.from_diamonds(250) == (2.0, "EUR")


def test_con_dolares_los_bits_no_necesitan_tasas(conversor):
    conversor.set_base_currency("USD")

    assert conversor.from_bits(500) == (5.0, "USD")


def test_cache_reciente_evita_la_descarga(conversor, pendientes):
    escribir_cache("USD", tabla("USD", COP=4000))

    conversor.set_base_currency("USD")

    assert pendientes == []
    assert conversor.convert(4000, "COP") == (1.0, "USD")


def test_cache_de_mas_de_un_dia_se_borra_y_se_descarga(conversor, pendientes):
    ruta = escribir_cache("USD", tabla("USD", COP=4000), antiguedad=2 * 86400)

    conversor.set_base_currency("USD")

    assert not os.path.exists(ruta)
    assert len(pendientes) == 1
    assert conversor.convert(4000, "COP") is None


@pytest.mark.parametrize(
    "contenido",
    [
        tabla("USD", COP=4000),  # tasas de otra base
        {"result": "error", "error-type": "unsupported-code"},
        ["no", "es", "un", "objeto"],
    ],
)
def test_cache_que_no_es_de_la_divisa_pedida_no_vale(conversor, pendientes, contenido):
    escribir_cache("EUR", contenido)

    conversor.set_base_currency("EUR")

    assert len(pendientes) == 1
    assert conversor.convert(4000, "COP") is None


def test_cache_corrupta_no_vale(conversor, pendientes):
    with open(os.path.join("divisas", "EUR.json"), "w", encoding="utf-8") as f:
        f.write("{a medias")

    conversor.set_base_currency("EUR")

    assert len(pendientes) == 1


def test_si_falla_la_principal_se_usa_la_de_respaldo(
    conversor, pendientes, monkeypatch
):
    conversor.set_base_currency("USD")

    cliente = descargar(
        pendientes,
        monkeypatch,
        {
            PRINCIPAL: RespuestaFalsa(status_code=503),
            RESPALDO: RespuestaFalsa(data=tabla("USD", EUR=0.8)),
        },
    )

    assert len(cliente.peticiones) == 2
    assert PRINCIPAL in cliente.peticiones[0][0]
    assert RESPALDO in cliente.peticiones[1][0]
    assert conversor.convert(8, "EUR") == (10.0, "USD")


def test_si_la_principal_no_contesta_se_usa_la_de_respaldo(
    conversor, pendientes, monkeypatch
):
    conversor.set_base_currency("USD")

    cliente = descargar(
        pendientes,
        monkeypatch,
        {
            PRINCIPAL: TimeoutError("sin respuesta"),
            RESPALDO: RespuestaFalsa(data=tabla("USD", EUR=0.8)),
        },
    )

    assert conversor.convert(8, "EUR") == (10.0, "USD")
    # El cliente compartido no tiene tiempo de espera: lo pone cada petición.
    assert all(kwargs.get("timeout") for _, kwargs in cliente.peticiones)


def test_respuesta_en_otra_base_se_rechaza(conversor, pendientes, monkeypatch):
    """Tasas relativas al dólar para quien pidió euros darían importes falsos."""
    conversor.set_base_currency("EUR")

    descargar(
        pendientes,
        monkeypatch,
        {
            PRINCIPAL: RespuestaFalsa(data=tabla("USD", EUR=0.8, COP=4000)),
            RESPALDO: RespuestaFalsa(data=tabla("EUR", USD=1.25)),
        },
    )

    assert conversor.convert(4000, "COP") is None
    assert conversor.convert(5, "USD") == (4.0, "EUR")


def test_tasas_que_no_son_numeros_positivos_se_descartan(
    conversor, pendientes, monkeypatch
):
    conversor.set_base_currency("EUR")

    descargar(
        pendientes,
        monkeypatch,
        {
            PRINCIPAL: RespuestaFalsa(
                data=tabla("EUR", USD="1.25", GBP=0, JPY=-3, MXN=20)
            )
        },
    )

    assert sorted(conversor.rates) == ["EUR", "MXN"]
    assert conversor.convert(5, "USD") is None
    assert conversor.convert(5, "GBP") is None


def test_si_no_responde_ninguna_fuente_no_convierte(conversor, pendientes, monkeypatch):
    conversor.set_base_currency("COP")

    descargar(
        pendientes,
        monkeypatch,
        {
            PRINCIPAL: RespuestaFalsa(data={"result": "error"}),
            RESPALDO: RespuestaFalsa(status_code=404),
        },
    )

    assert conversor.convert(5, "USD") is None
    assert os.listdir("divisas") == []


def test_cache_que_no_se_puede_escribir_no_pasa_al_respaldo(
    conversor, pendientes, monkeypatch
):
    """Las tasas de la principal ya están en memoria: perder la caché no es
    motivo para cambiarlas por las ~30 de la fuente de respaldo."""
    conversor.set_base_currency("USD")
    os.rmdir("divisas")

    cliente = descargar(
        pendientes,
        monkeypatch,
        {
            PRINCIPAL: RespuestaFalsa(data=tabla("USD", COP=4000)),
            RESPALDO: RespuestaFalsa(data=tabla("USD", EUR=0.8)),
        },
    )

    assert len(cliente.peticiones) == 1
    assert conversor.convert(4000, "COP") == (1.0, "USD")


def test_cambiar_de_divisa_durante_la_descarga(conversor, pendientes, monkeypatch):
    """Las tasas de la divisa anterior no se publican con la divisa nueva."""
    conversor.set_base_currency("USD")
    conversor.set_base_currency("EUR")
    assert len(pendientes) == 2

    descargar(
        pendientes,
        monkeypatch,
        {PRINCIPAL: RespuestaFalsa(data=tabla("USD", COP=4000))},
    )
    assert conversor.base_currency == "EUR"
    assert conversor.convert(4000, "COP") is None

    descargar(
        pendientes,
        monkeypatch,
        {PRINCIPAL: RespuestaFalsa(data=tabla("EUR", COP=5000))},
    )
    assert conversor.convert(5000, "COP") == (1.0, "EUR")


def test_volver_a_por_defecto_deja_de_convertir(conversor):
    escribir_cache("USD", tabla("USD", COP=4000))
    conversor.set_base_currency("USD")
    assert conversor.convert(4000, "COP") == (1.0, "USD")

    conversor.set_base_currency("Por defecto")

    assert conversor.base_currency is None
    assert conversor.convert(4000, "COP") is None
    assert conversor.convert(5, "USD") is None


def test_repetir_la_divisa_ya_cargada_no_descarga_otra_vez(conversor, pendientes):
    escribir_cache("USD", tabla("USD", COP=4000))
    conversor.set_base_currency("USD")
    os.remove(os.path.join("divisas", "USD.json"))

    conversor.set_base_currency("USD")

    assert pendientes == []
    assert conversor.convert(4000, "COP") == (1.0, "USD")


def test_repetir_la_divisa_sin_tasas_lo_vuelve_a_intentar(
    conversor, pendientes, monkeypatch
):
    conversor.set_base_currency("USD")
    descargar(pendientes, monkeypatch, {PRINCIPAL: OSError(), RESPALDO: OSError()})
    assert conversor.convert(4000, "COP") is None

    conversor.set_base_currency("USD")

    assert len(pendientes) == 1
