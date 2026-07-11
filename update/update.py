from logging import getLogger
import json
from utils import languageHandler
import contextlib
import io
import os
import sys
import platform
import httpx
import tempfile
try:
    import czipfile as zipfile
except ImportError:
    import zipfile
import wx
from platform_utils import paths
from utils.translator import TranslatorWrapper
from setup import network
logger = getLogger('update')

def perform_update(update_url, donations=True, password=None, progress_callback=None, update_complete_callback=None):
    base_path = tempfile.mkdtemp()
    download_path = os.path.join(base_path, 'update.zip')
    update_path = os.path.join(base_path, 'update')
    
    # perform_update corre en un hilo aparte (updater.py); el diálogo va al hilo de la UI
    if donations: wx.CallAfter(donation)
    
    with httpx.Client(follow_redirects=True, timeout=None) as client:
        downloaded = download_update(update_url, download_path, client=client, progress_callback=progress_callback)
    
    extracted = extract_update(downloaded, update_path, password=password)
    bootstrap_path = move_bootstrap(extracted)
    if callable(update_complete_callback):
        update_complete_callback()
    execute_bootstrap(bootstrap_path, extracted)
    logger.info("Update prepared for installation.")

async def async_check_update(endpoint, current_version):
    try:
        if os.path.exists("data.json"):
            with open ("data.json") as file: resultado=json.load(file)
            donations = resultado.get('donations', True)
            traducir = resultado.get('traducir', False)
        else:
            donations = True
            traducir = False

        response = await network.client.get(endpoint)
        response.raise_for_status()
        available_update = response.json()
        
        available_version = available_update['current_version']
        arch_key = platform.system() + platform.architecture()[0][:2]
        
        if available_version == current_version or arch_key not in available_update['downloads']:
            logger.debug("No update available or not for this architecture")
            return None
            
        if not traducir:
            available_description = available_update.get('description', None)
        else:
            translator = TranslatorWrapper()
            available_description = translator.translate(available_update.get('description', None), target=languageHandler.curLang[:2])
            
        update_url = available_update['downloads'][arch_key]
        
        return {
            'update_url': update_url,
            'available_version': available_version,
            'available_description': available_description,
            'donations': donations
        }
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return None

def download_update(update_url, update_destination, client, progress_callback=None, chunk_size=128*1024):
    total_downloaded = 0
    last_percent = -1
    with io.open(update_destination, 'w+b') as outfile:
        with client.stream("GET", update_url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            logger.debug("Total update size: %d" % total_size)
            for chunk in response.iter_bytes(chunk_size):
                outfile.write(chunk)
                total_downloaded += len(chunk)
                if callable(progress_callback) and total_size > 0:
                    percent = int((total_downloaded * 100) / total_size)
                    if percent > last_percent:
                        last_percent = percent
                        call_callback(progress_callback, total_downloaded, total_size)
    logger.debug("Update downloaded")
    return update_destination

def extract_update(update_archive, destination, password=None):
    """Given an update archive, extracts it. Returns the directory to which it has been extracted"""
    with contextlib.closing(zipfile.ZipFile(update_archive)) as archive:
        if password:
            archive.setpassword(password)
        archive.extractall(path=destination)
    logger.debug("Update extracted")
    return destination

def move_bootstrap(extracted_path):
    working_path = os.path.abspath(os.path.join(extracted_path, '..'))
    if platform.system() == 'Darwin':
        extracted_path = os.path.join(extracted_path, 'Contents', 'Resources')
    downloaded_bootstrap = os.path.join(extracted_path, bootstrap_name())
    new_bootstrap_path = os.path.join(working_path, bootstrap_name())
    os.rename(downloaded_bootstrap, new_bootstrap_path)
    return new_bootstrap_path

def execute_bootstrap(bootstrap_path, source_path):
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen: dest_path = os.path.dirname(sys.executable)
    else: dest_path = os.path.abspath(os.path.join(paths.app_path()))
    arguments = r'"%s" "%s" "%s" "%s"' % (os.getpid(), source_path, dest_path, paths.get_executable())
    if platform.system() == 'Windows':
        import win32api
        win32api.ShellExecute(0, 'open', bootstrap_path, arguments, '', 5)
    else:  
        import subprocess
        make_executable(bootstrap_path)
        subprocess.Popen(['%s %s' % (bootstrap_path, arguments)], shell=True)
    logger.info("Bootstrap executed")

def bootstrap_name():
    if platform.system() == 'Windows': return 'bootstrap.exe'
    if platform.system() == 'Darwin': return 'bootstrap-mac.sh'
    return 'bootstrap-lin.sh'

def make_executable(path):
    import stat
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def call_callback(callback, *args, **kwargs):
    # try:
    callback(*args, **kwargs)
# except:
#  logger.exception("Failed calling callback %r with args %r and kwargs %r" % (callback, args, kwargs))
def donation():
    dlg = wx.MessageDialog(None, _("Con tu apoyo contribuyes a que este programa siga siendo gratuito. ¿Te unes a nuestra causa?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
    dlg.SetYesNoLabels(_("&Aceptar"), _("&Cancelar"))
    if dlg.ShowModal()==wx.ID_YES: wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U')

