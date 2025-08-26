import configparser
from os import path, makedirs

class KeyUtils:
    def __init__(self): self.leerTeclas()

    def escribirTeclas(self):
        config = configparser.ConfigParser(interpolation=None)
        config['atajos_chat'] = {
            'control+p': 'reader._leer.silence',
            'alt+shift+up': 'chat.elementoAnterior',
            'alt+shift+down': 'chat.elementoSiguiente',
            'alt+shift+left': 'chat.retrocederCategorias',
            'alt+shift+right': 'chat.avanzarCategorias',
            'alt+shift+home': 'chat.elemento_inicial',
            'alt+shift+end': 'chat.elemento_final',
            'alt+shift+f': 'chat.agregar_mensajes_favoritos',
            'alt+shift+c': 'chat.copiarMensajeActual',
            'alt+shift+r': 'chat.toggle_lectura_automatica',
            'alt+shift+s': 'chat.buscar_mensajes',
            'alt+shift+v': 'chat.mostrar_mensaje_actual',
            'alt+shift+d': 'chat.borrar_pagina_actual',
            'alt+shift+p': 'chat.toggle_sounds',
            'alt+shift+k': 'chat.mostrar_editor_combinaciones',
            'alt+shift+a': 'chat.archivar_mensaje',
        }
        makedirs("keymaps", exist_ok=True)
        with open('keymaps/keys.txt', 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        self.leerTeclas()

    def leerTeclas(self):
        config = configparser.ConfigParser(interpolation=None)
        if path.exists("keymaps/keys.txt"):
            config.read("keymaps/keys.txt")
            if 'atajos_chat' in config:
                self.teclas = list(config['atajos_chat'].keys())
            else:
                self.teclas = []
        else:
            self.escribirTeclas()
            self.leerTeclas()

    def reemplazar(self, old_shortcut, new_shortcut):
        config = configparser.ConfigParser(interpolation=None)
        config.read("keymaps/keys.txt")
        if 'atajos_chat' in config:
            function_call = None
            for key, value in config['atajos_chat'].items():
                if key == old_shortcut:
                    function_call = value
                    del config['atajos_chat'][key]
                    break
            
            if function_call:
                config['atajos_chat'][new_shortcut] = function_call
                with open("keymaps/keys.txt", 'w', encoding='utf-8') as configfile:
                    config.write(configfile)
                self.leerTeclas()
            else:
                print(f"Warning: Old shortcut '{old_shortcut}' not found in keys.txt for replacement.")
        else:
            print("Warning: [atajos_chat] section not found in keys.txt for replacement.")

editor=KeyUtils()