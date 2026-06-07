# Design: Testing Infrastructure

## Technical Approach

Add a dev toolchain (pytest, ruff, ty) via `[dependency-groups]` in `pyproject.toml`, guard `setup.py` I/O with a `VETUBE_TEST_MODE` env var, seed `tests/` with a focused `EstadisticasManager` suite, and wire test+lint+type-check into `betube64.yml`. Keep the production code surface area minimal — only add `to_dict`/`from_dict` to `EstadisticasManager` (a 12-line additive change required to satisfy the spec's round-trip scenario).

## Architecture Decisions

| Decision | Choice | Tradeoff |
|---|---|---|
| Test isolation mechanism | `VETUBE_TEST_MODE` env var in `setup.py` | One-line check, no refactor. Cost: relies on `setup.py` being the import surface — must stay in sync. |
| wx headless handling | `@pytest.mark.skipif(not os.environ.get("DISPLAY"), ...)` | stdlib only. Cost: Windows CI always has a display, so the skip is effectively a Linux/macOS guard. |
| Tool config location | All in `pyproject.toml` (`[tool.ruff]`, `[tool.ty]`) | One config source for uv project. Cost: ty's schema is still evolving. |
| CI scope | `betube64.yml` only (x64) | Lower iteration cost. x86 deferred to follow-up. |
| Serialization API | Add `to_dict`/`from_dict` to `EstadisticasManager` | Spec mandates them. Cost: small additive change to production code. |
| Python version in CI | Align all workflows to **Python 3.13** | Matches `.python-version` and `pyproject.toml` `requires-python = >=3.13`. Fixes pre-existing drift. |

**Rejected alternatives**:
- Refactor `setup.py` to lazy-import hardware modules → too invasive for a tooling PR.
- Use `pytest-wx` plugin → adds a dep, doesn't solve headless skip.
- Move config to separate `ruff.toml`/`ty.toml` → fragments the project config hub.
- Add the test job to both `betube64.yml` and `betube32.yml` → doubles CI iteration cost before validation.
- Keep mixed versions (`3.12.4` / `3.11.9`) → pre-existing drift would remain unresolved.

## Data Flow

N/A for tooling config. The `VETUBE_TEST_MODE` guard path is:

```
test process start
   → conftest.py sets os.environ["VETUBE_TEST_MODE"] = "1"
   → any test imports setup.py / application code
   → setup.py checks os.environ, returns early before sound_lib/espeak/accessible_output2 init
```

## File Changes

| File | Action | Description |
|---|---|---|
| `pyproject.toml` | Modify | Append `[dependency-groups] dev = [pytest, ruff, ty]` and `[tool.ruff]`, `[tool.ty]` blocks. Permissive ruff rules to avoid legacy noise. |
| `setup.py` | Modify | Wrap lines 6–11 in `if os.environ.get("VETUBE_TEST_MODE") != "1":`. |
| `servicios/estadisticas_manager.py` | Modify | Add `to_dict()` and `from_dict(d)` — additive, no behavior change to existing methods. |
| `tests/__init__.py` | Create | Empty package marker. |
| `tests/conftest.py` | Create | Sets `VETUBE_TEST_MODE=1` before any app import; adds `sample_stats` fixture returning a pre-populated `EstadisticasManager`. |
| `tests/test_estadisticas_manager.py` | Create | One test per public method (~10 tests). Zero mocks — class is pure. |
| `.github/workflows/betube64.yml` | Modify | Add `test` job: `uv sync --dev` → `pytest` → `ruff check` → `ty check`. Triggers on push/PR, not tags. |

## Interfaces / Contracts

`EstadisticasManager` new public methods (additive):

```python
def to_dict(self) -> dict:
    return {
        "usuarios": list(self.usuarios),
        "mensajes_por_usuario": list(self.mensajes_por_usuario),
        "unidos": self.unidos,
        "seguidores": self.seguidores,
        "megusta": self.megusta,
        "compartidas": self.compartidas,
    }

@classmethod
def from_dict(cls, data: dict) -> "EstadisticasManager":
    inst = cls()
    inst.usuarios = list(data["usuarios"])
    inst.mensajes_por_usuario = list(data["mensajes_por_usuario"])
    inst.unidos = data["unidos"]
    inst.seguidores = data["seguidores"]
    inst.megusta = data["megusta"]
    inst.compartidas = data["compartidas"]
    return inst
```

`setup.py` guarded entry point (after change):

```python
import os
if os.environ.get("VETUBE_TEST_MODE") != "1":
    from utils import languageHandler
    from globals.data_store import config
    from players.sound_helper import SoundPlayer
    from helpers.reader_handler import ReaderHandler
    # ...existing init...
```

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | `EstadisticasManager` (10 methods + round-trip) | Direct instantiation, no mocks, asserts on returned values and internal state. |
| Lint | Whole repo | `ruff check .` — permissive baseline (`E,F,W` only, ignore `E501`). |
| Type | `servicios/estadisticas_manager.py` initially | `ty check servicios/estadisticas_manager.py` — narrow scope first. |
| Integration / E2E | Deferred | Needs adapter refactors and a wx fixture harness. Out of scope per proposal. |

## Migration / Rollout

No data migration. Rollback = revert the 7 touched/created files. CI change is additive — if the `test` job is flaky, the existing `build` job still ships binaries. Feature-flag style: no `VETUBE_TEST_MODE=1` in production code paths.

## Open Questions

- **Spec typo**: spec says `agrega_mensaje()` and `reset()` — actual code uses `agregar_mensaje` and `resetear_estadisticas`. Tests will use the real names; spec should be corrected in archive phase.
- **`to_dict`/`from_dict` addition**: spec requires them but they're not in the class. Design adds them as a small additive change. If the user prefers a pure tooling PR (no production code), the round-trip scenario drops and the spec must be updated.
- **Python version drift**: resolved — all workflows aligned to Python 3.13. `betube64.yml` changed from `3.12.4` → `3.13`, `betube32.yml` changed from `3.11.9` → `3.13`. If x86 3.13 is unavailable on GitHub Actions, fall back to `3.12`.
