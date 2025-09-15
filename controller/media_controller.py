import configparser
from players.media_handler import MediaHandler
from helpers.keyboard_handler.wx_handler import WXKeyboardHandler

class MediaController:
    def __init__(self, url, frame):
        self.player = MediaHandler(url=url)
        self.keyboard_handler = WXKeyboardHandler(frame)
        self.shortcuts = {}
        self.register_shortcuts()

    def play(self):
        self.player.play()

    def toggle_pause(self):
        self.player.toggle_pause()

    def adelantar(self):
        self.player.adelantar(10)

    def atrasar(self):
        self.player.atrasar(10)

    def release(self):
        if self.keyboard_handler:
            self.keyboard_handler.unregister_all_keys()
        if self.player:
            self.player.release()

    def register_shortcuts(self):
        command_objects = {'player': self}
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read("keymaps/keys.txt")
            if 'atajos_player' in config:
                for key, command_str in config['atajos_player'].items():
                    try:
                        obj_name, method_path = command_str.split('.', 1)
                        if obj_name in command_objects:
                            target_obj = command_objects[obj_name]
                            # Asumimos que los métodos no tienen argumentos complejos desde el config
                            final_callable = getattr(target_obj, method_path)
                            if callable(final_callable):
                                self.shortcuts[key] = final_callable
                            else:
                                print(f"Advertencia: El comando '{command_str}' no resuelve a una función.")
                        else:
                            print(f"Advertencia: Objeto '{obj_name}' no definido para comandos de reproductor.")
                    except Exception as e:
                        print(f"Error parseando el atajo {key}={command_str}: {e}")
            if self.shortcuts:
                self.keyboard_handler.register_keys(self.shortcuts)
        except Exception as e:
            print(f"Error al leer o registrar atajos del reproductor: {e}")
