import os
import tarfile
from .lector import detect_onnx_models
from .Piper import speaker
import wx
def extract_tar(file, destination):
	if not os.path.exists(destination):
		os.makedirs(destination)
	with tarfile.open(file, 'r:gz') as tar:
		tar.extractall(destination)

def install_piper_voice(config, reader):
	abrir_tar = wx.FileDialog(None, _("Selecciona un paquete de voz"), wildcard=_("Archivos tar.gz (*.tar.gz)|*.tar.gz"), style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
	if abrir_tar.ShowModal() == wx.ID_CANCEL:
		wx.MessageBox(_('Para usar piper como sistema TTS, necesitas tener al menos una voz. Si quieres hacerlo de forma manual, extrae el paquete de voz en la carpeta "piper/voices/voice-nombre_de_paquete" en VeTube.'), _("No se instaló ninguna voz"), wx.ICON_ERROR)
		return
	paquete = abrir_tar.GetPath()
	nombre_paquete = os.path.splitext(os.path.basename(paquete))[0]
	destino = os.path.join(os.getcwd(), "piper", "voices", nombre_paquete[:-3])
	extract_tar(paquete, destino)
	wx.MessageBox(_("¡Voz instalada satosfactoriamente! esta será establecida en VeTube ahora. Para cambiar de modelo de voz, puedes hacerlo a través de las configuraciones."), _("Listo"), wx.ICON_INFORMATION)
	reader=speaker.piperSpeak(f"{destino}/{nombre_paquete}.onnx")
	config['voz'] = 0
	abrir_tar.Destroy()
	return config, reader

def piper_list_voices():
	voice_list = detect_onnx_models("piper/voices")
	# fix paths:
	if isinstance(voice_list, str):
		voice_list = [os.path.basename(voice_list)]
	elif isinstance(voice_list, list):
		voice_list = [os.path.basename(path) for path in voice_list]
	return voice_list