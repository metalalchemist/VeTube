from setup import reader, player
from players.sound_helper import SoundPlayer
from globals import data_store
import threading

class MediaHandler:
    def __init__(self, url=None, state_callback=None):
        self.url = url
        self.sonando = False
        self.player = None
        self.player_type = None
        self.cargando = False
        self.state_callback = state_callback

    def _notify_state_change(self, state):
        if self.state_callback:
            self.state_callback(state)

    def play(self):
        if not self.url:
            print("Error: No se ha proporcionado ninguna URL.")
            return
        if self.cargando:
            reader.leer_auto("ya está cargando un reproductor")
            return
        if self.sonando and self.player and self.player.is_playing(): # Already playing
            self._notify_state_change('playing') # Re-confirm playing state
            return

        self.cargando = True
        reader.leer_auto("Cargando el reproductor")
        self._notify_state_change('loading')

        def playback_task():
            try:
                new_player_type = 'sound' if "mp4" in self.url else 'vlc'
                if self.player_type != new_player_type:
                    if self.player:
                        self.player.release()

                    if new_player_type == 'sound':
                        self.player = SoundPlayer()
                    else:
                        from players.vlc_helper import MinimalVlcPlayer
                        def vlc_playing_callback(event):
                            self.cargando = False
                            if self.player and self.player.is_playing():
                                self.sonando = True
                                self._notify_state_change('playing')
                            else:
                                self.sonando = False
                                self._notify_state_change('stopped')
                        self.player = MinimalVlcPlayer(playing_callback=vlc_playing_callback)

                    self.player_type = new_player_type

                self.sonando = True
                self.player.play(self.url)
                self.cargando = False
                self._notify_state_change('playing')
            except Exception as e:
                print(f"Error in playback_task: {e}")
                self.cargando = False
                self.sonando = False
                self._notify_state_change('stopped')

        thread = threading.Thread(target=playback_task, daemon=True)
        thread.start()

    def pause(self):
        """Pausa la reproducción del medio."""
        if self.sonando and self.player and self.player.is_playing():
            self.player.toggle_player()
            self.sonando = False
            self._notify_state_change('paused')

    def stop(self):
        """Detiene la reproducción y libera los recursos del reproductor."""
        if self.player:
            self.player.release()
            self.player = None
            self.player_type = None
        self.sonando = False
        self._notify_state_change('stopped')

    def toggle_pause(self):
        """Alterna el estado de reproducción/pausa del medio."""
        if self.sonando and self.player:
            self.player.toggle_player()
            self.sonando = self.player.is_playing()
            self._notify_state_change('playing' if self.sonando else 'paused')
        else:
            self.play()

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

    def set_volume(self, volume):
        """Establece el volumen del reproductor."""
        if self.player and hasattr(self.player, 'set_volume'):
            if self.player_type == 'sound':
                # Convert volume from 0-100 scale to 0.0-1.0 scale
                sound_volume = volume / 100.0
                self.player.set_volume(sound_volume)
            else:
                self.player.set_volume(volume)

    def release(self):
        """Libera los recursos del reproductor actual."""
        if self.player:
            self.player.release()
            self.player = None
            self.player_type = None
        self.sonando = False
        self._notify_state_change('stopped')

    def is_playing(self):
        return self.sonando and self.player and self.player.is_playing()