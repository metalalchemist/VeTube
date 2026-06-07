import os
import sys

# Set test mode BEFORE any application imports
os.environ["VETUBE_TEST_MODE"] = "1"

# Ensure project root is on sys.path so tests can import application modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from servicios.estadisticas_manager import EstadisticasManager


@pytest.fixture
def sample_stats():
    """Return a pre-populated EstadisticasManager for testing."""
    mgr = EstadisticasManager()
    mgr.agregar_mensaje("alice")
    mgr.agregar_mensaje("bob")
    mgr.agregar_seguidor()
    mgr.actualizar_megusta(1)
    mgr.agregar_unido()
    mgr.agregar_compartida()
    return mgr
