import os
import sys
import types

# Bloquear la carga de plugins BASS en sound_lib.external.__init__.
# Ese __init__.py importa TODOS los plugins (bassopus, basswma, bass_aac,
# bass_alac, bassflac, bassmidi) al arrancar, lo que carga 6 DLLs extra
# en cadena. En HDD eso suma ~10 s al arranque. VeTube solo necesita
# bass.dll (MP3/WAV son nativos), así que sustituimos el paquete por un
# stub: el __init__. real nunca se ejecuta y los plugins no se cargan.
# Los stream de audio que necesiten un codec (Opus, FLAC…) se cargan
# bajo demanda cuando BASS devuelva BASS_ERROR_CODEC (20).
if "sound_lib.external" not in sys.modules:
    import sound_lib as _sl

    _ext_dir = os.path.join(os.path.dirname(_sl.__file__), "external")
    _stub = types.ModuleType("sound_lib.external")
    _stub.__path__ = [_ext_dir]  # permite resolver pybass, paths, etc.
    _stub.__package__ = "sound_lib.external"
    sys.modules["sound_lib.external"] = _stub

from sound_lib import stream  # noqa: E402
from sound_lib.main import BassError  # noqa: E402
from sound_lib.output import Output  # noqa: E402


class SoundPlayer:
    def __init__(self):
        # Sin dispositivo de audio (o con BASS roto), la app debe ARRANCAR
        # muda en vez de morir: las máquinas de validación de winget no tienen
        # tarjeta de sonido, y un usuario con el audio averiado se comía un
        # UnboundLocalError antes de que la app dijera nada.
        output = None
        try:
            output = Output(device=-1)
        except BassError as e:
            if e.code == 14:
                # Ya estaba inicializado: liberar y reintentar.
                try:
                    Output.free()
                    output = Output(device=-1)
                except BassError:
                    output = None
        if output is not None:
            try:
                output.start()
            except BassError:
                output = None
        # Setup:
        self.output = output
        self.sound = None
        self.devicenames = output.get_device_names() if output else []
        self.device = 1

    def setdevice(self, device):
        if self.output is None:
            return
        if device > 0 and device <= len(self.devicenames):
            self.device = device
        else:
            raise Exception(
                "device is less than 1 or greater than the available devices."
            )

    def play(self, filename, block=False):
        if self.output is None:
            return
        if (
            self.sound is not None
            and hasattr(self.sound, "is_playing")
            and self.sound.is_playing
        ):
            self.sound.stop()
        if self.device != self.output.get_device():
            self.output.set_device(self.device)
        try:
            self.sound = stream.FileStream(file=filename)
        except BassError as e:
            if e.code == 2 and (
                filename.startswith("http://") or filename.startswith("https://")
            ):
                try:
                    self.sound = stream.URLStream(url=filename)
                except:
                    raise e
            else:
                raise e
        if not block:
            self.sound.play()
        else:
            self.sound.play_blocking()

    def toggle_player(self):
        if not self.sound:
            return
        if self.sound.is_playing:
            self.sound.pause()
        else:
            self.sound.play()

    def is_playing(self):
        return (
            self.sound is not None
            and hasattr(self.sound, "is_playing")
            and self.sound.is_playing
        )

    def atrasar(self, seconds):
        if not self.sound:
            return
        current_pos = self.sound.get_position()
        bytes_to_move = self.sound.seconds_to_bytes(seconds)
        new_pos = current_pos - bytes_to_move
        new_pos = max(new_pos, 0)
        self.sound.set_position(new_pos)

    def adelantar(self, seconds):
        if not self.sound:
            return
        current_pos = self.sound.get_position()
        total_length = self.sound.get_length()
        bytes_to_move = self.sound.seconds_to_bytes(seconds)
        new_pos = current_pos + bytes_to_move
        new_pos = min(new_pos, total_length)
        self.sound.set_position(new_pos)

    def get_volume(self):
        """Devuelve el volumen actual del reproductor (0.0 a 1.0)."""
        if self.sound:
            return self.sound.volume
        return 1.0  # Default volume

    def set_volume(self, volume):
        """Establece el volumen del reproductor."""
        if self.sound:
            # Asegurarse de que el volumen esté en el rango de 0.0 a 1.0
            vol = max(0.0, min(1.0, volume))
            self.sound.volume = vol

    def volume_up(self, step=0.1):
        """Sube el volumen."""
        current_volume = self.get_volume()
        new_volume = current_volume + step
        self.set_volume(new_volume)

    def volume_down(self, step=0.1):
        """Baja el volumen."""
        current_volume = self.get_volume()
        new_volume = current_volume - step
        self.set_volume(new_volume)

    def release(self):
        if self.sound:
            self.sound.free()
