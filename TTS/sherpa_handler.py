import os
import sys
import json
import asyncio
import subprocess
import socket
import threading
import atexit
import ctypes
from pathlib import Path
from sound_lib import stream
from grpclib.client import Channel
import grpclib.const

# Servidor TTS nativo: ejecutable Rust + sherpa-onnx (C-API oficial), proceso
# separado sin Python ni numpy (el arranque de VeTube nunca depende de él,
# incluso en CPUs antiguas sin AVX). Habla el mismo protocolo sonata_grpc que
# el antiguo servidor de Piper y sintetiza AMBOS motores: las voces Piper del
# catálogo rhasspy y el modelo Kokoro. Un solo proceso residente para los dos.
_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN_PUENTE = _BASE_DIR / "64" / "sherpa"
EXE_PUENTE = str(BIN_PUENTE / "vetube-sherpa-grpc.exe")
NOMBRE_EXE_PUENTE = "vetube-sherpa-grpc.exe"

# Modelo Kokoro local: vive en voices/ junto a las voces de Piper y lo instala
# el descargador propio (servicios/kokoro_manager.py, release tts-models de k2-fsa).
KOKORO_MODEL_DIR = os.path.join("voices", "kokoro-multi-lang-v1_0")

def kokoro_model_instalado():
    """True si el modelo está instalado y completo (el descargador solo mueve la
    carpeta a voices/ tras verificarla, así que basta con el fichero principal)."""
    return os.path.isfile(os.path.join(KOKORO_MODEL_DIR, "model.onnx"))

# Voces del modelo: (etiqueta para la UI, sid, idioma espeak para la fonemización).
# Mapeo de sid = tabla oficial del modelo kokoro-multi-lang-v1_0 en la doc de
# sherpa-onnx (¡no es el orden de hexgrad: em_santa no existe aquí!). Las tres
# primeras conservan su posición histórica para no invalidar config['voz'] de
# instalaciones existentes; el resto va en orden de sid.
VOCES_KOKORO = [
    ("ff_siwis (francés)", 30, "fr"),
    ("ef_dora (español)", 28, "es"),
    ("em_alex (español)", 29, "es"),
    # Inglés de EE. UU. (af_ = mujer, am_ = hombre)
    ("af_alloy (inglés)", 0, "en-us"),
    ("af_aoede (inglés)", 1, "en-us"),
    ("af_bella (inglés)", 2, "en-us"),
    ("af_heart (inglés)", 3, "en-us"),
    ("af_jessica (inglés)", 4, "en-us"),
    ("af_kore (inglés)", 5, "en-us"),
    ("af_nicole (inglés)", 6, "en-us"),
    ("af_nova (inglés)", 7, "en-us"),
    ("af_river (inglés)", 8, "en-us"),
    ("af_sarah (inglés)", 9, "en-us"),
    ("af_sky (inglés)", 10, "en-us"),
    ("am_adam (inglés)", 11, "en-us"),
    ("am_echo (inglés)", 12, "en-us"),
    ("am_eric (inglés)", 13, "en-us"),
    ("am_fenrir (inglés)", 14, "en-us"),
    ("am_liam (inglés)", 15, "en-us"),
    ("am_michael (inglés)", 16, "en-us"),
    ("am_onyx (inglés)", 17, "en-us"),
    ("am_puck (inglés)", 18, "en-us"),
    ("am_santa (inglés)", 19, "en-us"),
    # Inglés británico
    ("bf_alice (inglés británico)", 20, "en-gb"),
    ("bf_emma (inglés británico)", 21, "en-gb"),
    ("bf_isabella (inglés británico)", 22, "en-gb"),
    ("bf_lily (inglés británico)", 23, "en-gb"),
    ("bm_daniel (inglés británico)", 24, "en-gb"),
    ("bm_fable (inglés británico)", 25, "en-gb"),
    ("bm_george (inglés británico)", 26, "en-gb"),
    ("bm_lewis (inglés británico)", 27, "en-gb"),
    # Hindi
    ("hf_alpha (hindi)", 31, "hi"),
    ("hf_beta (hindi)", 32, "hi"),
    ("hm_omega (hindi)", 33, "hi"),
    ("hm_psi (hindi)", 34, "hi"),
    # Italiano
    ("if_sara (italiano)", 35, "it"),
    ("im_nicola (italiano)", 36, "it"),
    # Portugués brasileño
    ("pf_dora (portugués)", 42, "pt-br"),
    ("pm_alex (portugués)", 43, "pt-br"),
    ("pm_santa (portugués)", 44, "pt-br"),
]
# Quedan fuera adrede (comprobado en banco el 2026-08-03): las 8 voces chinas
# (sid 45-52) — el puente aún no pasa el lexicón zh del modelo y el texto se
# traga (0,3 s de audio por frase) — y las 5 japonesas (sid 37-41) — espeak
# fonemiza mal el japonés (14,6 s para una frase corta) y el modelo no lo
# soporta oficialmente vía sherpa. Rehabilitarlas pasaría por el servidor.

