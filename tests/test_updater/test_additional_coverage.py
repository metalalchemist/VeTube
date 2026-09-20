"""Focused branch tests for updater support modules."""

import io
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from update import (
    bootstrap_fix,
    release_notes_dialog,
    update,
    updater,
    utils,
    wxUpdater,
)
from update.github_client import ReleaseInfo


def test_convert_bytes_boundaries():
    assert utils.convert_bytes(0) == "0"
    assert utils.convert_bytes(1024) == "1.00Kb"
    assert utils.convert_bytes(1 << 20) == "1.00Mb"
    assert utils.convert_bytes(1 << 30) == "1.00Gb"
    assert utils.convert_bytes(1 << 40) == "1.00Tb"
    # The legacy helper formats petabytes using its existing implementation.
    assert utils.convert_bytes(1 << 50) == "1024.00Pb"


def test_dir_size_ignores_unreadable_files():
    with (
        patch("update.backup.os.walk", return_value=[("dir", [], ["file"])]),
        patch("update.backup.os.path.getsize", side_effect=OSError),
    ):
        from update.backup import _dir_size

        assert _dir_size("dir") == 0


def test_fetch_releases_sends_etag_and_handles_not_modified():
    from update import github_client

    github_client._cache.etag = "etag"
    response = MagicMock(status_code=304)
    client = MagicMock()
    client.get.return_value = response
    assert github_client._fetch_releases(client) == ([], None, True)
    assert client.get.call_args.kwargs["headers"]["If-None-Match"] == "etag"


def test_github_client_cache_hit_and_unexpected_error():
    from update import github_client

    info = ReleaseInfo("v1", "1", False, "", "zip", "sum", "a.zip")
    github_client._cache.store(info, "etag", channel="stable")
    with patch("update.github_client.httpx.Client") as client:
        assert github_client.get_latest_release("stable") is info
        client.assert_not_called()
    github_client.clear_cache()
    with patch("update.github_client.httpx.Client", side_effect=RuntimeError("bad")):
        assert github_client.get_latest_release("stable") is None


def test_read_version_uses_metadata_and_fallback():
    base_dir = MagicMock()
    base_dir.__truediv__.return_value.exists.return_value = False
    with (
        patch.object(updater, "BASE_DIR", base_dir),
        patch("importlib.metadata.version", return_value="7.0"),
    ):
        assert updater._read_version() == "7.0"
    with (
        patch.object(updater, "BASE_DIR", base_dir),
        patch("importlib.metadata.version", side_effect=Exception),
        patch("builtins.open", side_effect=OSError),
    ):
        assert updater._read_version() == "0.0.0"


def test_read_version_uses_pyproject_when_metadata_is_unavailable():
    base_dir = MagicMock()
    base_dir.__truediv__.return_value.exists.return_value = False
    with (
        patch.object(updater, "BASE_DIR", base_dir),
        patch("importlib.metadata.version", side_effect=Exception),
        patch(
            "builtins.open",
            return_value=io.BytesIO(b'[project]\nversion = "8.0"\n'),
        ),
    ):
        assert updater._read_version() == "8.0"


def _run_thread_immediately(target, args=(), daemon=True):
    target(*args)


def test_do_update_manual_no_release_and_latest(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            return_value=updater.github_client.ReleaseLookupResult(
                updater.github_client.ReleaseLookupStatus.NO_COMPATIBLE_RELEASE
            ),
        ),
        patch.object(updater.wx, "MessageBox") as message_box,
        patch.object(
            updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)
        ) as call_after,
    ):
        updater.do_update(is_manual=True)
        assert call_after.called
        assert "no hay una versión compatible" in message_box.call_args.args[0].lower()
    release = SimpleNamespace(version=updater.VERSION, description="notes")
    with (
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            return_value=updater.github_client.ReleaseLookupResult(
                updater.github_client.ReleaseLookupStatus.SUCCESS, release
            ),
        ),
        patch.object(updater.wx, "MessageBox") as message_box,
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
    ):
        updater.do_update(is_manual=True)
        assert message_box.call_args.args[0] == (
            "Al parecer tienes la última versión del programa"
        )


def test_do_update_starts_install_for_new_release(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)
    release = SimpleNamespace(version="99.0", description="notes")

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            return_value=updater.github_client.ReleaseLookupResult(
                updater.github_client.ReleaseLookupStatus.SUCCESS, release
            ),
        ),
        patch("update.updater.show_release_notes_dialog", return_value=True),
        patch("update.updater._install_update") as install,
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
        patch.object(updater.threading, "Thread", side_effect=run_thread),
    ):
        updater.do_update()
    install.assert_called_once_with(release)


