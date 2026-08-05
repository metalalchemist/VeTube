# edge_handler: motor de voz de Microsoft Edge (edge-tts).
#
# A diferencia de Piper/Kokoro no hay nada local: las voces viven en el CDN de
# Microsoft y el audio (MP3) se descarga por red con edge_tts. La reproducción
# se hace con sound_lib (BASS) igual que el puente sherpa: el MP3 completo se
# acumula en memoria y se toca con FileStream(mem=True). El volumen y el tono
# se aplican sobre el stream BASS; la velocidad se manda nativa a edge-tts
# (rate='+/-N%').
import asyncio
import threading
import atexit
import ctypes
from edge_tts import Communicate, VoicesManager
from sound_lib import stream

_VOCES = []                # lista caché de voces (dicts de VoicesManager)
_CARGA_EN_CURSO = False
_AL_TERMINAR_CARGA = []    # callbacks a avisar cuando la lista esté lista
_LOOP = None
_THREAD = None
_INSTANCIA = None


def _run_loop():
    asyncio.set_event_loop(_LOOP)
    try:
        _LOOP.run_forever()
    except Exception:
        pass


def _garantizar_loop():
    """Asegura un loop de asyncio corriendo en un hilo propio. Si el hilo
    anterior ya murió (tras close()), levanta uno nuevo."""
    global _LOOP, _THREAD
    if _THREAD is not None and _THREAD.is_alive() and _LOOP is not None:
        return
    _LOOP = asyncio.new_event_loop()
    _THREAD = threading.Thread(target=_run_loop, daemon=True, name="edge-tts")
    _THREAD.start()


async def _fetch_voces():
    global _VOCES, _CARGA_EN_CURSO
    try:
        manager = await VoicesManager.create()
        # Lista nueva (no mutación in place): los lectores no ven una lista a
        # medio llenar mientras la recorren.
        _VOCES = list(manager.voices)
    except Exception as e:
        print(f"No se pudo obtener la lista de voces de Edge TTS: {e}")
    finally:
        _CARGA_EN_CURSO = False
        _avisar_carga()


def _avisar_carga():
    for cb in _AL_TERMINAR_CARGA:
        try:
            cb()
        except Exception:
            pass
    _AL_TERMINAR_CARGA.clear()


def edge_iniciar_carga(on_listo=None):
    """Dispara en segundo plano la descarga de la lista de voces. on_listo se
    llama (desde el hilo del loop) cuando la lista está disponible; el llamante
    debe llevarlo al hilo de la UI (wx.CallAfter) si va a tocar widgets."""
    global _CARGA_EN_CURSO
    _garantizar_loop()
    if on_listo is not None:
        _AL_TERMINAR_CARGA.append(on_listo)
    if _VOCES:
        _avisar_carga()
        return
    if _CARGA_EN_CURSO:
        return
    _CARGA_EN_CURSO = True
    asyncio.run_coroutine_threadsafe(_fetch_voces(), _LOOP)


def edge_voces_listas():
    return bool(_VOCES)


def edge_list_voices():
    """Nombres cortos de todas las voces (ShortName), en el orden del CDN."""
    return [v["ShortName"] for v in _VOCES]


def edge_idiomas_disponibles():
    """Códigos de idioma (2 letras) que trae el catálogo, sin repetir."""
    codigos = []
    for v in _VOCES:
        lang = v.get("Language") or ""
        if lang and lang not in codigos:
            codigos.append(lang)
    return sorted(codigos)


def edge_voces_de_idioma(codigo=None):
    """[(índice, ShortName)] de las voces de un idioma, o de todas si no se
    pasa ninguno. El índice es el global de _VOCES, el que se guarda en
    config['voz']: una lista filtrada NO puede indexarse sola."""
    return [(i, v["ShortName"]) for i, v in enumerate(_VOCES)
            if codigo is None or (v.get("Language") or "") == codigo]


def edge_idioma_de_voz(index):
    if 0 <= index < len(_VOCES):
        return _VOCES[index].get("Language")
    return None


def edge_voz_shortname(index):
    """Nombre corto de la voz que ocupa ese índice global, o None."""
    if 0 <= index < len(_VOCES):
        return _VOCES[index]["ShortName"]
    return None


