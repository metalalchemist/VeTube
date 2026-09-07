import asyncio
import atexit
import ctypes
import os
import socket
import subprocess
import sys
import threading
from pathlib import Path

import grpclib.const
from grpclib.client import Channel
from sound_lib import stream

from globals.paths import ENGINES_DIR, VOICES_DIR

# Servidor TTS nativo: ejecutable Rust + sherpa-onnx (C-API oficial), proceso
# separado sin Python ni numpy (el arranque de VeTube nunca depende de él,
# incluso en CPUs antiguas sin AVX). Habla el mismo protocolo sonata_grpc que
# el antiguo servidor de Piper, pero aquí sintetiza SOLO el modelo Kokoro: las
# voces Piper volvieron al puente sonata, que las fonemiza mejor. Todo lo que
# hacía falta para servirlas desde aquí (preparación del tokens.txt, metadatos
# del .onnx, resolución de rutas de fichero) se fue con ellas.
_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NOMBRE_EXE_PUENTE = "vetube-sherpa-grpc.exe"
# Carpeta clásica, resuelta respecto a este módulo: en la app compilada cae en
# lib/64/sherpa. Desde la 3.95 el build YA NO la copia (pyproject enumera 64/
# archivo por archivo y deja sherpa fuera), así que solo existe en dos sitios:
# el árbol de desarrollo, y las instalaciones que la recibieron de un build
# anterior, donde quedó porque el actualizador no borra nada. En ambos casos
# manda, porque es de la misma versión que la app que la trajo.
_BIN_EMPAQUETADO = _BASE_DIR / "64" / "sherpa"
# Carpeta del motor descargado: al lado del ejecutable (como voices/), porque
# un directorio descargado no viaja en el build y lib/64/ no existe para él.
_BIN_DESCARGADO = ENGINES_DIR / "sherpa"


def sherpa_bin_dir():
    """Carpeta del servidor sherpa. El empaquetado (64/sherpa) manda si está;
    el descargado (engines/sherpa) es para las instalaciones que ya no lo traen.

    Se resuelve en cada __init__ del puente y no al importar: un motor recién
    descargado tiene que encontrarse sin reiniciar VeTube."""
    if (_BIN_EMPAQUETADO / NOMBRE_EXE_PUENTE).is_file():
        return _BIN_EMPAQUETADO
    return _BIN_DESCARGADO


def sherpa_instalado():
    """True si el motor sherpa está en el equipo (empaquetado o descargado).
    Sin él las voces Kokoro no pueden sonar: configurar_tts cae en el respaldo
    SAPI momentáneo y la interfaz ofrece el descargador.

    No confundir con kokoro_model_instalado(), que mira el paquete de voces:
    para que suene algo hacen falta los dos, y se piden por separado."""
    return (sherpa_bin_dir() / NOMBRE_EXE_PUENTE).is_file()


# Modelo Kokoro local: vive en voices/ junto a las voces de Piper y lo instala
# el descargador propio (servicios/kokoro_manager.py, release tts-models de k2-fsa).
KOKORO_MODEL_DIR = str(VOICES_DIR / "kokoro-multi-lang-v1_0")


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
    # Inglés británico. OJO: el código es «en» a secas, NO «en-gb». En espeak-ng
    # el inglés británico es la variante por defecto y se llama «en»; «en-gb» no
    # existe (sí en-GB-scotland, en-GB-x-rp...). Pedirlo tumbaba el servidor:
    # ninguna voz británica sonaba y el puente se quedaba mudo hasta el
    # siguiente cambio de idioma, que lo reinicia.
    ("bf_alice (inglés británico)", 20, "en"),
    ("bf_emma (inglés británico)", 21, "en"),
    ("bf_isabella (inglés británico)", 22, "en"),
    ("bf_lily (inglés británico)", 23, "en"),
    ("bm_daniel (inglés británico)", 24, "en"),
    ("bm_fable (inglés británico)", 25, "en"),
    ("bm_george (inglés británico)", 26, "en"),
    ("bm_lewis (inglés británico)", 27, "en"),
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
    return [
        (i, voz[0])
        for i, voz in enumerate(VOCES_KOKORO)
        if codigo is None or voz[2] == codigo
    ]


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

