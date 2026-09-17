from globals.data_store import config, motor_de_interfaz
from helpers.reader_handler import ReaderHandler
from players.sound_helper import SoundPlayer
from utils import languageHandler

languageHandler.setLanguage(config["idioma"])
player = SoundPlayer()
# Si el dispositivo guardado ya no existe (por ejemplo, auriculares USB/Bluetooth desconectados),
# volvemos al primero: los índices fuera de rango rompen el arranque con Piper al indexar devicenames.
# Con la lista VACÍA (arranque mudo, sin dispositivo de audio) no se toca nada: ningún valor
# sería válido y una avería pasajera machacaría la preferencia guardada del usuario.
if player.devicenames and not (1 <= config["dispositivo"] <= len(player.devicenames)):
    config["dispositivo"] = 1
reader = ReaderHandler()
reader._leer.set_rate(config["speed"])
reader._leer.set_pitch(config["tono"])
reader._leer.set_volume(config["volume"])
voices_leer = reader._leer.list_voices()
if voices_leer:
    # La voz SAPI tiene su propia clave: config['voz'] es la posición dentro de
    # la lista del motor elegido, y aplicarla aquí cargaba una voz SAPI
    # cualquiera (o la primera, al salirse de rango).
    idx = config.get("voz_sapi", 0)
    if idx >= len(voices_leer):
        idx = 0
    reader._leer.set_voice(voices_leer[idx])

# Configurar el lector principal según el motor que lee el programa (con la
# casilla «Usar voz sapi» marcada vuelve a leerlo el lector de pantalla, aunque
# en la lista siga elegido otro motor).
motor = motor_de_interfaz()
if motor in ("piper", "kokoro"):
    # Los dos puentes (sonata para Piper, sherpa para Kokoro) guardan los
    # parámetros y los aplican en cada speak; la voz se carga en
    # run_main_window. Misma escala que app_utilitys.porcentaje_a_escala (no se
    # importa para no crear un import circular).
    reader._lector.set_rate(1.25 + config["speed"] * 0.125)
    reader._lector.set_pitch(config["tono"])
    reader._lector.set_volume(config["volume"])
elif motor == "edge":
    # Edge guarda los parámetros y los aplica en cada speak; la voz se carga
    # en run_main_window. La velocidad va nativa (-10 a 10) a edge-tts.
    reader._lector.set_rate(config["speed"])
    reader._lector.set_pitch(config["tono"])
    reader._lector.set_volume(config["volume"])
else:
    reader._lector.set_rate(config["speed"])
    if motor == "onecore":
        reader._lector.set_pitch(config.get("tono_onecore", 0.6))
    else:
        reader._lector.set_pitch(config["tono"])
    reader._lector.set_volume(config["volume"])
    voices_lector = reader._lector.list_voices()
    if voices_lector:
        idx = config["voz"]
        if idx >= len(voices_lector):
            idx = 0
        reader._lector.set_voice(voices_lector[idx])
