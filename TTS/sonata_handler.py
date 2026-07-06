import os
import sys
import asyncio
import subprocess
import socket
import threading
import time
import atexit
import ctypes
from pathlib import Path
from sound_lib import stream, output
from sound_lib.main import BassError
from grpclib.client import Channel
import grpclib.const

# Configuración de Job Objects para Windows
if sys.platform == "win32":
    GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
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

class piperSpeak:
    def __new__(cls, *args, **kwargs):
        global _INSTANCIA_PIPER
        if _INSTANCIA_PIPER is None:
            _INSTANCIA_PIPER = super(piperSpeak, cls).__new__(cls)
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
        self.device = -1 # Dispositivo por defecto de BASS
        self.sample_rate = 22050 
        self.length_scale = 1.0
        self.pitch = 50 # Tono normal
        self.volume = 100 # Volumen máximo
        
        # Rutas dinámicas
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.bin_dir = base_dir / "64" / "sonata"
        self.exe = self.bin_dir / "sonata-grpc.exe"
        self.espeak_dir = self.bin_dir
        
        self.bass_stream = None
        # Generación de habla: silence() la incrementa para invalidar síntesis en curso o pendientes.
        self._speak_generation = 0

        # Iniciar Job Object en Windows
        if sys.platform == "win32":
            self.job_handle = CreateJobObject(None, None)
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            SetInformationJobObject(self.job_handle, JobObjectExtendedLimitInformation, ctypes.pointer(info), ctypes.sizeof(info))

        # Limpiar instancias huérfanas de NUESTRA carpeta antes de empezar
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
        """Mata procesos sonata-grpc.exe que se estén ejecutando desde nuestra propia carpeta de binarios."""
        try:
            # Comando PowerShell para obtener PID y Ruta de todos los sonata-grpc.exe
            cmd = 'powershell -NoProfile -Command "Get-Process sonata-grpc -ErrorAction SilentlyContinue | Select-Object Id, Path | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            if not output or "sonata-grpc" not in output: return

            import json
            data = json.loads(output)
            if isinstance(data, dict): data = [data] # Si hay uno solo, JSON lo devuelve como dict

            my_exe_path = str(self.exe).lower()
            for proc in data:
                p_path = proc.get('Path', '')
                if p_path and p_path.lower() == my_exe_path:
                    p_id = proc.get('Id')
                    if p_id:
                        subprocess.run(['taskkill', '/F', '/PID', str(p_id)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            creationflags=(subprocess.CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB) if sys.platform == "win32" else 0
        )
        
        # Asignar proceso al Job Object
        if sys.platform == "win32" and self.job_handle and self.process:
            res = AssignProcessToJobObject(self.job_handle, self.process._handle)

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
        
        # Si el archivo ONNX no existe en la ruta dada (debido a diferencias de nombres de carpeta),
        # lo buscamos dinámicamente dentro de subcarpetas de voices/
        if not os.path.exists(model_path):
            import glob
            filename = os.path.basename(model_path)
            coincidencias = glob.glob(os.path.join("voices", "*", filename))
            if coincidencias:
                model_path = coincidencias[0]
        
        if model_path.endswith(".onnx"):
            json_path = model_path + ".json"
            if not os.path.exists(json_path):
                # Para voces RT o cuando el JSON tiene un nombre diferente
                import glob
                dir_name = os.path.dirname(model_path)
                jsons = glob.glob(os.path.join(dir_name, "*.json"))
                if jsons:
                    model_path = jsons[0]
                else:
                    model_path = json_path
            else:
                model_path = json_path
        
        self.current_voice_path = model_path
        asyncio.run_coroutine_threadsafe(self._load_voice_task(model_path), self.loop)

    async def _load_voice_task(self, model_path):
        while self.channel is None:
            await asyncio.sleep(0.5)
            
        req = sonata_grpc_pb2.VoicePath(config_path=os.path.abspath(model_path))
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
            print(f"Error al cargar voz en Sonata: {e}")

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
        # Mapeamos el valor (usualmente -10 a 10) a 0-100 para Piper
        self.pitch = int(50 + (value * 2.5))
        if self.pitch < 0: self.pitch = 0
        if self.pitch > 100: self.pitch = 100

    def set_volume(self, value):
        self.volume = int(value)
        if self.volume < 0: self.volume = 0
        if self.volume > 100: self.volume = 100

    def set_device(self, device):
        self.device = device

    def is_multispeaker(self):
        return False

    def piperSpeak(self, model_path):
        self.load_model(model_path)
        return self

    def speak(self, text):
        if not text: return
        self.silence()
        asyncio.run_coroutine_threadsafe(self._speak_task(text, self._speak_generation), self.loop)

    def silence(self):
        # Invalida cualquier síntesis en curso o pendiente y corta el audio actual.
        self._speak_generation += 1
        if self.bass_stream is not None:
            try:
                self.bass_stream.stop()
                self.bass_stream.free()
            except: pass
            self.bass_stream = None

    async def _speak_task(self, text, gen):
        if not self.voice_id or not self.channel:
            return
        if gen != self._speak_generation:
            return  # silenciado antes de empezar

        rate_val = int(self.length_scale * 40)
        if rate_val < 5: rate_val = 5
        if rate_val > 200: rate_val = 200

        utterance = sonata_grpc_pb2.Utterance(
            voice_id=self.voice_id,
            text=text,
            speech_args=sonata_grpc_pb2.SpeechArgs(
                rate=rate_val,
                volume=self.volume,
                pitch=self.pitch
            )
        )

        try:
            local_stream = stream.PushStream(freq=self.sample_rate, chans=1)
            local_stream.volume = self.volume / 100.0
            if self.device != -1:
                try: local_stream.set_device(self.device)
                except: pass
            if gen != self._speak_generation:
                try: local_stream.free()
                except: pass
                return
            self.bass_stream = local_stream
            local_stream.play()

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

        except Exception as e:
            print(f"Error en síntesis Sonata: {e}")

    def close(self):
        if self.channel:
            try:
                self.channel.close()
            except:
                pass
            self.channel = None

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

        self.silence()

        if self.loop and self.loop.is_running():
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except:
                pass
        
        self._inicializado = False