def kokoro_list_voices():
    return [voz[0] for voz in VOCES_KOKORO]

def kokoro_idiomas_disponibles():
    """Códigos de idioma que trae el modelo, sin repetir y en el orden de la
    tabla. Sirve para ofrecer el filtro de idioma en los Ajustes."""
    codigos = []
    for etiqueta, sid, lang in VOCES_KOKORO:
        if lang not in codigos:
            codigos.append(lang)
    return codigos

def kokoro_voces_de_idioma(codigo=None):
    """Devuelve [(índice, etiqueta)] de las voces de un idioma, o de todas si
    no se pasa ninguno. El índice es el global de VOCES_KOKORO, que es el que
    se guarda en config['voz']: una lista filtrada NO puede indexarse sola."""
    return [(i, voz[0]) for i, voz in enumerate(VOCES_KOKORO)
            if codigo is None or voz[2] == codigo]

def kokoro_idioma_de_voz(index):
    """Código de idioma de la voz que ocupa ese índice global, o None."""
    if 0 <= index < len(VOCES_KOKORO):
        return VOCES_KOKORO[index][2]
    return None

def kokoro_voice_config(index):
    """Devuelve el config_path «carpeta?sid=N&lang=xx» que entiende el puente,
    o None si el modelo no está disponible en esta máquina."""
    if not kokoro_model_instalado():
        return None
    if not (0 <= index < len(VOCES_KOKORO)):
        index = 0
    _, sid, lang = VOCES_KOKORO[index]
    # Ruta absoluta: el puente corre con su propio directorio de trabajo,
    # una ruta relativa a VeTube no resolvería allí.
    return f"{os.path.abspath(KOKORO_MODEL_DIR)}?sid={sid}&lang={lang}"

def _varint(n):
    salida = b""
    while True:
        septeto = n & 0x7F
        n >>= 7
        if n:
            salida += bytes([septeto | 0x80])
        else:
            return salida + bytes([septeto])

def _entrada_metadata(clave, valor):
    """Serializa un metadata_props de ONNX: campo 14 del ModelProto (tag 0x72),
    con un StringStringEntryProto {key=1, value=2} dentro."""
    k = clave.encode("utf-8")
    v = str(valor).encode("utf-8")
    interno = b"\x0a" + _varint(len(k)) + k + b"\x12" + _varint(len(v)) + v
    return b"\x72" + _varint(len(interno)) + interno

