from setup import reader
from globals import data_store
class MediaHandler:
    def __init__(self, url=None):
        self.url = url
        self.sonando = False
        self.player = None
        self.player_type = None
        self.cargando=False

    def play(self):
        if not self.url:
            print("Error: No se ha proporcionado ninguna URL.")
            return
        if self.cargando:
            reader.leer_auto("ya está cargando un reproductor")
            return
        self.cargando = True
        reader.leer_auto("Cargando el reproductor")

        def playback_task():
            try:
                new_player_type = 'sound' if "mp4" in self.url else 'vlc'
                if self.player_type != new_player_type:
                    if self.player:
                        self.player.release()

                    if new_player_type == 'sound':
                        from players.sound_helper import playsound
                        self.player = playsound()
                        self.cargando = False
                    else:
                        from players.vlc_helper import MinimalVlcPlayer
                        def vlc_playing_callback(event):
                            self.cargando = False
                        self.player = MinimalVlcPlayer(playing_callback=vlc_playing_callback)

                    self.player_type = new_player_type

                self.sonando = True
                self.player.playsound(self.url)
            except Exception as e:
                print(f"Error in playback_task: {e}")
                self.cargando = False

        import threading
        thread = threading.Thread(target=playback_task, daemon=True)
        thread.start()

    def toggle_pause(self):
        """Alterna el estado de reproducción/pausa del medio."""
        if self.sonando and self.player:
            self.player.toggle_player()
        else: self.play()
    def adelantar(self, seconds):
        """Avanza la reproducción un número de segundos."""
        if self.sonando and self.player:
            self.player.adelantar(seconds)

    def atrasar(self, seconds):
        """Retrocede la reproducción un número de segundos."""
        if self.sonando and self.player:
            self.player.atrasar(seconds)

    def volume_up(self, step=10):
        """Sube el volumen del reproductor."""
        if self.sonando and self.player and hasattr(self.player, 'volume_up'):
            if self.player_type == 'sound':
                # Convert step from 0-100 scale to 0.0-1.0 scale
                sound_step = step / 100.0
                self.player.volume_up(sound_step)
            else:
                self.player.volume_up(step)

    def volume_down(self, step=10):
        """Baja el volumen del reproductor."""
        if self.sonando and self.player and hasattr(self.player, 'volume_down'):
            if self.player_type == 'sound':
                # Convert step from 0-100 scale to 0.0-1.0 scale
                sound_step = step / 100.0
                self.player.volume_down(sound_step)
            else:
                self.player.volume_down(step)

    def release(self):
        """Libera los recursos del reproductor actual."""
        if self.player:
            self.player.release()
            self.player = None
            self.player_type = None
        self.sonando = False