# Instancia global para el Singleton: un solo proceso puente para Kokoro, que
# el servidor mantiene con su modelo cargado residente mientras el motor esté
# activo. Al cambiar de motor, lector.configurar_tts cierra este puente.
_INSTANCIA_SHERPA = None
# El barrido de procesos huérfanos solo hace falta una vez por sesión.
_ORFANOS_LIMPIADOS = False


class sherpaSpeak:
    # Cerrojo del stream BASS. Va en la CLASE, no en la instancia: __init__ se
    # vuelve a ejecutar cada vez que el puente se reinicia, y un cerrojo nuevo
    # no protegería de la tarea que quedó viva de la encarnación anterior.
    # Hace falta porque silence()/close() liberan el stream desde el hilo de la
    # interfaz mientras _speak_task_inner sigue empujando audio desde el hilo
    # asíncrono: sin él, push() puede escribir en un handle ya liberado.
    _bass_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        global _INSTANCIA_SHERPA
        if _INSTANCIA_SHERPA is None:
            _INSTANCIA_SHERPA = super().__new__(cls)
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

        # Dónde está el motor, resuelto aquí y no al importar el módulo: si se
        # acaba de descargar, este puente lo encuentra sin reiniciar VeTube.
        self.bin_dir = sherpa_bin_dir()
        self.exe = str(self.bin_dir / NOMBRE_EXE_PUENTE)

        # Parámetros de audio
        self.device = -1  # Dispositivo por defecto de BASS
        self.sample_rate = 24000
        self.length_scale = 1.0
        # El tono ya no viaja al servidor: se aplica en VeTube re-muestreando
        # el stream BASS (misma técnica que el DSP del servidor sonata, paridad
        # validada de oído el 2026-08-02). ratio = 1 + 0.05 * slider.
        self.pitch_ratio = 1.0
        self.volume = 100  # Volumen máximo

        self.bass_stream = None
        # Generación de habla: silence() la incrementa para invalidar síntesis en curso o pendientes.
        self._speak_generation = 0
        # True mientras una síntesis sigue recibiendo audio del puente; junto
        # con el estado del stream BASS permite saber si aún se está hablando
        # (botón «Detener prueba» de los Ajustes).
        self._sintetizando = False
        # close() lo levanta: el arranque del servidor es asíncrono y puede
        # seguir en marcha cuando ya se ha pedido cerrar este puente.
        self._cerrado = False
        # Idioma de la voz Kokoro que tiene cargada el servidor: mientras no
        # sepa cambiarlo en caliente, cambiar de idioma obliga a reiniciarlo.
        self._idioma_cargado = None

        # Iniciar Job Object en Windows
        if sys.platform == "win32":
            self.job_handle = CreateJobObject(None, None)
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            SetInformationJobObject(
                self.job_handle,
                JobObjectExtendedLimitInformation,
                ctypes.pointer(info),
                ctypes.sizeof(info),
            )

        # Limpiar instancias huérfanas de NUESTRO puente antes de empezar.
        # Solo la primera vez de la sesión: sirve para barrer los restos de un
        # cierre anterior, y a partir del segundo arranque (cambio de motor)
        # acabamos de matar nosotros mismos el único proceso que podía haber.
        global _ORFANOS_LIMPIADOS
        if sys.platform == "win32" and not _ORFANOS_LIMPIADOS:
            self._cleanup_own_orphans()
            _ORFANOS_LIMPIADOS = True

        # Iniciar loop asíncrono
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        # Lanzar servidor
        asyncio.run_coroutine_threadsafe(self._start_server(), self.loop)

        # Solo la primera vez: __init__ se vuelve a ejecutar en cada cambio de
        # motor (close() deja _inicializado en False) y se acumulaba un
        # atexit por cada ida y vuelta.
        if not getattr(self, "_atexit_puesto", False):
            atexit.register(self.close)
            self._atexit_puesto = True

        if model_path:
            self.load_model(model_path)

        self._inicializado = True

    def _run_loop(self):
        # Guardar el loop en una variable local: self.loop apunta a otro en
        # cuanto el puente se reinicia, y limpiar «el loop de self» acabaría
        # cancelando las tareas del puente NUEVO en vez de las del viejo.
        loop = self.loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        except:
            pass
        finally:
            # Cerrarlo aquí, ya fuera de run_forever: cada cambio de motor crea
            # un loop nuevo, y los anteriores se quedaban abiertos con su
            # socketpair interno hasta el final de la sesión. Antes de cerrar
            # hay que cancelar lo que quedara en vuelo, o Python avisa por la
            # salida de error de cada tarea destruida a medias.
            try:
                tareas = asyncio.all_tasks(loop)
                for tarea in tareas:
                    tarea.cancel()
                if tareas:
                    loop.run_until_complete(
                        asyncio.gather(*tareas, return_exceptions=True)
                    )
            except Exception:
                pass
            try:
                loop.close()
            except Exception:
                pass

    def _cleanup_own_orphans(self):
        """Mata instancias del puente que hayan quedado huérfanas, pero SOLO las
        lanzadas desde nuestra propia carpeta de binarios: comparar únicamente
        el nombre del ejecutable mataba también el puente de otra instalación
        de VeTube abierta a la vez (portable, copia de desarrollo), que se
        quedaba muda sin volver a levantarlo."""
        try:
            import psutil

            ruta_propia = os.path.normcase(os.path.abspath(self.exe))
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    nombre = (proc.info.get("name") or "").lower()
                    if nombre != NOMBRE_EXE_PUENTE:
                        continue
                    ruta = proc.info.get("exe")
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
        # Puede haberse pedido el cierre mientras esta corrutina esperaba turno:
        # cambiar de motor cierra este puente, y arrancar un servidor después
        # dejaría un proceso que ya no es de nadie. No basta con mirar
        # _cerrado: si el puente ya se ha vuelto a abrir, __init__ lo ha puesto
        # otra vez en False y esta corrutina vieja se creería vigente. El loop
        # sí distingue una encarnación de la siguiente.
        mi_loop = asyncio.get_running_loop()
        if self._cerrado or self.loop is not mi_loop:
            return
        self.port = self._find_free_port()
        env = os.environ.copy()
        env["SONATA_GRPC_SERVER_PORT"] = str(self.port)

        self.process = subprocess.Popen(
            [self.exe],
            cwd=str(self.bin_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=(subprocess.CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB)
            if sys.platform == "win32"
            else 0,
        )

        # Si el cierre llegó justo mientras arrancábamos, close() ya no tenía
        # nada que matar (self.process aún era None) y el Job Object está
        # cerrado: hay que matarlo aquí o queda huérfano para siempre.
        proceso = self.process
        if self._cerrado or self.loop is not mi_loop:
            try:
                proceso.kill()
            except Exception:
                pass
            if self.process is proceso:
                self.process = None
            return

        # Asignar proceso al Job Object
        if sys.platform == "win32" and self.job_handle and self.process:
            AssignProcessToJobObject(self.job_handle, self.process._handle)

        max_retries = 15
        for i in range(max_retries):
            # El canal queda atado al loop donde se crea: si el puente ya se
            # ha reiniciado, publicarlo aquí se lo daría al puente nuevo, que
            # lo usaría desde OTRO loop («attached to a different loop») y no
            # conseguiría cargar ninguna voz.
            if self._cerrado or self.loop is not mi_loop:
                return
            try:
                self.channel = Channel("127.0.0.1", self.port)
                await asyncio.sleep(2)
                break
            except:
                await asyncio.sleep(1)

    def load_model(self, model_path=None):
        if not model_path:
            model_path = self.current_voice_path
        if not model_path:
            return

        # Aquí solo llegan rutas de Kokoro («carpeta?sid=..&lang=..»), que no
        # son ficheros y pasan tal cual: desde que Piper habla por sonata, no
        # hay ningún .onnx que buscar ni preparar en el disco.

        # El servidor guarda el modelo Kokoro en caché por su ruta, y con él el
        # idioma de la PRIMERA voz que se cargó: pedir después una voz de otro
        # idioma cambia el timbre pero sigue fonemizando con el anterior — una
        # voz francesa con acento español, muy audible. Mientras el puente no
        # sepa cambiar de idioma en caliente, se reinicia: cuesta ~2 s y solo
        # ocurre al cambiar de idioma de voz, no al cambiar de voz.
        idioma_nuevo = self._idioma_de_ruta(model_path)
        if (
            idioma_nuevo
            and self._idioma_cargado
            and idioma_nuevo != self._idioma_cargado
        ):
            # __init__() devuelve los parámetros de audio a sus valores por
            # defecto (dispositivo -1, volumen 100, velocidad y tono a 1), pero
            # esos son del usuario y no tienen por qué cambiar porque el puente
            # se reinicie: el volumen y la velocidad volvían al centro cada vez
            # que se cambiaba de idioma de voz.
            ajustes_audio = (
                self.device,
                self.volume,
                self.length_scale,
                self.pitch_ratio,
            )
            self.close()
            self.__init__()
            (self.device, self.volume, self.length_scale, self.pitch_ratio) = (
                ajustes_audio
            )
        self._idioma_cargado = idioma_nuevo or self._idioma_cargado

        self.current_voice_path = model_path
        # Invalidar la voz anterior antes de pedir la nueva: mientras el puente
        # responde, un mensaje del chat encontraría el identificador viejo, no
        # esperaría (ver _speak_task_inner) y se leería con la voz que el
        # usuario acaba de abandonar.
        self.voice_id = None
        asyncio.run_coroutine_threadsafe(self._load_voice_task(model_path), self.loop)

    @staticmethod
    def _idioma_de_ruta(model_path):
        """Idioma pedido en una ruta de Kokoro («carpeta?sid=N&lang=xx»)."""
        if "?" not in model_path:
            return None
        from urllib.parse import parse_qs

        valores = parse_qs(model_path.split("?", 1)[1]).get("lang")
        return valores[0] if valores else None

    async def _load_voice_task(self, model_path):
        # Si el puente se reinicia (cambio de idioma) mientras esta tarea
        # esperaba, su loop ya no es el del puente: hay que salir en vez de
        # hablarle a un servidor que ya no existe, que era lo que llenaba el
        # registro de «Connection closed» al recorrer la lista de voces.
        mi_loop = asyncio.get_running_loop()

        def vigente():
            return not self._cerrado and self.loop is mi_loop

        while self.channel is None:
            if not vigente():
                return
            await asyncio.sleep(0.5)
        if not vigente():
            return

        req = sonata_grpc_pb2.VoicePath(
            config_path=model_path if "?" in model_path else os.path.abspath(model_path)
        )
        try:
            async with self.channel.request(
                "/sonata_grpc.sonata_grpc/LoadVoice",
                grpclib.const.Cardinality.UNARY_UNARY,
                sonata_grpc_pb2.VoicePath,
                sonata_grpc_pb2.VoiceInfo,
            ) as s:
                await s.send_message(req, end=True)
                voice_info = await s.recv_message()
                if voice_info:
                    self.voice_id = voice_info.voice_id
                    if hasattr(voice_info, "audio") and voice_info.audio.sample_rate:
                        self.sample_rate = voice_info.audio.sample_rate
        except Exception as e:
            print(f"Error al cargar voz en el puente sherpa: {e}")

    def get_devices(self):
        try:
            from sound_lib.output import Output

            o = Output()
            return [
                {"name": name, "id": i} for i, name in enumerate(o.get_device_names())
            ]
        except:
            return []

    def find_device_id(self, term, known_devices=None):
        try:
            devices = known_devices if known_devices is not None else self.get_devices()
            for device in devices:
                if device["name"] == term:
                    return device["id"]
        except:
            pass
        return -1

    def set_rate(self, new_scale):
        self.length_scale = new_scale

    def set_pitch(self, value):
        # Mapeamos el slider (-10 a 10) al ratio de re-muestreo (0.5x a 2x aprox)
        ratio = 1.0 + (value * 0.05)
        ratio = max(ratio, 0.5)
        ratio = min(ratio, 2.0)
        self.pitch_ratio = ratio

    def set_volume(self, value):
        self.volume = int(value)
        self.volume = max(self.volume, 0)
        self.volume = min(self.volume, 100)

    def set_device(self, device):
        self.device = device

    def is_multispeaker(self):
        return False

    def unload_model(self):
        """Suelta la voz cargada. El puente sobrevive a que Kokoro se quede sin
        modelo instalado, así que hay que olvidar la voz anterior: si no, el
        chat se seguiría leyendo con una voz que Ajustes ya no muestra."""
        self.current_voice_path = None
        self.voice_id = None

    def speak(self, text):
        if not text:
            return
        # Puente cerrado porque se pasó al otro motor: nada que sintetizar.
        # Se mira _cerrado y no _inicializado porque close() levanta el primero
        # nada más empezar y solo baja el segundo al final: entre medias detiene
        # el loop, y programar ahí una síntesis reventaría con «Event loop is
        # closed» en el hilo de la interfaz.
        if self._cerrado:
            return
        # Sin voz pedida no hay nada que esperar: _speak_task_inner aguanta 12
        # segundos a que termine de cargar, y eso solo tiene sentido si hay
        # alguna voz en camino.
        if not self.current_voice_path:
            return
        self.silence()
        self._sintetizando = True
        asyncio.run_coroutine_threadsafe(
            self._speak_task(text, self._speak_generation), self.loop
        )

    def silence(self):
        # Invalida cualquier síntesis en curso o pendiente y corta el audio actual.
        self._speak_generation += 1
        self._sintetizando = False
        # Bajo cerrojo: el hilo asíncrono puede estar empujando audio en este
        # mismo stream, y liberarlo bajo sus pies es un uso después de liberar
        # dentro de una biblioteca nativa.
        with self._bass_lock:
            if self.bass_stream is not None:
                try:
                    self.bass_stream.stop()
                    self.bass_stream.free()
                except:
                    pass
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
        rate_val = max(rate_val, 5)
        rate_val = min(rate_val, 200)

        # Solo viaja la velocidad: el volumen y el tono se aplican aquí, sobre
        # el stream BASS, para que nada influya en la síntesis (pedido de César).
        utterance = sonata_grpc_pb2.Utterance(
            voice_id=self.voice_id,
            text=text,
            speech_args=sonata_grpc_pb2.SpeechArgs(rate=rate_val),
        )

        try:
            local_stream = stream.PushStream(freq=self.sample_rate, chans=1)
            local_stream.volume = self.volume / 100.0
            if self.pitch_ratio != 1.0:
                # Tono por re-muestreo: mismo resultado audible que el DSP de sonata.
                local_stream.frequency = self.sample_rate * self.pitch_ratio
            if self.device != -1:
                try:
                    local_stream.set_device(self.device)
                except:
                    pass
            # Comprobar y publicar en el mismo cerrojo: si se comprueba fuera,
            # un silence() que entre justo aquí deja este stream sin dueño (ya
            # no es self.bass_stream) y nadie lo libera nunca.
            with self._bass_lock:
                if gen != self._speak_generation:
                    try:
                        local_stream.free()
                    except:
                        pass
                    return
                self.bass_stream = local_stream

            # play() se llama tras empujar el primer bloque: un stream arrancado
            # sin datos queda STALLED y puede darse por terminado antes de sonar.
            primero = True

            async with self.channel.request(
                "/sonata_grpc.sonata_grpc/SynthesizeUtterance",
                grpclib.const.Cardinality.UNARY_STREAM,
                sonata_grpc_pb2.Utterance,
                sonata_grpc_pb2.SynthesisResult,
            ) as s:
                await s.send_message(utterance, end=True)
                async for result in s:
                    if gen != self._speak_generation:
                        break  # silenciado: dejar de empujar audio
                    if result.wav_samples:
                        # La generación se vuelve a mirar DENTRO del cerrojo: es
                        # lo que hace segura la escritura. Comprobarla fuera deja
                        # una rendija en la que silence() libera el handle entre
                        # la comprobación y el push, y BASS reutiliza los handles.
                        with self._bass_lock:
                            if gen != self._speak_generation:
                                break
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
        # Avisar cuanto antes: el servidor puede estar arrancando todavía en el
        # otro hilo y no debe quedarse vivo detrás de nosotros.
        self._cerrado = True
        # Invalidar las síntesis en curso: así el cierre del canal no se
        # confunde con un error de síntesis en las tareas aún a la escucha.
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
                if self.process.poll() is None:  # Si aún está corriendo
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


def detener_puente():
    """Cierra el servidor de este motor si hay uno vivo.

    Se llama al pasar al otro motor: cada puente tiene su propio proceso y
    basta con uno a la vez. Si nunca se usó Kokoro no crea nada, y si ya
    estaba cerrado no hace nada (close() deja _inicializado en False).
    """
    if _INSTANCIA_SHERPA is not None and getattr(
        _INSTANCIA_SHERPA, "_inicializado", False
    ):
        _INSTANCIA_SHERPA.close()