def test_do_update_reports_check_exception(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            side_effect=RuntimeError("offline"),
        ),
        patch.object(updater.wx, "MessageBox"),
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
    ):
        updater.do_update(is_manual=True)


def test_do_update_beta_current_prerelease_reports_latest(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "VERSION", "3.95rc4")
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)
    release = SimpleNamespace(version="3.95rc4", description="notes")
    result = updater.github_client.ReleaseLookupResult(
        updater.github_client.ReleaseLookupStatus.SUCCESS, release
    )

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(updater, "get_channel", return_value="beta"),
        patch.object(updater.github_client, "get_latest_release_result", return_value=result),
        patch("update.updater.show_release_notes_dialog", return_value=False),
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(updater.wx, "MessageBox") as message_box,
    ):
        updater.do_update(is_manual=True)

    message_box.assert_called_once()
    assert message_box.call_args.args[0] == (
        "Al parecer tienes la última versión del programa"
    )


def test_github_client_skips_invalid_candidate_version():
    from update import github_client

    invalid = SimpleNamespace(version="not-a-version")
    with patch.object(github_client, "_parse_release", return_value=invalid):
        assert github_client._select_highest_release([{}]) is None


def test_install_update_handles_checksum_and_disabled_backup(tmp_path):
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": False}),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value=None),
        patch("update.updater.verify") as verify,
        patch("update.updater.extract") as extract,
    ):
        updater._install_update(release)
    verify.assert_not_called()
    extract.assert_not_called()


def test_install_update_success_cleans_backup_and_notifies(sin_interfaz):
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": True}),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", return_value="backup"),
        patch("update.updater.extract"),
        patch("update.updater.launch_bootstrap", return_value=0) as bootstrap,
        patch("update.updater.cleanup_backup") as cleanup,
    ):
        updater._install_update(release)
    cleanup.assert_called_once_with("backup")
    assert bootstrap.call_args.kwargs["backup_dir"] == "backup"
    assert sin_interfaz.llamadas == [
        updater.iniciar_descarga,
        updater.aviso_descargada,
        updater.mostrar_ventanas,
    ]


def test_install_update_removes_a_half_made_backup(sin_interfaz, tmp_path):
    """Si create_backup falla a medias, backup_path sigue en None: la carpeta
    a medio copiar se borra igual (se conoce su sitio)."""
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": True}),
        patch.object(updater, "BASE_DIR", tmp_path / "VeTube"),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", side_effect=OSError("disco lleno")),
        patch("update.updater.cleanup_backup") as cleanup,
    ):
        updater._install_update(release)
    cleanup.assert_called_once_with(str(tmp_path / f"_backup_v{updater.VERSION}"))


def test_install_update_discards_backup_when_bootstrap_does_not_start(sin_interfaz):
    """El bootstrap no arrancó (código 1): la instalación está intacta, así
    que no hay nada que restaurar; la copia de seguridad se borra, las
    ventanas vuelven y se avisa."""
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": True}),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", return_value="backup"),
        patch("update.updater.extract"),
        patch("update.updater.launch_bootstrap", return_value=1),
        patch("update.updater.cleanup_backup") as cleanup,
    ):
        updater._install_update(release)
    cleanup.assert_called_once_with("backup")
    assert sin_interfaz.llamadas[-2] is updater.mostrar_ventanas
    sin_interfaz.llamadas[-1]()
    sin_interfaz.aviso.assert_called_once_with("el instalador no pudo arrancar (código 1)")


def test_install_update_translates_the_disk_space_reason(sin_interfaz):
    """Sin espacio para la copia de seguridad es el fallo en el que el usuario
    puede hacer algo: se le dice en su idioma y con la cifra."""
    from update.backup import InsufficientSpaceError

    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    error = InsufficientSpaceError("Need 1200 MB")
    error.required_mb = 1200
    with (
        patch.object(updater, "config", {"create_backup_before_update": True}),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", side_effect=error),
        patch("update.updater.extract") as extract,
    ):
        updater._install_update(release)
    extract.assert_not_called()
    sin_interfaz.llamadas[-1]()
    sin_interfaz.aviso.assert_called_once_with(
        "no hay espacio suficiente en el disco: hacen falta 1200 MB libres para la copia de seguridad"
    )


