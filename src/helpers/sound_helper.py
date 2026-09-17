from sound_lib import stream
from sound_lib.main import BassError
from sound_lib.output import Output


class playsound:
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
        if device > 0 or device < len(self.devicenames):
            self.device = device
        else:
            raise Exception(
                "device is less than 1 or greater than the available devices."
            )

    def playsound(self, filename, block=False):
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
