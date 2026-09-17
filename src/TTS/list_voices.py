import os
import tarfile

import wx

from globals.paths import VOICES_DIR

from . import sonata_handler as speaker


def extract_tar(file, destination):
    if not os.path.exists(destination):
        os.makedirs(destination)
    try:
        with tarfile.open(file, "r:gz") as tar:
            tar.extractall(destination)
    except tarfile.ReadError:
        with tarfile.open(file, "r:") as tar:
            tar.extractall(destination)


def install_piper_voice(config, reader):
    abrir_tar = wx.FileDialog(
        None,
        _("Selecciona un paquete de voz"),
        wildcard=_("Archivos tar.gz (*.tar.gz)|*.tar.gz"),
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
    )
    if abrir_tar.ShowModal() == wx.ID_CANCEL:
        wx.MessageBox(
            _(
                'Para usar piper como sistema TTS, necesitas tener al menos una voz. Si quieres hacerlo de forma manual, extrae el paquete de voz en la carpeta "voices/voice-nombre_de_paquete" en VeTube.'
            ),
            _("No se instaló ninguna voz"),
            wx.ICON_ERROR,
        )
        return False
    paquete = abrir_tar.GetPath()
    nombre_paquete = os.path.splitext(os.path.basename(paquete))[0]
    destino = str(VOICES_DIR / nombre_paquete[:-3])
    extract_tar(paquete, destino)
    wx.MessageBox(
        _(
            "¡Voz instalada satosfactoriamente! esta será establecida en VeTube ahora. Para cambiar de modelo de voz, puedes hacerlo a través de las configuraciones."
        ),
        _("Listo"),
        wx.ICON_INFORMATION,
    )
    reader = speaker.piperSpeak(f"{destino}/{nombre_paquete}.onnx")
    config["voz"] = 0
    abrir_tar.Destroy()
    return config, reader


def es_voz_rt(nombre_carpeta):
    """True si la voz instalada es la variante rápida (RT). Las dos variantes
    crean una carpeta con el MISMO nombre, así que sin mirar dentro no hay
    forma de distinguirlas: la RT es la que trae el modelo partido en
    encoder.onnx + decoder.onnx."""
    return (VOICES_DIR / nombre_carpeta / "decoder.onnx").exists()


# encoder.onnx no es un punto de entrada: es la mitad del modelo partido de las
# voces RT, y el fichero que carga sonata es decoder.onnx (mismo criterio que
# detect_onnx_models en lector.py). Contarlo como voz deja al usuario eligiendo
# en Ajustes una entrada que no carga nada y sin ningún aviso.
_ONNX_NO_CARGABLE = ("encoder.onnx",)


def _modelos_cargables(folder_path):
    """Los .onnx de una carpeta de voz que sirven como punto de entrada."""
    return [
        m for m in folder_path.glob("*.onnx") if m.name.lower() not in _ONNX_NO_CARGABLE
    ]


def piper_list_voices():
    if not VOICES_DIR.exists():
        return []
    folders = [
        f.name
        for f in VOICES_DIR.iterdir()
        if f.is_dir() and f.name.startswith("voice-")
    ]
    valid_folders = []
    for folder in folders:
        if _modelos_cargables(VOICES_DIR / folder):
            valid_folders.append(folder)
    return valid_folders


def obtener_ruta_voz(nombre_carpeta):
    if not nombre_carpeta:
        return None
    # Si ya es una ruta completa/relativa a un archivo, la devolvemos directamente
    if nombre_carpeta.endswith(".onnx") or nombre_carpeta.endswith(".json"):
        return nombre_carpeta

    folder_path = VOICES_DIR / nombre_carpeta
    # Si es una voz RT, priorizamos decoder.onnx
    rt_decoder = folder_path / "decoder.onnx"
    if rt_decoder.exists():
        return str(rt_decoder)
    # Si no, buscamos cualquier archivo .onnx cargable de la carpeta
    onnx_files = _modelos_cargables(folder_path)
    if onnx_files:
        return str(onnx_files[0])
    return None