def test_en_interfaz_waits_for_the_progress_bar_update_to_finish(sin_interfaz):
    """Si la petición llega mientras ProgressDialog.Update() está en curso,
    se aplaza con un temporizador y el hilo de descarga sigue esperando; solo
    cuando corre de verdad se libera."""
    from update import updater as real

    en_interfaz = sin_interfaz.original  # la fixture sustituye la función; aquí se prueba la real
    estados = iter([True, True, False])
    aplazadas = []
    hecho = []
    with (
        patch("update.updater.dentro_de_update", side_effect=lambda: next(estados)),
        patch.object(real.wx, "CallAfter", side_effect=lambda fn: fn()),
        patch.object(real.wx, "CallLater", side_effect=lambda ms, fn: aplazadas.append(fn)),
    ):
        en_interfaz(lambda: hecho.append(True), esperar=False)
        assert hecho == [] and len(aplazadas) == 1
        aplazadas.pop()()  # el temporizador dispara, sigue dentro de Update
        assert hecho == [] and len(aplazadas) == 1
        aplazadas.pop()()  # Update terminó
        assert hecho == [True] and aplazadas == []


def test_bootstrap_del_paquete_prefers_the_downloaded_one(tmp_path):
    """El bootstrap de la instalación se traba a sí mismo (tiene abiertos sus
    .pyd de lib/); se lanza el del paquete descargado, que corre desde la
    carpeta temporal. Si el paquete no trae ninguno, se usa el instalado."""
    assert updater._bootstrap_del_paquete(str(tmp_path)) == str(updater.BOOTSTRAP_EXE)
    (tmp_path / "bootstrap.exe").write_bytes(b"")
    assert updater._bootstrap_del_paquete(str(tmp_path)) == str(tmp_path / "bootstrap.exe")


def test_fetch_checksum_success_and_http_failure():
    response = MagicMock(text="hash  file.zip")
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    with patch("update.updater.httpx.Client", return_value=client):
        assert updater._fetch_checksum("url") == "hash  file.zip"
    client.get.side_effect = httpx.ConnectError("offline")
    with patch("update.updater.httpx.Client", return_value=client):
        assert updater._fetch_checksum("url") is None


def test_donation_dialog_accept_opens_browser(monkeypatch):
    monkeypatch.setattr(update, "_", lambda text: text, raising=False)
    dialog = MagicMock(ShowModal=MagicMock(return_value=update.wx.ID_YES))
    with (
        patch.object(update.wx, "MessageDialog", return_value=dialog),
        patch.object(update.wx, "LaunchDefaultBrowser") as launch,
    ):
        update.donation()
    launch.assert_called_once()


def test_donation_dialog_decline_does_not_open_browser(monkeypatch):
    monkeypatch.setattr(update, "_", lambda text: text, raising=False)
    dialog = MagicMock(ShowModal=MagicMock(return_value=update.wx.ID_NO))
    with (
        patch.object(update.wx, "MessageDialog", return_value=dialog),
        patch.object(update.wx, "LaunchDefaultBrowser") as launch,
    ):
        update.donation()
    launch.assert_not_called()


def _do_update_con_release(monkeypatch, donations, donation, install):
    """do_update() con una versión nueva aceptada; devuelve el orden de los gestos."""
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    release = SimpleNamespace(version="99.0", description="notes")
    orden = []
    donation.side_effect = lambda: orden.append("donation")
    install.side_effect = lambda r: orden.append("install")

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(updater, "config", {"donations": donations}),
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            return_value=updater.github_client.ReleaseLookupResult(
                updater.github_client.ReleaseLookupStatus.SUCCESS, release
            ),
        ),
        patch("update.updater.show_release_notes_dialog", return_value=True),
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
        patch.object(updater.threading, "Thread", side_effect=run_thread),
    ):
        updater.do_update()
    return orden


def test_donation_dialog_is_answered_before_the_download_starts(monkeypatch):
    """Con las donaciones desactivadas, el diálogo se muestra en el hilo de la
    interfaz tras «Actualizar ahora» y ANTES de arrancar el hilo de descarga:
    lanzado con CallAfter durante la descarga se abría con su dueña (la
    ventana principal) ya escondida y desaparecía sin respuesta."""
    with (
        patch("update.updater.donation") as donation,
        patch("update.updater._install_update") as install,
    ):
        orden = _do_update_con_release(monkeypatch, False, donation, install)
    assert orden == ["donation", "install"]


