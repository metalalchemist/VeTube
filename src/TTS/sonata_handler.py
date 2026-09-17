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

# Configuración de Job Objects para Windows
if sys.platform == "win32":
    CreateJobObject = ctypes.windll.kernel32.CreateJobObjectW
    SetInformationJobObject = ctypes.windll.kernel32.SetInformationJobObject
    AssignProcessToJobObject = ctypes.windll.kernel32.AssignProcessToJobObject

    # Constantes necesarias
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


# Añadir protos al path de búsqueda
PROTO_DIR = os.path.join(os.path.dirname(__file__), "sonata_protos")
if PROTO_DIR not in sys.path:
    sys.path.append(PROTO_DIR)

from .sonata_protos import sonata_grpc_pb2

# Instancia global para el Singleton
_INSTANCIA_PIPER = None
# El barrido de procesos huérfanos solo hace falta una vez por sesión.
_ORFANOS_LIMPIADOS = False

NOMBRE_EXE_SONATA = "sonata-grpc.exe"
# Carpeta clásica, resuelta respecto a este módulo: en la app compilada cae en
# lib/64/sonata. Desde la 3.95 el build YA NO la copia (pyproject enumera 64/
# archivo por archivo y deja sonata fuera), así que solo existe en dos sitios:
# el árbol de desarrollo, y las instalaciones anteriores a la 3.95, donde
# quedó del build viejo (el actualizador no borra nada). En ambos casos manda,
# porque es de la misma versión que la app que la trajo.
_BIN_EMPAQUETADO = (
    Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "64" / "sonata"
)
# Carpeta del motor descargado: al lado del ejecutable (como voices/), porque
# un directorio descargado no viaja en el build y lib/64/ no existe para él.
_BIN_DESCARGADO = ENGINES_DIR / "sonata"


def sonata_bin_dir():
    """Carpeta del servidor sonata. El empaquetado (64/sonata) manda si está,
    pero desde la 3.95 ya no viaja en el build: donde queda es en el árbol de
    desarrollo y en las instalaciones anteriores, así que es de la versión de
    la app que lo trajo, no forzosamente de la que está corriendo. El
    descargado (engines/sonata) es para las instalaciones que ya no lo traen."""
    if (_BIN_EMPAQUETADO / NOMBRE_EXE_SONATA).is_file():
        return _BIN_EMPAQUETADO
    return _BIN_DESCARGADO


def sonata_instalado():
    """True si el motor sonata está en el equipo (empaquetado o descargado).
    Sin él, las voces Piper no pueden sonar: configurar_tts cae en el respaldo
    SAPI momentáneo y la interfaz ofrece el descargador."""
    return (sonata_bin_dir() / NOMBRE_EXE_SONATA).is_file()


