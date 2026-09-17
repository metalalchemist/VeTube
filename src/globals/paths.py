import sys
from pathlib import Path

# En app compilada (cx-Freeze), sys.executable apunta al .exe
# En desarrollo, usamos la raíz del proyecto (3 niveles arriba: globals/ -> src/ -> raíz)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent

# Rutas a recursos
LOCALES_DIR = BASE_DIR / "locales"
SOUNDS_DIR = BASE_DIR / "sounds"
VOICES_DIR = BASE_DIR / "voices"
# Motores de voz descargados a demanda (idea de César, 2026-08-17): viven fuera
# de 64/ para que el build no tenga que enumerarlos, y al lado del ejecutable
# —como voices/— para que el actualizador no los pise ni los borre.
ENGINES_DIR = BASE_DIR / "engines"
DATA_FILE = BASE_DIR / "data.json"
FAVORITOS_FILE = BASE_DIR / "favoritos.json"
MENSAJES_DESTACADOS_FILE = BASE_DIR / "mensajes_destacados.json"
BOOTSTRAP_EXE = BASE_DIR / "bootstrap.exe"