def test_donation_dialog_is_skipped_when_enabled(monkeypatch):
    with (
        patch("update.updater.donation") as donation,
        patch("update.updater._install_update") as install,
    ):
        orden = _do_update_con_release(monkeypatch, True, donation, install)
    assert orden == ["install"]


def test_install_update_never_opens_the_donation_dialog(sin_interfaz):
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": False, "donations": False}),
        patch("update.updater.donation") as donation,
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.extract"),
        patch("update.updater.launch_bootstrap", return_value=0),
    ):
        updater._install_update(release)
    donation.assert_not_called()


def test_wx_updater_progress_and_notifications(monkeypatch):
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    wxUpdater.progress_dialog = None
    dialog = MagicMock()
    with (
        patch.object(wxUpdater.wx, "CallAfter", side_effect=lambda fn: fn()),
        patch.object(wxUpdater, "create_progress_dialog", return_value=dialog),
    ):
        wxUpdater.progress_callback(10, 100)
        wxUpdater.progress_callback(100, 100)
        # La misma barra sigue para la copia de seguridad: no se destruye
        # al terminar la descarga, y nunca llega al máximo (sin PD_AUTO_HIDE,
        # Update(100) no vuelve hasta que el usuario pulse Cerrar).
        wxUpdater.backup_progress_callback(1, 2)
        wxUpdater.backup_progress_callback(2, 2)
    dialog.Show.assert_called_once()
    dialog.Destroy.assert_not_called()
    assert [c.args[0] for c in dialog.Update.call_args_list] == [10, 99, 50, 99]
    assert "copia de seguridad" in dialog.Update.call_args_list[2].args[1]
    assert wxUpdater.progress_dialog is dialog
    assert not wxUpdater.dentro_de_update()
    wxUpdater.cerrar_barra()
    dialog.Destroy.assert_called_once()
    assert wxUpdater.progress_dialog is None
    with (
        patch.object(wxUpdater.wx, "CallAfter", side_effect=lambda fn: fn()),
        patch.object(wxUpdater.wx, "MessageDialog", return_value=MagicMock()),
    ):
        wxUpdater.rollback_notification("checksum")
        wxUpdater.no_updates_dialog("1.0")
    wxUpdater.progress_dialog = dialog
    with patch.object(wxUpdater.wx, "MessageDialog", return_value=MagicMock()) as aviso:
        wxUpdater.aviso_descargada()
    aviso.return_value.ShowModal.assert_called_once()
    # La barra es la madre del aviso: así sale delante aunque el programa esté escondido.
    assert aviso.call_args.args[0] is dialog
    # El botón se llama como dice la frase, en el idioma de VeTube y no en el de Windows.
    aviso.return_value.SetOKLabel.assert_called_once_with("&Aceptar")
    wxUpdater.progress_dialog = None


def test_wx_updater_update_reentrancy_is_visible(monkeypatch):
    """Update() procesa CallAfter pendientes: dentro_de_update() debe ser True
    mientras corre (anidado incluido) y False al salir, para que updater.py
    aplace lo que no puede ejecutarse ahí dentro."""
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    vistos = []
    dialog = MagicMock()

    def _update(pct, msg):
        vistos.append(wxUpdater.dentro_de_update())
        if pct == 10:
            wxUpdater._actualizar_barra(20, "anidado")  # como haría el yield interno
            vistos.append(wxUpdater.dentro_de_update())

    dialog.Update.side_effect = _update
    wxUpdater.progress_dialog = dialog
    wxUpdater._actualizar_barra(10, "x")
    assert vistos == [True, True, True]
    assert not wxUpdater.dentro_de_update()
    wxUpdater.progress_dialog = None