class piperSpeak:
    # Cerrojo del stream BASS. Va en la CLASE, no en la instancia: __init__ se
    # vuelve a ejecutar cada vez que el puente se reinicia, y un cerrojo nuevo
    # no protegería de la tarea que quedó viva de la encarnación anterior.
    # Hace falta porque silence()/close() liberan el stream desde el hilo de la
    # interfaz mientras _speak_task_inner sigue empujando audio desde el hilo
    # asíncrono: sin él, push() puede escribir en un handle ya liberado.
    _bass_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        global _INSTANCIA_PIPER
        if _INSTANCIA_PIPER is None:
            _INSTANCIA_PIPER = super().__new__(cls)
            _INSTANCIA_PIPER._inicializado = False
        return _INSTANCIA_PIPER

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
        self.device = -1  # Dispositivo por defecto de BASS
        self.sample_rate = 22050
        self.length_scale = 1.0
        self.pitch = 50  # Tono normal
        self.volume = 100  # Volumen máximo

        # Rutas dinámicas. Se resuelven aquí y no al importar el módulo:
        # __init__ vuelve a correr en cada reapertura del puente, así que un
        # motor recién descargado se encuentra sin reiniciar VeTube.
        self.bin_dir = sonata_bin_dir()
        self.exe = self.bin_dir / NOMBRE_EXE_SONATA
        self.espeak_dir = self.bin_dir

        self.bass_stream = None
        # Generación de habla: silence() la incrementa para invalidar síntesis en curso o pendientes.
        self._speak_generation = 0
        # close() lo levanta: el arranque del servidor es asíncrono y puede
        # seguir en marcha cuando ya se ha pedido cerrar este puente.
        self._cerrado = False
        # True mientras se está generando audio: lo consulta is_playing() para
        # el botón «Detener» de los Ajustes, que aún no tiene nada que sonar.
        self._sintetizando = False

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

        # Limpiar instancias huérfanas de NUESTRA carpeta antes de empezar.
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
        """Mata procesos sonata-grpc.exe huérfanos, pero SOLO los lanzados desde
        nuestra propia carpeta de binarios: matar por nombre acabaría también
        con el puente de otra instalación de VeTube abierta a la vez.

        Con psutil en vez del sondeo por PowerShell que había antes: lanzar
        PowerShell costaba 370 ms medidos, y esto ya no ocurre solo al abrir
        VeTube sino en cada cambio de motor, con el hilo de la interfaz
        parado mientras tanto. Con psutil son 2 ms, y es lo que usa el otro
        puente desde el PR #100."""
        try:
            import psutil

            ruta_propia = os.path.normcase(os.path.abspath(str(self.exe)))
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    nombre = (proc.info.get("name") or "").lower()
                    if nombre != "sonata-grpc.exe":
                        continue
                    ruta = proc.info.get("exe")
                    if ruta and os.path.normcase(ruta) == ruta_propia:
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except:
            pass

    def _find_free_port(self):
        # Intentar primero un puerto fijo (ej: 50051)
        fixed_port = 50051
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", fixed_port))
                return fixed_port
            except:
                # Si está ocupado, buscar uno libre al azar como antes
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
        env["SONATA_ESPEAKNG_DATA_DIRECTORY"] = str(os.path.abspath(self.espeak_dir))

        self.process = subprocess.Popen(
            [str(self.exe)],
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

        # Si el archivo ONNX no existe en la ruta dada (debido a diferencias de
        # nombres de carpeta), lo buscamos dinámicamente dentro de voices/.
        # Solo en las carpetas «voice-*»: desde que existe Kokoro, en voices/
        # vive también su paquete (voices/kokoro-multi-lang-v1_0/model.onnx), y
        # este fichero es anterior a esa vecindad. Mismo criterio que el otro
        # puente.
        if not os.path.exists(model_path):
            import glob

            filename = os.path.basename(model_path)
            coincidencias = glob.glob(
                os.path.join(str(VOICES_DIR), "voice-*", filename)
            )
            if coincidencias:
                model_path = coincidencias[0]

        if model_path.endswith(".onnx"):
            json_path = model_path + ".json"
            if not os.path.exists(json_path):
                # Para voces RT o cuando el JSON tiene un nombre diferente.
                # Los paquetes RT de mush42 llevan «+RT» en el nombre de su
                # .json, y una misma carpeta puede tener las dos variantes (se
                # descargan en el mismo sitio): hay que emparejar la config con
                # el modelo pedido en vez de coger el primer .json que salga,
                # que depende del orden del sistema de ficheros.
                import glob

                dir_name = os.path.dirname(model_path)
                es_rt = os.path.basename(model_path).lower() in (
                    "encoder.onnx",
                    "decoder.onnx",
                )
                jsons = glob.glob(os.path.join(dir_name, "*.json"))
                propios = [j for j in jsons if ("+RT" in os.path.basename(j)) == es_rt]
                if propios:
                    model_path = propios[0]
                elif jsons:
                    model_path = jsons[0]
                else:
                    model_path = json_path
            else:
                model_path = json_path

        self.current_voice_path = model_path
        # Invalidar la voz anterior antes de pedir la nueva: mientras el puente
        # carga, un mensaje que llegue no debe salir con la voz de antes (es lo
        # que hacía el botón de prueba del descargador, que carga y habla
        # seguido).
        self.voice_id = None
        asyncio.run_coroutine_threadsafe(self._load_voice_task(model_path), self.loop)

    async def _load_voice_task(self, model_path):
        # Si el puente se cierra (cambio de motor) mientras esta tarea
        # esperaba, su loop ya no es el del puente: hay que salir en vez de
        # hablarle a un servidor que ya no existe.
        mi_loop = asyncio.get_running_loop()

        def vigente():
            return not self._cerrado and self.loop is mi_loop

        while self.channel is None:
            if not vigente():
                return
            await asyncio.sleep(0.5)
        if not vigente():
            return

        req = sonata_grpc_pb2.VoicePath(config_path=os.path.abspath(model_path))
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
            print(f"Error al cargar voz en Sonata: {e}")

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
        # Mapeamos el valor (usualmente -10 a 10) a 0-100 para Piper
        self.pitch = int(50 + (value * 2.5))
        self.pitch = max(self.pitch, 0)
        self.pitch = min(self.pitch, 100)

    def set_volume(self, value):
        self.volume = int(value)
        self.volume = max(self.volume, 0)
        self.volume = min(self.volume, 100)

    def set_device(self, device):
        self.device = device

    def is_multispeaker(self):
        return False

    def piperSpeak(self, model_path):
        self.load_model(model_path)
        return self

    def unload_model(self):
        """Olvida la voz cargada. Se llama al pasar a este motor cuando no hay
        ninguna voz instalada para él: así el chat no intenta leerse con la
        que quedara de antes."""
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
        # lugar de callar: antes esto solo pasaba al abrir VeTube, pero ahora
        # el puente también arranca al cambiar de motor, y la primera lectura
        # se perdía en un silencio mudo (revisión de accesibilidad).
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

        # El cursor de velocidad tiene que sonar igual en los dos motores: si no,
        # pasar de Piper a Kokoro cambiaría la velocidad de golpe sin haber
        # tocado nada. Los dos reciben la misma escala (porcentaje_a_escala:
        # 0 a 2,5, con 1,25 en el centro) y cada puente la traduce a lo que
        # espera su servidor.
        #
        # Sonata interpreta rate como length_scale = 15/rate (medido en banco:
        # la duración sigue 187/(rate+8,9) con los silencios fijos aparte).
        # Enviaba length_scale * 40, o sea rate 50 en el centro, que resulta ser
        # length_scale 0,3: tres veces la velocidad natural de la voz. Con 12 el
        # centro cae en length_scale 1,0 —la velocidad que trae el modelo— y el
        # tope del cursor en 0,5, el doble de rápido, igual que en sherpa.
        rate_val = int(round(self.length_scale * 12))
        rate_val = max(rate_val, 1)
        rate_val = min(rate_val, 200)

        utterance = sonata_grpc_pb2.Utterance(
            voice_id=self.voice_id,
            text=text,
            speech_args=sonata_grpc_pb2.SpeechArgs(
                rate=rate_val, volume=self.volume, pitch=self.pitch
            ),
        )

        try:
            local_stream = stream.PushStream(freq=self.sample_rate, chans=1)
            local_stream.volume = self.volume / 100.0
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
            # sin datos queda STALLED y puede darse por terminado antes de sonar
            # —y is_playing() apagaría el botón «Detener prueba» sin que se haya
            # oído nada.
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
                print(f"Error en síntesis Sonata: {e}")

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
                # Antes esto solo pasaba al salir de VeTube; ahora también en
                # cada cambio de motor, así que se nota.
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
    basta con uno a la vez. Si nunca se usó Piper no crea nada, y si ya estaba
    cerrado no hace nada (close() deja _inicializado en False).
    """
    if _INSTANCIA_PIPER is not None and getattr(
        _INSTANCIA_PIPER, "_inicializado", False
    ):
        _INSTANCIA_PIPER.close()
