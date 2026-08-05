import wx
import asyncio
from ui.menus.main_menu import MainMenu
from update import updater
from utils.languageHandler import curLang
from ui.ajustes import configuracionDialog
from utils import fajustes, app_utilitys
from ui.dialog_response import response
from globals import data_store
from globals.resources import carpeta_voces,codes,codigos_traduccion
from controller.editor_controller import EditorController
from setup import network, reader
from exchange import codes as currency_codes
from servicios.language_updater import GestorRepositorios
from ui.update_languages_dialog import UpdateLanguagesDialog
from controller.update_languages_controller import UpdateLanguagesController
from controller.kokoro_downloader_controller import KokoroDownloaderController
from TTS.sherpa_handler import kokoro_model_instalado
class MainMenuController:
    def __init__(self, frame, main_controller):
        self.frame = frame
        self.main_controller = main_controller
        self.menu = MainMenu(frame)
        self.checking_languages = False
        self._bind_menu_events()

    def _bind_menu_events(self):
        self.frame.Bind(wx.EVT_MENU, lambda evt: wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+curLang[:2]+'/readme.md'), self.menu.manual)
        self.frame.Bind(wx.EVT_MENU, lambda evt: wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U'), self.menu.apoyo)
        self.frame.Bind(wx.EVT_MENU, lambda evt: wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube'), self.menu.itemPageMain)
        self.frame.Bind(wx.EVT_MENU, lambda evt: updater.do_update(is_manual=True), self.menu.actualizador)
        self.frame.Bind(wx.EVT_MENU, self.mostrar_acerca_de, self.menu.acercade)
        self.frame.Bind(wx.EVT_MENU, self.mostrar_ajustes, self.menu.opcion_1)
        self.frame.Bind(wx.EVT_MENU, self.restaurar, self.menu.opcion_3)
        self.frame.Bind(wx.EVT_MENU, self.cerrarVentana, self.menu.salir)
        self.frame.Bind(wx.EVT_MENU, self.main_controller.mostrar_editor_combinaciones, self.menu.opcion_0)
        self.frame.Bind(wx.EVT_MENU, self.on_update_languages, self.menu.update_langs)

    def mostrar_acerca_de(self, event):
        wx.MessageBox(
            _(u"Creadores del proyecto:")+"\nAlejandro Verástegui & Johan G.\n"+
            _(u"Descripción:\n Lee en voz alta los mensajes de los directos en youtube, tiktok, twitch, kick y la sala de  juegos, ajusta tus preferencias como quieras y disfruta más tus canales favoritos."),
            "VeTube "+str(updater.VERSION), wx.ICON_INFORMATION
        )

    def mostrar_ajustes(self, event):
        dlg = configuracionDialog(self.frame)
        resultado = dlg.ShowModal()
        try:
            if resultado == wx.ID_OK:
                self.config_dialog = dlg  # Guarda la referencia para usarla en guardar()
                self.guardar()
            else:
                dlg.ajustes_controller.revertir_cambios_en_caliente()
        finally:
            dlg.Destroy()
        # Pedido de César (2026-08-01): al Aceptar con Kokoro elegido y sin el
        # modelo en el equipo, ofrecer la descarga en el acto — así el paquete
        # de 334 MB solo lo baja quien de verdad va a usar estas voces.
        if resultado == wx.ID_OK and data_store.config['sistemaTTS'] == "kokoro" and not kokoro_model_instalado():
            KokoroDownloaderController(self.frame).show()

    def restaurar(self, event):
        if response(_("Estás apunto de reiniciar la configuración a sus valores predeterminados, ¿Deseas proceder?"), _("Atención:"))==wx.ID_YES:
            fajustes.escribirConfiguracion()
            app_utilitys.restart_program()
    def cerrarVentana(self, event):
        if data_store.config['salir']:
            if response(_("¿está seguro que desea salir del programa?"), _("¡atención!"))==wx.ID_YES: wx.GetApp().ExitMainLoop()
        else: wx.GetApp().ExitMainLoop()

    def on_update_languages(self, event):
        if self.checking_languages:
            # Aviso audible: sin él, con un lector de pantalla no se distingue
            # "ya está en curso" de "no ha pasado nada".
            wx.MessageBox(_("Ya hay una comprobación de idiomas en curso."), _("Actualización de idiomas"), wx.ICON_INFORMATION)
            return
        self.checking_languages = True
        gestor = GestorRepositorios(self.frame, github_repo="metalalchemist/vetube", local_dir=".")
        def handle_result(result):
            self.checking_languages = False
            if isinstance(result, Exception):
                wx.MessageBox(_("Error al conectar con el servidor de idiomas: {}").format(result), _("Error de red"), wx.ICON_ERROR)
            else:
                self._handle_language_check_result(gestor, result)

        network.execute(gestor.comprobar_nuevos_y_actualizaciones(), callback=handle_result)

    def _handle_language_check_result(self, gestor, result):
        if not result['success'] and not result.get('error', True): 
            wx.MessageBox(result['data'], _("Actualización de idiomas"), wx.ICON_INFORMATION)
        elif result['success']:
            nuevos = result['data'].get('nuevos', {})
            actualizaciones = result['data'].get('actualizaciones', {})
            
            if nuevos or actualizaciones:
                # Use the new controller
                update_controller = UpdateLanguagesController(self.frame, gestor, result['data'])
                update_controller.show()
                update_controller.close() # This will be called after ShowModal returns
            else:
                wx.MessageBox(_("No hay actualizaciones ni nuevos idiomas disponibles."), _("Actualización de idiomas"), wx.ICON_INFORMATION)
        else: # An actual error occurred
            wx.MessageBox(result['data'], _("Error de actualización"), wx.ICON_ERROR)

    def comprobar_idiomas_al_inicio(self):
        """Comprobación silenciosa al arrancar: solo pregunta cuando el idioma
        activo tiene algo que instalar. Los fallos (sin red, servidor caído) y
        el caso sin novedades se callan, porque el usuario no pidió nada y la
        opción manual del menú de ayuda sigue disponible."""
        if self.checking_languages: return
        self.checking_languages = True
        gestor = GestorRepositorios(self.frame, github_repo="metalalchemist/vetube", local_dir=".")

        def handle_result(result):
            self.checking_languages = False
            if isinstance(result, Exception) or not result['success']: return
            data = result['data']
            idioma_activo = curLang[:2]
            if idioma_activo not in data.get('nuevos', {}) and idioma_activo not in data.get('actualizaciones', {}): return
            self._preguntar_actualizar_idioma(gestor, data)

        # El cliente de red central no tiene timeout: sin este límite, una
        # petición colgada dejaría el cerrojo tomado toda la sesión y la
        # opción del menú quedaría muda.
        network.execute(asyncio.wait_for(gestor.comprobar_nuevos_y_actualizaciones(), 30), callback=handle_result)

    def _preguntar_actualizar_idioma(self, gestor, data):
        # Mientras la comprobación de actualización del programa siga activa
        # (incluido su diálogo de "nueva versión"), esperar: dos diálogos a la
        # vez se roban el foco y una pulsación perdida aceptaría una descarga.
        if updater.buscando:
            wx.CallLater(2000, self._preguntar_actualizar_idioma, gestor, data)
            return
        if response(_("Hay una actualización disponible para el idioma del programa. ¿Quieres instalarla ahora?"), _("Actualización de idiomas")) == wx.ID_YES:
            update_controller = UpdateLanguagesController(self.frame, gestor, data)
            update_controller.show()
            update_controller.close()

    def guardar(self):
        cf = self.config_dialog
        data_store.config['categorias'] = [cf.categoriza.IsItemChecked(i) for i in range(cf.categoriza.GetItemCount())]
        data_store.config['listasonidos'] = [cf.soniditos.IsItemChecked(i) for i in range(cf.soniditos.GetItemCount())]
        data_store.config['eventos'] = [cf.eventos.IsItemChecked(i) for i in range(cf.eventos.GetItemCount())]
        data_store.config['unread'] = [cf.unread.IsItemChecked(i) for i in range(cf.unread.GetItemCount())]
        data_store.config['leer_historial'] = cf.check_historial.IsChecked()
        seleccion_traduccion = cf.choice_traducir.GetSelection()
        # La traducción no es persistente: solo aplica a la sesión actual, no se guarda en la configuración
        data_store.dst = codigos_traduccion[seleccion_traduccion] if seleccion_traduccion != wx.NOT_FOUND else ""
        rest = False
        if data_store.config['idioma'] != codes[cf.choice_language.GetSelection()]:
            data_store.config['idioma'] = codes[cf.choice_language.GetSelection()]
            rest = True
        fajustes.guardarConfiguracion(data_store.config)
        if rest:
            if response(_("Es necesario reiniciar el programa para aplicar el nuevo idioma. ¿desea reiniciarlo ahora?"), _("¡Atención!")) == wx.ID_YES:
                app_utilitys.restart_program()
        reader._leer.set_rate(data_store.config['speed'])
        reader._leer.set_pitch(data_store.config['tono'])
        reader._leer.set_volume(data_store.config['volume'])
        voices_leer = reader._leer.list_voices()
        if voices_leer:
            idx = data_store.config['voz']
            if idx >= len(voices_leer): idx = 0
            reader._leer.set_voice(voices_leer[idx])
        
        if data_store.config['sistemaTTS'] in ("piper", "kokoro"):
            # El puente sherpa usa la escala porcentaje_a_escala y no expone list_voices
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(data_store.config['speed']))
            reader._lector.set_pitch(data_store.config['tono'])
            reader._lector.set_volume(data_store.config['volume'])
        elif data_store.config['sistemaTTS'] == "edge":
            # Edge: la velocidad va nativa (-10 a 10) a edge-tts
            reader._lector.set_rate(data_store.config['speed'])
            reader._lector.set_pitch(data_store.config['tono'])
            reader._lector.set_volume(data_store.config['volume'])
        else:
            reader._lector.set_rate(data_store.config['speed'])
            if data_store.config['sistemaTTS'] == "onecore":
                reader._lector.set_pitch(data_store.config.get('tono_onecore', 0.6))
            else:
                reader._lector.set_pitch(data_store.config['tono'])
            reader._lector.set_volume(data_store.config['volume'])
            voices_lector = reader._lector.list_voices()
            if voices_lector:
                idx = data_store.config['voz']
                if idx >= len(voices_lector): idx = 0
                reader._lector.set_voice(voices_lector[idx])

        reader.set_sapi(data_store.config['sapi'])
        if data_store.config['sistemaTTS'] in ("piper", "kokoro"):
            app_utilitys.fijar_dispositivo_lector()
            if data_store.config['sistemaTTS'] == "piper":
                app_utilitys.configurar_piper(self.frame, carpeta_voces)
        elif data_store.config['sistemaTTS'] == "edge":
            app_utilitys.fijar_dispositivo_lector()
        if cf.choice_moneditas.GetStringSelection()!='Por defecto':
            monedita=cf.choice_moneditas.GetStringSelection().split(', (')
            for k in currency_codes.CODES:
                if currency_codes.CODES[k] == monedita[0]:
                    data_store.divisa = k
                    break