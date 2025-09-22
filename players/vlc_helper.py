import os,platform
# Configurar las variables de entorno para que python-vlc encuentre las DLLs
dir_current_script = os.path.dirname(os.path.abspath(__file__))
arch="64" if platform.architecture()[0][:2] == "64" else "32"
# Subir un nivel para llegar a la raíz del proyecto y luego entrar a la carpeta 64
path_to_vlc_dir = os.path.abspath(os.path.join(dir_current_script, '..', arch))
# La ruta a la carpeta que contiene libvlccore.dll y la carpeta de plugins
os.environ['PYTHON_VLC_MODULE_PATH'] = path_to_vlc_dir
# La ruta al archivo libvlc.dll
os.environ['PYTHON_VLC_LIB_PATH'] = os.path.join(path_to_vlc_dir, 'libvlc.dll')
# Importar vlc DESPUÉS de configurar las variables de entorno
import vlc

class MinimalVlcPlayer:
    def __init__(self, playing_callback=None):
        self.Instance = vlc.Instance("--quiet")
        self.Instance.log_unset()
        self.player = self.Instance.media_player_new()
        self.player.video_set_mouse_input(False)
        self.player.video_set_key_input(False)
        self.url = None
        self.playing_callback = playing_callback
        if self.playing_callback:
            self.event_manager = self.player.event_manager()
            self.event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, self.playing_callback)
        else:
            self.event_manager = None

    def playsound(self, valor):
        self.Media = self.Instance.media_new(valor)
        self.player.set_media(self.Media)
        self.url = valor
        self.player.play()

    def toggle_player(self):
        if self.player.is_playing(): self.player.pause()
        else: self.player.play()
    def tiempotranscurrido(self): return self.player.get_time()

    def adelantar(self, segundos):
        if self.player.is_seekable():
            current_time = self.tiempotranscurrido()
            new_time = current_time + (segundos * 1000)
            self.player.set_time(new_time)
        else: print("No se puede avanzar en este medio.")

    def atrasar(self, segundos):
        if self.player.is_seekable():
            current_time = self.tiempotranscurrido()
            new_time = current_time - (segundos * 1000)
            # Asegurarse de no ir a tiempo negativo
            if new_time < 0: new_time = 0
            self.player.set_time(new_time)
        else: print("No se puede retroceder en este medio.")

    def get_volume(self):
        """Devuelve el volumen actual del reproductor (0 a 100)."""
        return self.player.audio_get_volume()

    def set_volume(self, volume):
        """Establece el volumen del reproductor."""
        # Asegurarse de que el volumen esté en el rango de 0 a 100
        vol = max(0, min(100, volume))
        return self.player.audio_set_volume(vol)

    def volume_up(self, step=10):
        """Sube el volumen."""
        current_volume = self.get_volume()
        new_volume = current_volume + step
        self.set_volume(new_volume)
        return new_volume

    def volume_down(self, step=10):
        """Baja el volumen."""
        current_volume = self.get_volume()
        new_volume = current_volume - step
        self.set_volume(new_volume)
        return new_volume

    def release(self):
        if self.player:
            if self.event_manager and self.playing_callback:
                self.event_manager.event_detach(vlc.EventType.MediaPlayerPlaying)
            self.player.release()
        if self.Instance:
            self.Instance.release()