def preparar_voz_piper(json_path, forzar=False):
    """Prepara (una sola vez) una voz del catálogo rhasspy para sherpa-onnx.

    Los paquetes oficiales k2-fsa traen de fábrica dos piezas que las voces
    rhasspy no tienen: los metadatos del .onnx (sample_rate, n_speakers,
    comment=piper…, sin los cuales el motor aborta) y el tokens.txt. Ambas se
    derivan por completo del .json de la voz: los metadatos se añaden por
    concatenación al .onnx (propiedad del wire format de protobuf: los campos
    repetidos de mensajes concatenados se fusionan) y el tokens.txt replica
    octeto a octeto el de los paquetes k2-fsa (una línea «símbolo id» por
    entrada de phoneme_id_map).

    El tokens.txt se escribe EL ÚLTIMO porque hace de marcador de «voz ya
    preparada»: si algo se interrumpe a medias, el próximo intento rehace
    todo (los metadatos repetidos con el mismo valor son inofensivos).

    forzar=True rehace la preparación aunque el marcador esté: hay que usarlo
    siempre que se sustituya el .onnx de una carpeta ya preparada (reinstalar
    una voz), porque el tokens.txt viejo sobrevive al fichero nuevo y este se
    quedaría sin metadatos — y un .onnx sin metadatos aborta el puente entero.
    """
    try:
        carpeta = os.path.dirname(json_path)
        marcador = os.path.join(carpeta, "tokens.txt")
        if os.path.isfile(marcador) and not forzar:
            return True
        with open(json_path, encoding="utf-8") as f:
            cfg = json.load(f)
        mapa = cfg.get("phoneme_id_map")
        if not mapa:
            return False

        onnx_path = json_path[:-len(".json")]
        if not os.path.isfile(onnx_path):
            return False
        meta = {
            "model_type": "vits",
            "comment": "piper",
            "language": cfg.get("language", {}).get("name_english", "unknown"),
            "voice": cfg.get("espeak", {}).get("voice", ""),
            "has_espeak": 1,
            "n_speakers": cfg.get("num_speakers", 1),
            "sample_rate": cfg["audio"]["sample_rate"],
        }
        blob = b"".join(_entrada_metadata(k, v) for k, v in meta.items())
        with open(onnx_path, "ab") as f:
            f.write(blob)

        temporal = marcador + ".tmp"
        with open(temporal, "w", encoding="utf-8", newline="") as f:
            for simbolo, ids in mapa.items():
                f.write(f"{simbolo} {ids[0]}\n")
        os.replace(temporal, marcador)
        return True
    except Exception as e:
        print(f"No se pudo preparar la voz {json_path}: {e}")
        return False

# Configuración de Job Objects para Windows
if sys.platform == "win32":
    CreateJobObject = ctypes.windll.kernel32.CreateJobObjectW
    SetInformationJobObject = ctypes.windll.kernel32.SetInformationJobObject
    AssignProcessToJobObject = ctypes.windll.kernel32.AssignProcessToJobObject

    JobObjectExtendedLimitInformation = 9
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    CREATE_BREAKAWAY_FROM_JOB = 0x01000000

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("LimitFlags", ctypes.c_uint32),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("SiloId", ctypes.c_uint32),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryLimit", ctypes.c_size_t),
            ("PeakJobMemoryLimit", ctypes.c_size_t),
        ]

# Reutilizamos el proto de sonata: el puente habla el mismo protocolo.
PROTO_DIR = os.path.join(os.path.dirname(__file__), "sonata_protos")
if PROTO_DIR not in sys.path:
    sys.path.append(PROTO_DIR)

from .sonata_protos import sonata_grpc_pb2

# Instancia global para el Singleton: los modos «piper» y «kokoro» comparten
# el mismo proceso puente (el servidor mantiene cada modelo cargado residente,
# así que alternar entre motores no recarga nada).
_INSTANCIA_SHERPA = None

