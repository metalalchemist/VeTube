import os
# Configurar las variables de entorno para que python-vlc encuentre las DLLs
dir_current_script = os.path.dirname(os.path.abspath(__file__))
# Subir un nivel para llegar a la raíz del proyecto y luego entrar a la carpeta 64
path_to_vlc_dir = os.path.abspath(os.path.join(dir_current_script, '..', '64'))
# La ruta a la carpeta que contiene libvlccore.dll y la carpeta de plugins
os.environ['PYTHON_VLC_MODULE_PATH'] = path_to_vlc_dir
# La ruta al archivo libvlc.dll
os.environ['PYTHON_VLC_LIB_PATH'] = os.path.join(path_to_vlc_dir, 'libvlc.dll')
# Importar vlc DESPUÉS de configurar las variables de entorno
import vlc

class MinimalVlcPlayer:
    def __init__(self):
        self.Instance = vlc.Instance("--quiet")
        self.Instance.log_unset()
        self.player = self.Instance.media_player_new()
        self.player.video_set_mouse_input(False)
        self.player.video_set_key_input(False)
        self.url = None

    def playsound(self, valor):
        self.Media = self.Instance.media_new(valor)
        self.player.set_media(self.Media)
        self.url = valor
        self.player.play()

    def toggle_player(self):
        if self.player.is_playing(): self.player.play()
        else: self.player.pause()
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

    def release(self):
        if self.player:
            self.player.release()
        if self.Instance:
            self.Instance.release()