class edgeSpeak:
    def __new__(cls, *args, **kwargs):
        global _INSTANCIA
        if _INSTANCIA is None:
            _INSTANCIA = super(edgeSpeak, cls).__new__(cls)
            _INSTANCIA._inicializado = False
        return _INSTANCIA

    def __init__(self, model_path=None):
        if self._inicializado:
            if model_path:
                self.load_model(model_path)
            return
        self.device = -1  # dispositivo por defecto de BASS
        self.volume = 100
        # Tono por re-muestreo sobre el stream BASS (misma técnica que sherpa):
        # ratio = 1 + 0.05 * slider (-10 a 10 -> 0.5x a 2x).
        self.pitch_ratio = 1.0
        # Velocidad nativa de edge-tts: porcentaje relativo a la normal.
        self.rate_pct = 0
        self.current_voice = None   # ShortName de la voz elegida
        self.bass_stream = None
        self._mp3_buffer = None
        # silence() incrementa la generación para invalidar síntesis en curso.
        self._speak_generation = 0
        self._sintetizando = False

        _garantizar_loop()
        atexit.register(self.close)

        if model_path:
            self.load_model(model_path)
        self._inicializado = True

    def get_devices(self):
        try:
            from sound_lib.output import Output
            o = Output()
            return [{'name': name, 'id': i} for i, name in enumerate(o.get_device_names())]
        except Exception:
            return []

    def find_device_id(self, term, known_devices=None):
        try:
            devices = known_devices if known_devices is not None else self.get_devices()
            for device in devices:
                if device['name'] == term:
                    return device['id']
        except Exception:
            pass
        return -1

    def set_rate(self, value):
        # value = velocidad del slider (-10 a 10). edge-tts espera '+/-N%'.
        self.rate_pct = int(round(value * 5))
        if self.rate_pct < -100:
            self.rate_pct = -100
        if self.rate_pct > 100:
            self.rate_pct = 100

    def set_pitch(self, value):
        ratio = 1.0 + (value * 0.05)
        if ratio < 0.5:
            ratio = 0.5
        if ratio > 2.0:
            ratio = 2.0
        self.pitch_ratio = ratio

    def set_volume(self, value):
        self.volume = int(value)
        if self.volume < 0:
            self.volume = 0
        if self.volume > 100:
            self.volume = 100

    def set_device(self, device):
        self.device = device

    def is_multispeaker(self):
        return False

    def load_model(self, model_path=None):
        # En Edge la «voz» es el ShortName: no hay modelo local que cargar.
        if model_path:
            self.current_voice = model_path

    def unload_model(self):
        self.current_voice = None

    def speak(self, text):
        if not text:
            return
        if not self.current_voice:
            return
        self.silence()
        self._sintetizando = True
        asyncio.run_coroutine_threadsafe(
            self._speak_task(text, self._speak_generation), _LOOP)

    def silence(self):
        # Invalida cualquier síntesis en curso y corta el audio actual.
        self._speak_generation += 1
        self._sintetizando = False
        if self.bass_stream is not None:
            try:
                self.bass_stream.stop()
                self.bass_stream.free()
            except Exception:
                pass
            self.bass_stream = None
            self._mp3_buffer = None

    def is_playing(self):
        # True mientras se sintetiza o suena (botón «Detener prueba»).
        if self._sintetizando:
            return True
        s = self.bass_stream
        if s is None:
            return False
        try:
            return bool(s.is_playing)
        except Exception:
            return False

    async def _speak_task(self, text, gen):
        try:
            await self._speak_task_inner(text, gen)
        finally:
            # Solo la síntesis vigente apaga el indicador: una tarea vieja
            # invalidada por silence() no debe pisar el estado de la nueva.
            if gen == self._speak_generation:
                self._sintetizando = False

    async def _speak_task_inner(self, text, gen):
        voz = self.current_voice
        if not voz:
            return
        rate = f"{self.rate_pct:+d}%"
        communicate = Communicate(text, voz, rate=rate)
        # edge-tts devuelve el audio en MP3: se acumula entero en memoria.
        mp3 = bytearray()
        async for chunk in communicate.stream():
            if gen != self._speak_generation:
                return  # silenciado mientras se descargaba
            if chunk["type"] == "audio":
                mp3.extend(chunk["data"])
        if gen != self._speak_generation or not mp3:
            return
        datos = bytes(mp3)
        # BASS no copia el buffer de memoria: hay que mantener vivo el ctypes.
        cdata = ctypes.create_string_buffer(datos, len(datos))
        local_stream = stream.FileStream(mem=True, file=ctypes.addressof(cdata),
                                         offset=0, length=len(datos), autofree=False)
        local_stream.volume = self.volume / 100.0
        if self.pitch_ratio != 1.0:
            try:
                local_stream.set_frequency(
                    int(local_stream.get_frequency() * self.pitch_ratio))
            except Exception:
                pass
        if self.device != -1:
            try:
                local_stream.set_device(self.device)
            except Exception:
                pass
        if gen != self._speak_generation:
            try:
                local_stream.free()
            except Exception:
                pass
            return
        self._mp3_buffer = cdata
        self.bass_stream = local_stream
        local_stream.play()

    def close(self):
        self.silence()
        try:
            if _LOOP is not None and _LOOP.is_running():
                _LOOP.call_soon_threadsafe(_LOOP.stop)
        except Exception:
            pass
        self._inicializado = False