class sherpaSpeak:
    def __new__(cls, *args, **kwargs):
        global _INSTANCIA_SHERPA
        if _INSTANCIA_SHERPA is None:
            _INSTANCIA_SHERPA = super(sherpaSpeak, cls).__new__(cls)
            _INSTANCIA_SHERPA._inicializado = False
        return _INSTANCIA_SHERPA

    def __init__(self, model_path=None):
        if self._inicializado:
            if model_path:
                self.load_model(model_path)
            return

        self.process = None
        self.port = None
        self.channel = None
        self.voice_id = None
        self.current_voice_path = None
        self.job_handle = None

        # Parámetros de audio
        self.device = -1 # Dispositivo por defecto de BASS
        self.sample_rate = 24000
        self.length_scale = 1.0
        # El tono ya no viaja al servidor: se aplica en VeTube re-muestreando
        # el stream BASS (misma técnica que el DSP del servidor sonata, paridad
        # validada de oído el 2026-08-02). ratio = 1 + 0.05 * slider.
        self.pitch_ratio = 1.0
        self.volume = 100 # Volumen máximo

        self.bass_stream = None
        # Generación de habla: silence() la incrementa para invalidar síntesis en curso o pendientes.
        self._speak_generation = 0
        # True mientras una síntesis sigue recibiendo audio del puente; junto
        # con el estado del stream BASS permite saber si aún se está hablando
        # (botón «Detener prueba» de los Ajustes).
        self._sintetizando = False

        # Iniciar Job Object en Windows
        if sys.platform == "win32":
            self.job_handle = CreateJobObject(None, None)
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            SetInformationJobObject(self.job_handle, JobObjectExtendedLimitInformation, ctypes.pointer(info), ctypes.sizeof(info))

        # Limpiar instancias huérfanas de NUESTRO puente antes de empezar
        if sys.platform == "win32":
            self._cleanup_own_orphans()

        # Iniciar loop asíncrono
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        # Lanzar servidor
        asyncio.run_coroutine_threadsafe(self._start_server(), self.loop)

        atexit.register(self.close)

        if model_path:
            self.load_model(model_path)

        self._inicializado = True

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        except:
            pass

    def _cleanup_own_orphans(self):
        """Mata instancias del puente que hayan quedado huérfanas, pero SOLO las
        lanzadas desde nuestra propia carpeta de binarios: comparar únicamente
        el nombre del ejecutable mataba también el puente de otra instalación
        de VeTube abierta a la vez (portable, copia de desarrollo), que se
        quedaba muda sin volver a levantarlo."""
        try:
            import psutil
            ruta_propia = os.path.normcase(os.path.abspath(EXE_PUENTE))
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    nombre = (proc.info.get('name') or '').lower()
                    if nombre != NOMBRE_EXE_PUENTE:
                        continue
                    ruta = proc.info.get('exe')
                    if ruta and os.path.normcase(ruta) == ruta_propia:
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except:
            pass

    def _find_free_port(self):
        # Intentar primero un puerto fijo distinto del de sonata (50051)
        fixed_port = 50052
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", fixed_port))
                return fixed_port
            except:
                s.bind(("127.0.0.1", 0))
                return s.getsockname()[1]

    async def _start_server(self):
        self.port = self._find_free_port()
        env = os.environ.copy()
        env["SONATA_GRPC_SERVER_PORT"] = str(self.port)

        self.process = subprocess.Popen(
            [EXE_PUENTE],
            cwd=os.path.dirname(EXE_PUENTE),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=(subprocess.CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB) if sys.platform == "win32" else 0
        )

        # Asignar proceso al Job Object
        if sys.platform == "win32" and self.job_handle and self.process:
            AssignProcessToJobObject(self.job_handle, self.process._handle)

        max_retries = 15
        for i in range(max_retries):
            try:
                self.channel = Channel('127.0.0.1', self.port)
                await asyncio.sleep(2)
                break
            except:
                await asyncio.sleep(1)

    def load_model(self, model_path=None):
        if not model_path:
            model_path = self.current_voice_path
        if not model_path: return

        # Las rutas de Kokoro («carpeta?sid=..&lang=..») no son ficheros: pasan
        # tal cual, sin buscarlas en el disco.
        es_ruta_kokoro = "?" in model_path

        # Si el .onnx no está en la ruta dada (nombres de carpeta que no
        # coinciden), lo buscamos dentro de voices/. Solo en las carpetas
        # «voice-*»: en voices/ vive también el paquete de Kokoro, y sus
        # ficheros (model.onnx, tokens.txt) no son voces de Piper.
        if not es_ruta_kokoro and not os.path.exists(model_path):
            import glob
            filename = os.path.basename(model_path)
            coincidencias = glob.glob(os.path.join("voices", "voice-*", filename))
            if coincidencias:
                model_path = coincidencias[0]

        if model_path.endswith(".onnx"):
            json_path = model_path + ".json"
            if not os.path.exists(json_path):
                # Voz colocada a mano: su configuración puede llamarse de otro
                # modo (config.json, <nombre>.json). Sin este repli se enviaría
                # el .onnx crudo, que se salta la preparación de abajo y llega
                # al puente sin tokens.txt.
                import glob
                otros = [j for j in glob.glob(os.path.join(os.path.dirname(model_path), "*.json"))
                         if "+RT" not in os.path.basename(j)]
                json_path = otros[0] if otros else json_path
            if os.path.exists(json_path):
                model_path = json_path

        # Voz Piper: garantizar el tokens.txt y los metadatos que exige sherpa
        # (las voces del catálogo rhasspy no los traen; se preparan una vez).
        # Sin preparación no se intenta cargar: un .onnx sin metadatos aborta
        # el proceso del puente entero, no solo la carga.
        if model_path.endswith(".json") and not preparar_voz_piper(model_path):
            print(f"Voz no preparada para sherpa, no se carga: {model_path}")
            # Soltar la voz anterior: si no, el puente seguiría hablando con
            # ella (puede ser la del otro motor) mientras Ajustes muestra la
            # que se acaba de elegir.
            self.unload_model()
            return

        self.current_voice_path = model_path
        # Invalidar la voz anterior antes de pedir la nueva: mientras el puente
        # responde, un mensaje del chat encontraría el identificador viejo, no
        # esperaría (ver _speak_task_inner) y se leería con la voz que el
        # usuario acaba de abandonar, incluso la del otro motor.
        self.voice_id = None
        asyncio.run_coroutine_threadsafe(self._load_voice_task(model_path), self.loop)

    async def _load_voice_task(self, model_path):
        while self.channel is None:
            await asyncio.sleep(0.5)

        req = sonata_grpc_pb2.VoicePath(config_path=model_path if "?" in model_path else os.path.abspath(model_path))
        try:
            async with self.channel.request(
                '/sonata_grpc.sonata_grpc/LoadVoice',
                grpclib.const.Cardinality.UNARY_UNARY,
                sonata_grpc_pb2.VoicePath,
                sonata_grpc_pb2.VoiceInfo,
            ) as s:
                await s.send_message(req, end=True)
                voice_info = await s.recv_message()
                if voice_info:
                    self.voice_id = voice_info.voice_id
                    if hasattr(voice_info, 'audio') and voice_info.audio.sample_rate:
                        self.sample_rate = voice_info.audio.sample_rate
        except Exception as e:
            print(f"Error al cargar voz en el puente sherpa: {e}")

    def get_devices(self):
        try:
            from sound_lib.output import Output
            o = Output()
            return [{'name': name, 'id': i} for i, name in enumerate(o.get_device_names())]
        except:
            return []

    def find_device_id(self, term, known_devices=None):
        try:
            devices = known_devices if known_devices is not None else self.get_devices()
            for device in devices:
                if device['name'] == term:
                    return device['id']
        except:
            pass
        return -1

    def set_rate(self, new_scale):
        self.length_scale = new_scale

    def set_pitch(self, value):
        # Mapeamos el slider (-10 a 10) al ratio de re-muestreo (0.5x a 2x aprox)
        ratio = 1.0 + (value * 0.05)
        if ratio < 0.5: ratio = 0.5
        if ratio > 2.0: ratio = 2.0
        self.pitch_ratio = ratio

    def set_volume(self, value):
        self.volume = int(value)
        if self.volume < 0: self.volume = 0
        if self.volume > 100: self.volume = 100

    def set_device(self, device):
        self.device = device

    def is_multispeaker(self):
        return False

    def piperSpeak(self, model_path):
        # Nombre histórico del handler de Piper: carga la voz y devuelve la
        # instancia (varios llamantes reasignan el lector con su resultado).
        self.load_model(model_path)
        return self

    def unload_model(self):
        """Suelta la voz cargada. El puente es un singleton que comparten los
        dos motores, así que al pasar a uno que no tiene ninguna voz instalada
        hay que olvidar la anterior: si no, el chat se seguiría leyendo con la
        voz del otro motor."""
        self.current_voice_path = None
        self.voice_id = None

    def speak(self, text):
        if not text: return
        # Sin voz pedida no hay nada que esperar: _speak_task_inner aguanta 12
        # segundos a que termine de cargar, y eso solo tiene sentido si hay
        # alguna voz en camino.
        if not self.current_voice_path: return
        self.silence()
        self._sintetizando = True
        asyncio.run_coroutine_threadsafe(self._speak_task(text, self._speak_generation), self.loop)

    def silence(self):
        # Invalida cualquier síntesis en curso o pendiente y corta el audio actual.
        self._speak_generation += 1
        self._sintetizando = False
        if self.bass_stream is not None:
            try:
                self.bass_stream.stop()
                self.bass_stream.free()
            except: pass
            self.bass_stream = None

    def is_playing(self):
        """True mientras la voz sigue sonando o generando (para el botón de
        prueba de los Ajustes). Un PushStream nunca «termina» por sí solo:
        al agotarse los datos queda STALLED, que aquí ya cuenta como fin
        porque la síntesis dejó de empujar audio."""
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
        # Si el puente aún está arrancando o cargando el modelo, esperamos en
        # lugar de callar: sin esto, la primera lectura tras elegir la voz se
        # pierde en un silencio mudo (hallazgo de la revisión de accesibilidad).
        espera = 0.0
        while (not self.voice_id or not self.channel) and espera < 12.0:
            if gen != self._speak_generation:
                return  # silenciado mientras esperábamos
            await asyncio.sleep(0.2)
            espera += 0.2
        if not self.voice_id or not self.channel:
            return
        if gen != self._speak_generation:
            return  # silenciado antes de empezar

        rate_val = int(self.length_scale * 40)
        if rate_val < 5: rate_val = 5
        if rate_val > 200: rate_val = 200

        # Solo viaja la velocidad: el volumen y el tono se aplican aquí, sobre
        # el stream BASS, para que nada influya en la síntesis (pedido de César).
        utterance = sonata_grpc_pb2.Utterance(
            voice_id=self.voice_id,
            text=text,
            speech_args=sonata_grpc_pb2.SpeechArgs(
                rate=rate_val
            )
        )

        try:
            local_stream = stream.PushStream(freq=self.sample_rate, chans=1)
            local_stream.volume = self.volume / 100.0
            if self.pitch_ratio != 1.0:
                # Tono por re-muestreo: mismo resultado audible que el DSP de sonata.
                local_stream.frequency = self.sample_rate * self.pitch_ratio
            if self.device != -1:
                try: local_stream.set_device(self.device)
                except: pass
            if gen != self._speak_generation:
                try: local_stream.free()
                except: pass
                return
            self.bass_stream = local_stream

            # play() se llama tras empujar el primer bloque: un stream arrancado
            # sin datos queda STALLED y puede darse por terminado antes de sonar.
            primero = True

            async with self.channel.request(
                '/sonata_grpc.sonata_grpc/SynthesizeUtterance',
                grpclib.const.Cardinality.UNARY_STREAM,
                sonata_grpc_pb2.Utterance,
                sonata_grpc_pb2.SynthesisResult,
            ) as s:
                await s.send_message(utterance, end=True)
                async for result in s:
                    if gen != self._speak_generation:
                        break  # silenciado: dejar de empujar audio
                    if result.wav_samples:
                        local_stream.push(result.wav_samples)
                        if primero:
                            primero = False
                            local_stream.play()

        except Exception as e:
            # Un corte voluntario (silence()/cierre) también rompe el stream:
            # solo es un error de verdad si NADIE ha invalidado esta síntesis.
            if gen == self._speak_generation:
                print(f"Error en síntesis del puente sherpa: {e}")

    def close(self):
        # Invalidar primero las síntesis en curso: así el cierre del canal no
        # se confunde con un error de síntesis en las tareas aún a la escucha.
        self.silence()

        if self.channel:
            canal = self.channel
            self.channel = None
            try:
                # Cerrar el canal DESDE su propio loop: grpclib no es seguro
                # entre hilos y cerrarlo desde aquí daba errores aleatorios.
                if self.loop and self.loop.is_running():
                    self.loop.call_soon_threadsafe(canal.close)
                else:
                    canal.close()
            except:
                pass

        if self.process:
            try:
                if self.process.poll() is None: # Si aún está corriendo
                    self.process.kill()
                    self.process.wait(timeout=1)
            except:
                pass
            self.process = None

        # Cerrar el handle del Job Object (esto matará a los procesos si el flag está activo)
        if self.job_handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self.job_handle)
            except:
                pass
            self.job_handle = None

        if self.loop and self.loop.is_running():
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except:
                pass

        self._inicializado = False
