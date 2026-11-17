"""Regression tests for the main menu controller."""

from unittest.mock import MagicMock, patch

from controller.menus import main_menu_controller


def test_guardar_persists_selected_beta_channel_without_overwriting_it():
    """Saving settings keeps Beta in the complete configuration payload."""
    config = {
        "idioma": main_menu_controller.codes[0],
        "speed": 0,
        "tono": 0,
        "volume": 0,
        "sapi": False,
        "voz": 0,
        "update_channel": "stable",
    }
    dialog = MagicMock()
    dialog.choice_traducir.GetSelection.return_value = -1
    dialog.choice_language.GetSelection.return_value = 0
    dialog.choice_canal.GetSelection.return_value = 1
    dialog.check_backup.IsChecked.return_value = False
    dialog.choice_moneditas.GetSelection.return_value = 0
    controller = main_menu_controller.MainMenuController.__new__(
        main_menu_controller.MainMenuController
    )
    controller.config_dialog = dialog
    # El lector entero simulado: el real depende del motor de data.json, y
    # edgeSpeak no tiene list_voices (el test fallaba con Edge elegido).
    lector = MagicMock()
    lector._leer.list_voices.return_value = []

    with (
        patch.object(main_menu_controller.data_store, "config", config),
        patch.object(main_menu_controller.data_store, "divisa", "Por defecto"),
        patch.object(main_menu_controller.data_store, "motor_de_interfaz", return_value="edge"),
        patch.object(main_menu_controller.fajustes, "guardarConfiguracion") as save,
        patch.object(main_menu_controller.app_utilitys, "fijar_dispositivo_lector"),
        patch.object(main_menu_controller, "reader", lector),
        patch.object(main_menu_controller, "exchange"),
    ):
        controller.guardar()

    save.assert_called_once_with(config)
    assert save.call_args.args[0]["update_channel"] == "beta"


def _guardar_con_moneda(posicion, divisa_anterior="Por defecto"):
    """Acepta los ajustes con esa posición elegida en la lista de divisas.

    Devuelve la divisa que queda en data_store y el conversor (simulado).
    """
    config = {
        "idioma": main_menu_controller.codes[0],
        "speed": 0,
        "tono": 0,
        "volume": 0,
        "sapi": False,
        "voz": 0,
        "update_channel": "stable",
    }
    dialog = MagicMock()
    dialog.choice_traducir.GetSelection.return_value = -1
    dialog.choice_language.GetSelection.return_value = 0
    dialog.choice_canal.GetSelection.return_value = 0
    dialog.check_backup.IsChecked.return_value = False
    dialog.choice_moneditas.GetSelection.return_value = posicion
    controller = main_menu_controller.MainMenuController.__new__(
        main_menu_controller.MainMenuController
    )
    controller.config_dialog = dialog
    lector = MagicMock()
    lector._leer.list_voices.return_value = []

    with (
        patch.object(main_menu_controller.data_store, "config", config),
        patch.object(main_menu_controller.data_store, "divisa", divisa_anterior),
        patch.object(main_menu_controller.data_store, "motor_de_interfaz", return_value="edge"),
        patch.object(main_menu_controller.fajustes, "guardarConfiguracion"),
        patch.object(main_menu_controller.app_utilitys, "fijar_dispositivo_lector"),
        patch.object(main_menu_controller, "reader", lector),
        patch.object(main_menu_controller, "exchange") as conversor,
    ):
        controller.guardar()
        return main_menu_controller.data_store.divisa, conversor


def test_guardar_avisa_al_conversor_de_la_divisa_elegida():
    """El conversor nace sin divisa: si guardar() no le avisa, nunca carga tasas."""
    posicion = main_menu_controller.codigos_monedas.index("EUR")

    divisa, conversor = _guardar_con_moneda(posicion)

    assert divisa == "EUR"
    conversor.set_base_currency.assert_called_once_with("EUR")


def test_guardar_elige_la_divisa_por_posicion_no_por_nombre():
    """«Russian Ruble» está dos veces (RUR, retirado, y RUB): por nombre salía
    siempre el primero, que no tiene tasas."""
    from exchange.codes import CODES

    assert CODES["RUR"] == CODES["RUB"]
    posicion = main_menu_controller.codigos_monedas.index("RUB")

    divisa, conversor = _guardar_con_moneda(posicion)

    assert divisa == "RUB"
    conversor.set_base_currency.assert_called_once_with("RUB")


def test_guardar_con_por_defecto_deja_de_convertir():
    divisa, conversor = _guardar_con_moneda(0, divisa_anterior="EUR")

    assert divisa == "Por defecto"
    conversor.set_base_currency.assert_called_once_with("Por defecto")


def test_la_lista_de_divisas_y_sus_codigos_van_a_la_par():
    """guardar() y el panel de ajustes se fían de que los índices coincidan."""
    from globals.resources import codigos_monedas, monedas

    assert len(monedas) == len(codigos_monedas)
    assert codigos_monedas[0] == "Por defecto"
    assert all(
        texto.endswith(f", ({codigo})")
        for texto, codigo in zip(monedas[1:], codigos_monedas[1:])
    )
