"""Fixtures compartidas por las pruebas del actualizador."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def sin_interfaz():
    """Las pruebas corren sin wx.App: los saltos al hilo de la interfaz se anotan
    en vez de ejecutarse, y el aviso de vuelta atrás no abre ningún diálogo.

    ``sin_interfaz.llamadas`` guarda las funciones pedidas, en orden, para que
    una prueba pueda comprobar qué diálogos se habrían mostrado.
    """
    from update import updater

    original = updater._en_interfaz
    llamadas = []

    def _anotar(funcion, esperar=False):
        llamadas.append(funcion)

    with (
        patch("update.updater._en_interfaz", side_effect=_anotar) as en_interfaz,
        patch("update.updater.rollback_notification") as aviso,
        # Las frases de cambio de fase salen por la voz del programa (setup):
        # aquí no hay motores; se anotan.
        patch("update.updater._anunciar") as anunciar,
        # El data.json del repo es el de la máquina de desarrollo: con las
        # donaciones desactivadas, _install_update abría un diálogo real.
        patch.dict("update.updater.config", {"donations": True}),
        # gettext lo instala la app como builtin; aquí no hay app.
        patch("update.updater._", lambda texto: texto, create=True),
    ):
        en_interfaz.llamadas = llamadas
        en_interfaz.aviso = aviso
        en_interfaz.anunciar = anunciar
        en_interfaz.original = original  # para probar la función real
        yield en_interfaz
