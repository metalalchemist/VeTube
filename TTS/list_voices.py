import os
import tarfile
from .lector import detect_onnx_models
from . import sonata_handler as speaker
import wx
def extract_tar(file, destination):
	if not os.path.exists(destination):
		os.makedirs(destination)
	try:
		with tarfile.open(file, 'r:gz') as tar:
			tar.extractall(destination)
	except tarfile.ReadError:
		with tarfile.open(file, 'r:') as tar:
			tar.extractall(destination)

def install_piper_voice(config, reader):
	abrir_tar = wx.FileDialog(None, _("Selecciona un paquete de voz"), wildcard=_("Archivos tar.gz (*.tar.gz)|*.tar.gz"), style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
	if abrir_tar.ShowModal() == wx.ID_CANCEL:
		wx.MessageBox(_('Para usar piper como sistema TTS, necesitas tener al menos una voz. Si quieres hacerlo de forma manual, extrae el paquete de voz en la carpeta "voices/voice-nombre_de_paquete" en VeTube.'), _("No se instaló ninguna voz"), wx.ICON_ERROR)
		return False
	paquete = abrir_tar.GetPath()
	nombre_paquete = os.path.splitext(os.path.basename(paquete))[0]
	destino = os.path.join(os.getcwd(), "voices", nombre_paquete[:-3])
	extract_tar(paquete, destino)
	wx.MessageBox(_("¡Voz instalada satosfactoriamente! esta será establecida en VeTube ahora. Para cambiar de modelo de voz, puedes hacerlo a través de las configuraciones."), _("Listo"), wx.ICON_INFORMATION)
	reader=speaker.piperSpeak(f"{destino}/{nombre_paquete}.onnx")
	config['voz'] = 0
	abrir_tar.Destroy()
	return config, reader

def piper_list_voices():
	if not os.path.exists("voices"):
		return []
	folders = [f for f in os.listdir("voices") if os.path.isdir(os.path.join("voices", f)) and f.startswith("voice-")]
	valid_folders = []
	for folder in folders:
		folder_path = os.path.join("voices", folder)
		import glob
		onnx_files = glob.glob(os.path.join(folder_path, "*.onnx"))
		if onnx_files:
			valid_folders.append(folder)
	return valid_folders

def obtener_ruta_voz(nombre_carpeta):
	if not nombre_carpeta:
		return None
	# Si ya es una ruta completa/relativa a un archivo, la devolvemos directamente
	if nombre_carpeta.endswith(".onnx") or nombre_carpeta.endswith(".json"):
		return nombre_carpeta
		
	folder_path = os.path.join("voices", nombre_carpeta)
	import glob
	# Si es una voz RT, priorizamos decoder.onnx
	rt_decoder = os.path.join(folder_path, "decoder.onnx")
	if os.path.exists(rt_decoder):
		return rt_decoder
	# Si no, buscamos cualquier archivo .onnx en la carpeta
	onnx_files = glob.glob(os.path.join(folder_path, "*.onnx"))
	if onnx_files:
		return onnx_files[0]
	return None
