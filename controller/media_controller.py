from players.media_handler import MediaHandler
from globals import data_store
class MediaController:
    def __init__(self, url):
        self.player = MediaHandler(url=url)
        self.player.set_volume(data_store.config.get('volumen', 100))
        if data_store.config['reproducir']: self.play()

    def play(self):
        self.player.play()

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
