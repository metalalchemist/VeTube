import wx
import setup
from globals.data_store import config
from controller.main_controller import MainController
from update import updater,update
def run_app():
    app = wx.App(False)
    if config['donations']:
        update.donation()
    if config.get('updates', False):
        updater.do_update()
    name = 'vetube-instance-checker'
    instance = wx.SingleInstanceChecker(name)
    if instance.IsAnotherRunning():
        wx.MessageBox(_('VeTube ya se encuentra en ejecución. Cierra la otra instancia antes de iniciar esta.'), 'Error', wx.ICON_ERROR)
        return
    MainController()
    app.MainLoop()
run_app()