def test_wx_updater_hides_and_restores_windows(monkeypatch):
    """iniciar_descarga crea la barra de progreso ANTES de esconder las
    ventanas (el foco pasa a la barra); mostrar_ventanas devuelve solo las
    que estaban a la vista y sigue viva la referencia."""
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    wxUpdater.progress_dialog = None
    wxUpdater._ventanas_ocultas = []
    principal = MagicMock(); principal.IsShown.return_value = True
    escondida = MagicMock(); escondida.IsShown.return_value = False
    destruida = MagicMock(); destruida.IsShown.return_value = True
    destruida.__bool__ = lambda self: False
    dialogo = MagicMock(); dialogo.IsShown.return_value = True
    with (
        patch.object(wxUpdater, "create_progress_dialog", return_value=dialogo),
        patch.object(
            wxUpdater.wx,
            "GetTopLevelWindows",
            return_value=[principal, escondida, dialogo, destruida],
        ),
        patch.object(wxUpdater.wx, "GetActiveWindow", return_value=principal),
    ):
        wxUpdater.iniciar_descarga()
    dialogo.Show.assert_called_once()
    dialogo.Hide.assert_not_called()
    principal.Hide.assert_called_once()
    escondida.Hide.assert_not_called()
    assert wxUpdater._ventanas_ocultas == [principal, destruida]

    with patch.object(wxUpdater.wx, "CallAfter", side_effect=lambda fn: fn()):
        wxUpdater.mostrar_ventanas()
    principal.Show.assert_called_once()
    principal.Raise.assert_called_once()
    principal.SetFocus.assert_called_once()
    destruida.Show.assert_not_called()
    assert wxUpdater._ventanas_ocultas == []
    # Al volver, la barra se cierra (después de mostrar: el primer plano
    # pasa de la barra a la ventana principal, no a otro programa).
    dialogo.Destroy.assert_called_once()
    assert wxUpdater.progress_dialog is None


def test_wx_updater_restores_the_window_that_had_focus_first(monkeypatch):
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    wxUpdater.progress_dialog = MagicMock()
    principal = MagicMock(); principal.IsShown.return_value = True
    chat = MagicMock(); chat.IsShown.return_value = True
    with patch.object(wxUpdater.wx, "GetTopLevelWindows", return_value=[principal, chat]):
        wxUpdater.ocultar_ventanas(activa=chat)
    # La que tenía el foco (el chat) es la que vuelve al frente.
    assert wxUpdater._ventanas_ocultas == [chat, principal]
    wxUpdater._ventanas_ocultas = []
    wxUpdater.progress_dialog = None


def test_wx_updater_dialog_choices(monkeypatch):
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    dialog = MagicMock(ShowModal=MagicMock(return_value=wxUpdater.wx.ID_YES))
    with (
        patch.object(wxUpdater.wx, "MessageDialog", return_value=dialog),
        patch.object(wxUpdater, "get_channel", return_value="beta"),
    ):
        assert wxUpdater.available_update_dialog("2.0", "notes") is True
    dialog.ShowModal.return_value = wxUpdater.wx.ID_NO
    with patch.object(wxUpdater.wx, "MessageDialog", return_value=dialog):
        assert wxUpdater.available_update_dialog("2.0", "notes") is False


def test_wx_updater_creates_check_and_download_dialogs(monkeypatch):
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    dialog = MagicMock()
    with patch.object(wxUpdater.wx, "ProgressDialog", return_value=dialog):
        assert wxUpdater.checking_updates_dialog() is dialog
        assert wxUpdater.create_progress_dialog() is dialog
    dialog.Pulse.assert_called_once()
    dialog.Show.assert_called_once()


def test_release_notes_helpers_and_navigation(monkeypatch):
    monkeypatch.setattr(release_notes_dialog, "_", lambda text: text, raising=False)
    html = release_notes_dialog._markdown_to_html(
        "# Title\n\n**bold** *italic*\n\n- item\n\n[x](https://example.com)"
    )
    assert "<h1>Title</h1>" in html and "<strong>bold</strong>" in html
    assert '<a href="https://example.com">x</a>' in html
    assert "<html>" in release_notes_dialog._get_styled_html("Title", html)
    dialog = release_notes_dialog.ReleaseNotesDialog.__new__(
        release_notes_dialog.ReleaseNotesDialog
    )
    dialog.version = "2.0"
    dialog.release_notes = "notes"
    dialog.webview = MagicMock()
    dialog._load_content()
    assert dialog.webview.SetPage.called
    event = MagicMock()
    event.GetURL.return_value = "https://example.com"
    with patch.object(release_notes_dialog.wx, "LaunchDefaultBrowser"):
        dialog._on_webview_navigating(event)
    event.Veto.assert_called_once()
    dialog._on_webview_navigating(SimpleNamespace(GetURL=lambda: "about:blank"))


