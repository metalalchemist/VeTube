"""Integration tests for the full update flow."""

from unittest.mock import MagicMock, patch

import pytest

from update.github_client import ReleaseInfo, clear_cache


@pytest.fixture(autouse=True)
def _clear_gh_cache():
    clear_cache()
    yield
    clear_cache()


def updater_version():
    from update.updater import VERSION

    return VERSION


def _make_release(tag="v4.0", version="4.0"):
    return ReleaseInfo(
        tag=tag,
        version=version,
        prerelease=False,
        description="New features",
        zip_url="https://example.com/VeTube.zip",
        checksum_url="https://example.com/VeTube.zip.sha256",
        zip_name="VeTube.zip",
    )


class TestInstallUpdateFlow:
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    @patch("update.updater.cleanup_backup")
    def test_successful_update(
        self,
        mock_cleanup,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        tmp_path,
        sin_interfaz,
    ):
        from update.updater import (
            _install_update,
            aviso_descargada,
            iniciar_descarga,
            mostrar_ventanas,
        )

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = True
        mock_backup.return_value = str(tmp_path / "backup")
        mock_bootstrap.return_value = 0

        _install_update(release)

        mock_download.assert_called_once()
        mock_fetch_checksum.assert_called_once_with(
            "https://example.com/VeTube.zip.sha256"
        )
        mock_verify.assert_called_once()
        mock_backup.assert_called_once()
        mock_extract.assert_called_once()
        mock_bootstrap.assert_called_once()
        # La copia de seguridad viaja al bootstrap: es él quien la usa o la borra.
        assert mock_bootstrap.call_args.kwargs["backup_dir"] == str(tmp_path / "backup")
        mock_cleanup.assert_called_once_with(str(tmp_path / "backup"))
        # Primero se esconde el programa; el aviso «descargada» se muestra ANTES
        # de lanzar el bootstrap (que cierra VeTube), esperando al Aceptar.
        # (y con VeTube todavía vivo tras un código 0, la interfaz vuelve)
        assert sin_interfaz.llamadas == [iniciar_descarga, aviso_descargada, mostrar_ventanas]
        assert sin_interfaz.call_args_list[1].kwargs == {"esperar": True}
        sin_interfaz.aviso.assert_not_called()

    @patch("update.updater.cleanup_backup")
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    def test_verification_fail_shows_windows_again(
        self,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        mock_cleanup,
        tmp_path,
        sin_interfaz,
    ):
        from update.updater import _install_update, mostrar_ventanas

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = False

        _install_update(release)

        mock_backup.assert_not_called()
        mock_extract.assert_not_called()
        mock_bootstrap.assert_not_called()
        # Aunque no se llegó a crear la copia de seguridad, se limpia su carpeta
        # (una copia a medias de un intento anterior no debe quedarse).
        assert mock_cleanup.call_args.args[0].endswith("_backup_v" + updater_version())
        # Orden fijo: primero vuelven las ventanas, después el aviso.
        assert sin_interfaz.llamadas[-2] is mostrar_ventanas
        sin_interfaz.llamadas[-1]()
        sin_interfaz.aviso.assert_called_once_with(
            "el archivo descargado no supera la comprobación de integridad"
        )

    @patch("update.updater.cleanup_backup")
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    def test_extraction_fail_discards_backup_without_restoring(
        self,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        mock_cleanup,
        tmp_path,
        sin_interfaz,
    ):
        """Antes del bootstrap no se ha tocado la instalación: no hay nada que
        restaurar (restaurar con VeTube abierto borraba archivos en uso). La
        copia de seguridad, ya inútil, se borra."""
        from update.updater import _install_update, mostrar_ventanas

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = True
        mock_backup.return_value = str(tmp_path / "backup")
        mock_extract.side_effect = OSError("extraction failed")

        _install_update(release)

        mock_bootstrap.assert_not_called()
        mock_cleanup.assert_called_once_with(str(tmp_path / "backup"))
        assert sin_interfaz.llamadas[-2] is mostrar_ventanas
        sin_interfaz.llamadas[-1]()
        sin_interfaz.aviso.assert_called_once_with("extraction failed")
        # Cada fase se anuncia por la voz del programa.
        assert [c.args[0] for c in sin_interfaz.anunciar.call_args_list] == [
            "Descargando la actualización",
            "Creando la copia de seguridad...",
            "Extrayendo la actualización...",
        ]

    @pytest.mark.parametrize(
        ("exit_code", "borra_backup", "motivo"),
        [
            (1, True, "el instalador no pudo arrancar (código 1)"),
            (2, True, "Windows no dio permiso para instalar"),  # UAC rechazado
            (-1, False, "el instalador sigue en marcha tras 30 segundos"),  # se le deja la copia
        ],
    )
    @patch("update.updater.cleanup_backup")
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    def test_bootstrap_not_run_shows_windows_again(
        self,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        mock_cleanup,
        exit_code,
        borra_backup,
        motivo,
        tmp_path,
        sin_interfaz,
    ):
        from update.updater import _install_update, mostrar_ventanas

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = True
        mock_backup.return_value = str(tmp_path / "backup")
        mock_bootstrap.return_value = exit_code

        _install_update(release)

        assert mock_cleanup.called is borra_backup
        assert sin_interfaz.llamadas[-2] is mostrar_ventanas
        sin_interfaz.llamadas[-1]()
        sin_interfaz.aviso.assert_called_once_with(motivo)


class TestVersionComparison:
    def test_newer_version_is_detected(self):
        from packaging.version import Version

        current = Version("1.0")
        latest = Version("99.0")
        assert latest > current

    def test_same_version_no_update(self):
        from packaging.version import Version

        current = Version("1.0")
        latest = Version("1.0")
        assert latest <= current

    def test_older_version_no_update(self):
        from packaging.version import Version

        current = Version("1.0")
        latest = Version("0.5")
        assert latest <= current


class TestChannelFiltering:
    @patch("update.github_client.httpx.Client")
    def test_stable_filters_prereleases(self, mock_client_cls):
        from update.github_client import get_latest_release

        releases = [
            {
                "tag_name": "v4.0-beta1",
                "prerelease": True,
                "body": "",
                "assets": [
                    {
                        "name": "VeTube.zip",
                        "browser_download_url": "https://example.com/VeTube.zip",
                    },
                    {
                        "name": "VeTube.zip.sha256",
                        "browser_download_url": "https://example.com/VeTube.zip.sha256",
                    },
                ],
            },
            {
                "tag_name": "v3.95",
                "prerelease": False,
                "body": "",
                "assets": [
                    {
                        "name": "VeTube.zip",
                        "browser_download_url": "https://example.com/VeTube.zip",
                    },
                    {
                        "name": "VeTube.zip.sha256",
                        "browser_download_url": "https://example.com/VeTube.zip.sha256",
                    },
                ],
            },
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = releases
        mock_response.headers = {"ETag": "etag"}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = get_latest_release(channel="stable")
        assert result is not None
        assert result.tag == "v3.95"
