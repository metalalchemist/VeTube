import wx
from ui.menus.main_menu import MainMenu
from update import updater
from utils.languageHandler import curLang
from ui.ajustes import configuracionDialog
from utils import fajustes, app_utilitys
from ui.dialog_response import response
from globals.data_store import config
from ui.editor.editor import EditorCombinaciones
from controller.ajustes_controller import AjustesController

class MainMenuController:
    def __init__(self, frame):
        self.frame = frame
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
        self.frame.Bind(wx.EVT_MENU, self.mostrar_editor_combinaciones, self.menu.opcion_0)

    def enlazar_actualizador(self, event):
        update = updater.do_update()
        if update == False:
            if self.frame.GetTitle():
                wx.MessageBox(_("Al parecer tienes la última versión del programa"), _( "Información"), wx.ICON_INFORMATION) # type: ignore

    def mostrar_acerca_de(self, event):
        wx.MessageBox(
            _(u"Creadores del proyecto:")+"\nCésar Verástegui & Johan G.\n"+
            _(u"Descripción:\n Lee en voz alta los mensajes de los directos en youtube, tiktok, twitch y la sala de  juegos, ajusta tus preferencias como quieras y disfruta más tus canales favoritos."),
            _(u"Información"), wx.ICON_INFORMATION
        )

    def mostrar_ajustes(self, event):
        dlg = configuracionDialog(self.frame)
        AjustesController(dlg)
        dlg.ShowModal()
        dlg.Destroy()

    def restaurar(self, event):
        if response(_("Estás apunto de reiniciar la configuración a sus valores predeterminados, ¿Deseas proceder?"), _("Atención:"))==wx.ID_YES:
            fajustes.escribirConfiguracion()
            app_utilitys.restart_program()
    def cerrarVentana(self, event):
        if config['salir']:
            if response(_("¿está seguro que desea salir del programa?"), _("¡atención!"))==wx.ID_YES: wx.GetApp().ExitMainLoop()
        else: wx.GetApp().ExitMainLoop()

    def mostrar_editor_combinaciones(self, event):
        dlg = EditorCombinaciones(self.frame)
        dlg.ShowModal()