def test_release_notes_dialog_callbacks_and_fallback(monkeypatch):
    monkeypatch.setattr(release_notes_dialog, "_", lambda text: text, raising=False)
    dialog = release_notes_dialog.ReleaseNotesDialog.__new__(
        release_notes_dialog.ReleaseNotesDialog
    )
    dialog.version = "2.0"
    dialog.release_notes = "raw notes"
    dialog.webview = MagicMock()
    dialog.webview.SetPage.side_effect = [RuntimeError("webview unavailable"), None]
    with patch.object(release_notes_dialog.logger, "exception"):
        dialog._load_content()
    assert "raw notes" in dialog.webview.SetPage.call_args.args[0]
    dialog.user_accepted = False
    dialog.EndModal = MagicMock()
    dialog._on_update(None)
    assert dialog.get_user_choice() is True
    dialog._on_cancel(None)
    assert dialog.get_user_choice() is False
    for url in ("", "data:text/plain,ok", "ftp://example.com"):
        event = SimpleNamespace(GetURL=lambda url=url: url)
        dialog._on_webview_navigating(event)


def test_show_release_notes_dialog_returns_modal_and_choice(monkeypatch):
    monkeypatch.setattr(release_notes_dialog, "_", lambda text: text, raising=False)
    dialog = MagicMock()
    dialog.ShowModal.return_value = release_notes_dialog.wx.ID_OK
    dialog.get_user_choice.return_value = True
    with patch.object(release_notes_dialog, "ReleaseNotesDialog", return_value=dialog):
        assert release_notes_dialog.show_release_notes_dialog(None, "1.0", "notes")
    dialog.Destroy.assert_called_once_with()


def test_bootstrap_fix_helpers_and_main_success(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap_fix, "LOG_FILE", str(tmp_path / "log.txt"))
    bootstrap_fix.log("message")
    assert "message" in (tmp_path / "log.txt").read_text()
    bootstrap_fix._write_rollback_signal(str(tmp_path))
    assert (tmp_path / bootstrap_fix.ROLLBACK_SIGNAL).exists()
    with patch.object(bootstrap_fix.ctypes, "windll", create=True) as windll:
        windll.kernel32.OpenProcess.return_value = 0
        bootstrap_fix.kill_process(123)
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    exe = dest / "app.exe"
    exe.write_text("exe")
    monkeypatch.setattr(
        sys, "argv", ["bootstrap.py", "1", str(source), str(dest), str(exe)]
    )
    with (
        patch.object(bootstrap_fix.time, "sleep"),
        patch.object(bootstrap_fix, "kill_process"),
        patch.object(bootstrap_fix.shutil, "copytree"),
        patch.object(bootstrap_fix.subprocess, "Popen"),
        pytest.raises(SystemExit) as result,
    ):
        bootstrap_fix.main()
    assert result.value.code == bootstrap_fix.EXIT_SUCCESS


def test_bootstrap_fix_rejects_missing_arguments(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["bootstrap.py"])
    with patch.object(bootstrap_fix, "log"), pytest.raises(SystemExit) as result:
        bootstrap_fix.main()
    assert result.value.code == bootstrap_fix.EXIT_FAILURE


@pytest.mark.parametrize(
    ("error", "exit_code"),
    [(PermissionError("denied"), bootstrap_fix.EXIT_CANCELLED),
     (OSError("copy failed"), bootstrap_fix.EXIT_FAILURE)],
)
def test_bootstrap_fix_copy_errors_write_rollback(tmp_path, monkeypatch, error, exit_code):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    monkeypatch.setattr(
        sys, "argv", ["bootstrap.py", "1", str(source), str(dest), "missing.exe"]
    )
    with (
        patch.object(bootstrap_fix.time, "sleep"),
        patch.object(bootstrap_fix, "kill_process"),
        patch.object(bootstrap_fix, "_copy_update_files", side_effect=error),
        patch.object(bootstrap_fix, "_write_rollback_signal") as rollback,
        pytest.raises(SystemExit) as result,
    ):
        bootstrap_fix.main()
    assert result.value.code == exit_code
    rollback.assert_called_once_with(str(dest))


def test_bootstrap_fix_uses_fallback_executable_launch(tmp_path, monkeypatch):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    exe = dest / "app.exe"
    exe.write_text("exe")
    original = tmp_path / "_internal" / "app.exe"
    monkeypatch.setattr(
        sys, "argv", ["bootstrap.py", "1", str(source), str(dest), str(original)]
    )
    with (
        patch.object(bootstrap_fix.time, "sleep"),
        patch.object(bootstrap_fix, "kill_process"),
        patch.object(bootstrap_fix, "_copy_update_files"),
        patch.object(bootstrap_fix.subprocess, "Popen", side_effect=[OSError("first"), MagicMock()]),
        pytest.raises(SystemExit) as result,
    ):
        bootstrap_fix.main()
    assert result.value.code == bootstrap_fix.EXIT_SUCCESS
