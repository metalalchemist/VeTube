import configparser
from os import path, makedirs

class KeyUtils:
    def __init__(self):
        self.teclas = {}
        self.leerTeclas()

    def leerTeclas(self):
        """
        Lee, limpia y actualiza el archivo de atajos. Es idempotente.
        1. Lee los atajos del usuario.
        2. Elimina duplicados, conservando la primera asignación para cada acción.
        3. Añade atajos por defecto para acciones que no estén asignadas.
        4. Reescribe el archivo solo si se han realizado cambios.
        """
        default_keys = {
            'control+alt+shift+right': 'chat_dialog.next_session',
            'control+alt+shift+left': 'chat_dialog.previous_session',
            'alt+shift+h': 'chat_dialog.toggle_chat_window_visibility',
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
            'alt+shift+b': 'chat.buscar_mensajes',
            'alt+shift+v': 'chat.mostrar_mensaje_actual',
            'alt+shift+d': 'chat.borrar_pagina_actual',
            'alt+shift+p': 'chat.toggle_sounds',
            'alt+shift+k': 'main.mostrar_editor_combinaciones',
            'alt+shift+a': 'chat.archivar_mensaje',
            'control+shift+p': 'chat_dialog.toggle_global_media_pause',
            'control+shift+right': 'media_player.adelantar',
            'control+shift+left': 'media_player.atrasar',
            'control+shift+up': 'media_player.volume_up',
            'control+shift+down': 'media_player.volume_down',
            'control+shift+s': 'media_player.release',
        }
        config_path = "keymaps/keys.txt"
        makedirs("keymaps", exist_ok=True)

        if not path.exists(config_path):
            config = configparser.ConfigParser(interpolation=None)
            config['atajos_chat'] = default_keys
            with open(config_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            self.teclas = default_keys
            return

        user_config = configparser.ConfigParser(interpolation=None)
        user_config.read(config_path, encoding='utf-8')
        original_keys = dict(user_config['atajos_chat']) if 'atajos_chat' in user_config else {}

        final_keys = {}
        actions_assigned = set()

        # 1. Primer paso: respetar las teclas del usuario y limpiar duplicados
        for key, action in original_keys.items():
            if action not in actions_assigned:
                final_keys[key] = action
                actions_assigned.add(action)

        # 2. Segundo paso: añadir atajos por defecto que falten
        for key, action in default_keys.items():
            if action not in actions_assigned:
                final_keys[key] = action
                actions_assigned.add(action)

        # 3. Reescribir solo si ha habido cambios
        if final_keys != original_keys:
            new_config = configparser.ConfigParser(interpolation=None)
            new_config['atajos_chat'] = final_keys
            with open(config_path, 'w', encoding='utf-8') as configfile:
                new_config.write(configfile)
        
        self.teclas = final_keys

    def reemplazar(self, old_shortcut, new_shortcut):
        """Reemplaza un atajo existente por uno nuevo."""
        if old_shortcut in self.teclas:
            action = self.teclas[old_shortcut]
            self.del_shortcut(old_shortcut)
            self.add_shortcut(new_shortcut, action)
            self.leerTeclas() # Recargar para mantener consistencia

    def add_shortcut(self, shortcut, action):
        """Agrega un nuevo atajo al archivo de configuración."""
        config = configparser.ConfigParser(interpolation=None)
        config.read("keymaps/keys.txt", encoding='utf-8')
        if 'atajos_chat' not in config:
            config['atajos_chat'] = {}
        config['atajos_chat'][shortcut] = action
        with open("keymaps/keys.txt", 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def del_shortcut(self, shortcut):
        """Elimina un atajo del archivo de configuración."""
        config = configparser.ConfigParser(interpolation=None)
        config.read("keymaps/keys.txt", encoding='utf-8')
        if 'atajos_chat' in config and shortcut in config['atajos_chat']:
            del config['atajos_chat'][shortcut]
            with open("keymaps/keys.txt", 'w', encoding='utf-8') as configfile:
                config.write(configfile)

editor=KeyUtils()