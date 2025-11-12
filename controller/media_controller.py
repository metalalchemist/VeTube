from players.media_handler import MediaHandler
from globals import data_store
class MediaController:
    def __init__(self, url, state_callback=None):
        handler_callback = None
        if state_callback:
            handler_callback = lambda state: state_callback(self, state)
        self.player = MediaHandler(url=url, state_callback=handler_callback)
        self.player.set_volume(data_store.config.get('volumen', 100))
        if data_store.config['reproducir']: self.play()

    def play(self):
        self.player.play()

    def pause(self):
        if self.player:
            self.player.pause()

    def toggle_pause(self):
        self.player.toggle_pause()

    def adelantar(self):
        self.player.adelantar(data_store.config['tiempo'])

    def atrasar(self):
        self.player.atrasar(data_store.config['tiempo'])

    def volume_up(self):
        self.player.volume_up(data_store.config.get('cambiovolumen', 10))

    def volume_down(self):
        self.player.volume_down(data_store.config.get('cambiovolumen', 10))

    def release(self):
        if self.player:
            self.player.release()

    def is_playing(self):
        if self.player:
            return self.player.is_playing()
        return False
