from servicios.estadisticas_manager import EstadisticasManager


class TestInitialState:
    """All counters must be zero on a fresh instance."""

    def test_initial_usuarios_empty(self):
        mgr = EstadisticasManager()
        assert mgr.usuarios == []

    def test_initial_mensajes_por_usuario_empty(self):
        mgr = EstadisticasManager()
        assert mgr.mensajes_por_usuario == []

    def test_initial_unidos_zero(self):
        mgr = EstadisticasManager()
        assert mgr.unidos == 0

    def test_initial_seguidores_zero(self):
        mgr = EstadisticasManager()
        assert mgr.seguidores == 0

    def test_initial_megusta_zero(self):
        mgr = EstadisticasManager()
        assert mgr.megusta == 0

    def test_initial_compartidas_zero(self):
        mgr = EstadisticasManager()
        assert mgr.compartidas == 0


class TestAgregarMensaje:

    def test_new_author(self):
        mgr = EstadisticasManager()
        mgr.agregar_mensaje("alice")
        assert mgr.usuarios == ["alice"]
        assert mgr.mensajes_por_usuario == [1]

    def test_existing_author_increments(self):
        mgr = EstadisticasManager()
        mgr.agregar_mensaje("alice")
        mgr.agregar_mensaje("alice")
        assert mgr.usuarios == ["alice"]
        assert mgr.mensajes_por_usuario == [2]

    def test_multiple_authors(self):
        mgr = EstadisticasManager()
        mgr.agregar_mensaje("alice")
        mgr.agregar_mensaje("bob")
        assert mgr.usuarios == ["alice", "bob"]
        assert mgr.mensajes_por_usuario == [1, 1]


class TestAgregarSeguidor:

    def test_increments_by_one(self):
        mgr = EstadisticasManager()
        mgr.agregar_seguidor()
        assert mgr.seguidores == 1

    def test_multiple_increments(self):
        mgr = EstadisticasManager()
        mgr.agregar_seguidor()
        mgr.agregar_seguidor()
        mgr.agregar_seguidor()
        assert mgr.seguidores == 3


class TestAgregarUnido:

    def test_increments_by_one(self):
        mgr = EstadisticasManager()
        mgr.agregar_unido()
        assert mgr.unidos == 1

    def test_multiple_increments(self):
        mgr = EstadisticasManager()
        mgr.agregar_unido()
        mgr.agregar_unido()
        assert mgr.unidos == 2


class TestActualizarMegusta:

    def test_sets_total(self):
        mgr = EstadisticasManager()
        mgr.actualizar_megusta(42)
        assert mgr.megusta == 42

    def test_overwrites_previous(self):
        mgr = EstadisticasManager()
        mgr.actualizar_megusta(10)
        mgr.actualizar_megusta(5)
        assert mgr.megusta == 5


class TestAgregarCompartida:

    def test_increments_by_one(self):
        mgr = EstadisticasManager()
        mgr.agregar_compartida()
        assert mgr.compartidas == 1

    def test_multiple_increments(self):
        mgr = EstadisticasManager()
        mgr.agregar_compartida()
        mgr.agregar_compartida()
        mgr.agregar_compartida()
        assert mgr.compartidas == 3


class TestSerialization:

    def test_to_dict_keys(self):
        mgr = EstadisticasManager()
        d = mgr.to_dict()
        assert set(d.keys()) == {
            "usuarios",
            "mensajes_por_usuario",
            "unidos",
            "seguidores",
            "megusta",
            "compartidas",
        }

    def test_to_dict_values(self, sample_stats):
        d = sample_stats.to_dict()
        assert d["usuarios"] == ["alice", "bob"]
        assert d["mensajes_por_usuario"] == [1, 1]
        assert d["unidos"] == 1
        assert d["seguidores"] == 1
        assert d["megusta"] == 1
        assert d["compartidas"] == 1

    def test_round_trip(self):
        original = EstadisticasManager()
        original.agregar_mensaje("alice")
        original.agregar_mensaje("alice")
        original.agregar_mensaje("bob")
        original.agregar_seguidor()
        original.actualizar_megusta(99)
        original.agregar_unido()
        original.agregar_compartida()

        data = original.to_dict()
        restored = EstadisticasManager.from_dict(data)

        assert restored.usuarios == original.usuarios
        assert restored.mensajes_por_usuario == original.mensajes_por_usuario
        assert restored.unidos == original.unidos
        assert restored.seguidores == original.seguidores
        assert restored.megusta == original.megusta
        assert restored.compartidas == original.compartidas

    def test_from_dict_returns_new_instance(self):
        data = {
            "usuarios": ["x"],
            "mensajes_por_usuario": [3],
            "unidos": 0,
            "seguidores": 0,
            "megusta": 0,
            "compartidas": 0,
        }
        restored = EstadisticasManager.from_dict(data)
        assert isinstance(restored, EstadisticasManager)
        assert restored.usuarios == ["x"]
        assert restored.mensajes_por_usuario == [3]

    def test_to_dict_returns_copies(self):
        """Mutating the returned dict must not affect the instance."""
        mgr = EstadisticasManager()
        mgr.agregar_mensaje("alice")
        d = mgr.to_dict()
        d["usuarios"].append("hacker")
        assert "hacker" not in mgr.usuarios


class TestResetearEstadisticas:

    def test_reset_clears_all(self, sample_stats):
        sample_stats.resetear_estadisticas()
        assert sample_stats.usuarios == []
        assert sample_stats.mensajes_por_usuario == []
        assert sample_stats.unidos == 0
        assert sample_stats.seguidores == 0
        assert sample_stats.megusta == 0
        assert sample_stats.compartidas == 0

    def test_reset_on_fresh_instance(self):
        mgr = EstadisticasManager()
        mgr.resetear_estadisticas()
        assert mgr.usuarios == []
        assert mgr.mensajes_por_usuario == []
