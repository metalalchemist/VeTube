import wx,json,google_currency
from ui.menus.main_menu import MainMenu
from update import updater
from utils.languageHandler import curLang
from ui.ajustes import configuracionDialog
from utils import fajustes, app_utilitys
from ui.dialog_response import response
from globals import data_store
from globals.resources import carpeta_voces,codes,idiomas_disponibles,monedas
from controller.editor_controller import EditorController
from controller.ajustes_controller import AjustesController
from setup import reader,player
from googletrans import LANGUAGES
from servicios.language_updater import GestorRepositorios
from ui.update_languages_dialog import UpdateLanguagesDialog
from controller.update_languages_controller import UpdateLanguagesController
class MainMenuController:
    def __init__(self, frame, main_controller):
        self.frame = frame
        self.main_controller = main_controller
        self.menu = MainMenu(frame)
        self._bind_menu_events()

    def _bind_menu_events(self):
        self.frame.Bind(wx.EVT_MENU, lambda evt: wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+curLang[:2]+'/readme.md'), self.menu.manual)
        self.frame.Bind(wx.EVT_MENU, lambda evt: wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U'), self.menu.apoyo)
        self.frame.Bind(wx.EVT_MENU, lambda evt: wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube'), self.menu.itemPageMain)
        self.frame.Bind(wx.EVT_MENU, self.enlazar_actualizador, self.menu.actualizador)
        self.frame.Bind(wx.EVT_MENU, self.mostrar_acerca_de, self.menu.acercade)
        self.frame.Bind(wx.EVT_MENU, self.mostrar_ajustes, self.menu.opcion_1)
        self.frame.Bind(wx.EVT_MENU, self.restaurar, self.menu.opcion_3)
        self.frame.Bind(wx.EVT_MENU, self.cerrarVentana, self.menu.salir)
        self.frame.Bind(wx.EVT_MENU, self.main_controller.mostrar_editor_combinaciones, self.menu.opcion_0)
        self.frame.Bind(wx.EVT_MENU, self.on_update_languages, self.menu.update_langs)

    def enlazar_actualizador(self, event):
        update = updater.do_update()
        if update == False:
            if self.frame.GetTitle():
                wx.MessageBox(_("Al parecer tienes la última versión del programa"), _( "Información"), wx.ICON_INFORMATION) # type: ignore

    def mostrar_acerca_de(self, event):
        wx.MessageBox(
            _(u"Creadores del proyecto:")+"\nAlejandro Verástegui & Johan Antonio Gutierres.\n"+
            _(u"Descripción:\n Lee en voz alta los mensajes de los directos en youtube, tiktok, twitch y la sala de  juegos, ajusta tus preferencias como quieras y disfruta más tus canales favoritos."),
            _(u"Información"), wx.ICON_INFORMATION
        )

    def mostrar_ajustes(self, event):
        dlg = configuracionDialog(self.frame)
        AjustesController(dlg)
        resultado = dlg.ShowModal()
        if resultado == wx.ID_OK:
            self.config_dialog = dlg  # Guarda la referencia para usarla en guardar()
            self.guardar()
        dlg.Destroy()

    def restaurar(self, event):
        if response(_("Estás apunto de reiniciar la configuración a sus valores predeterminados, ¿Deseas proceder?"), _("Atención:"))==wx.ID_YES:
            fajustes.escribirConfiguracion()
            app_utilitys.restart_program()
    def cerrarVentana(self, event):
        if data_store.config['salir']:
            if response(_("¿está seguro que desea salir del programa?"), _("¡atención!"))==wx.ID_YES: wx.GetApp().ExitMainLoop()
        else: wx.GetApp().ExitMainLoop()

    def on_update_languages(self, event):
        # Hardcode the repo URL for now
        github_repo_url = "metalalchemist/vetube"
        
        # Instantiate the GestorRepositorios
        gestor = GestorRepositorios(self.frame, github_repo=github_repo_url, local_dir=".")
        
        # Check for updates
        result = gestor.comprobar_nuevos_y_actualizaciones()
        
        if not result['success'] and not result.get('error', True): # 'error': False means no updates
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

    def guardar(self):
        cf = self.config_dialog
        data_store.config['categorias'] = [cf.categoriza.IsItemChecked(i) for i in range(cf.categoriza.GetItemCount())]
        data_store.config['listasonidos'] = [cf.soniditos.IsItemChecked(i) for i in range(cf.soniditos.GetItemCount())]
        data_store.config['eventos'] = [cf.eventos.IsItemChecked(i) for i in range(cf.eventos.GetItemCount())]
        data_store.config['unread'] = [cf.unread.IsItemChecked(i) for i in range(cf.unread.GetItemCount())]
        rest = False
        if data_store.config['idioma'] != codes[cf.choice_language.GetSelection()]:
            data_store.config['idioma'] = codes[cf.choice_language.GetSelection()]
            rest = True
        with open('data.json', 'w+', encoding='utf-8') as file:
            json.dump(data_store.config, file, indent=4, ensure_ascii=False)
        if rest:
            if response(_("Es necesario reiniciar el programa para aplicar el nuevo idioma. ¿desea reiniciarlo ahora?"), _("¡Atención!")) == wx.ID_YES:
                app_utilitys.restart_program()
        reader._leer.set_rate(data_store.config['speed'])
        reader._leer.set_pitch(data_store.config['tono'])
        reader._leer.set_voice(reader._leer.list_voices()[data_store.config['voz']])
        reader._leer.set_volume(data_store.config['volume'])
        reader.set_sapi(data_store.config['sapi'])
        if data_store.config['sistemaTTS'] == "piper":
            salida_actual = reader._lector.find_device_id(player.devicenames[data_store.config["dispositivo"]-1])
            reader._lector.set_device(salida_actual)
            app_utilitys.configurar_piper(carpeta_voces)
        if cf.choice_traducir.GetStringSelection()!="":
            for k in LANGUAGES:
                if LANGUAGES[k] == cf.choice_traducir.GetStringSelection():
                    data_store.dst = k
                    break
        if cf.choice_moneditas.GetStringSelection()!='Por defecto':
            monedita=cf.choice_moneditas.GetStringSelection().split(', (')
            for k in google_currency.CODES:
                if google_currency.CODES[k] == monedita[0]:
                    data_store.divisa = k
                    break