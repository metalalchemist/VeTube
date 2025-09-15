class MediaHandler:
    def __init__(self, url=None):
        self.url = url
        self.sonando = False
        self.player = None
        self.player_type = None

    def play(self):
        if not self.url:
            print("Error: No se ha proporcionado ninguna URL.")
            return

        def playback_task():
            # Determina qué reproductor usar y créalo si es necesario
            new_player_type = 'sound' if "mp4" in self.url else 'vlc'
            if self.player_type != new_player_type:
                if self.player:
                    self.player.release()
                
                if new_player_type == 'sound':
                    from players.sound_helper import playsound
                    self.player = playsound()
                else:
                    from players.vlc_helper import MinimalVlcPlayer
                    self.player = MinimalVlcPlayer()
                
                self.player_type = new_player_type

            # Reproduce el sonido y actualiza el estado
            self.player.playsound(self.url)
            self.sonando = True
            print(f"Reproduciendo con {self.player_type}")
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

    def release(self):
        """Libera los recursos del reproductor actual."""
        if self.player:
            self.player.release()
            self.player = None
            self.player_type = None
        self.sonando = False
