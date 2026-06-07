# Tasks: Testing Infrastructure

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 150–200 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Complete testing infra + toolchain + tests | PR 1 | ~150–200 lines, single autonomous deliverable |

## Phase 1: Foundation

- [x] 1.1 Add `[dependency-groups]` section to `pyproject.toml` with `dev = ["pytest>=9.0.2", "ruff>=0.14.12", "ty>=0.14.0"]`
- [x] 1.2 Add `[tool.ruff]` section to `pyproject.toml` with rules `select = ["E", "F", "W"]` and `ignore = ["E501"]`
- [x] 1.3 Add `[tool.ty]` section to `pyproject.toml` targeting `files = ["servicios/estadisticas_manager.py"]`

## Phase 2: Test Isolation

- [x] 2.1 Wrap `setup.py` lines 1–11 under `import os; if os.environ.get("VETUBE_TEST_MODE") != "1":` so all audio/IO init is skipped in test mode
- [x] 2.2 Create `tests/__init__.py` as an empty package marker file
- [x] 2.3 Create `tests/conftest.py` setting `os.environ["VETUBE_TEST_MODE"] = "1"` before any app imports, plus a `sample_stats` fixture returning a pre-populated `EstadisticasManager` (2 messages, 1 follower, 1 like, 1 join, 1 share)

## Phase 3: Production Code

- [x] 3.1 Add `to_dict()` method to `servicios/estadisticas_manager.py` returning `{usuarios, mensajes_por_usuario, unidos, seguidores, megusta, compartidas}`
- [x] 3.2 Add `from_dict(data: dict)` classmethod to `servicios/estadisticas_manager.py` restoring instance state from the serialized dict

## Phase 4: Unit Tests

- [x] 4.1 Create `tests/test_estadisticas_manager.py` with tests for every public method: `agregar_mensaje`, `agregar_seguidor`, `agregar_unido`, `actualizar_megusta`, `agregar_compartida` (1 test each)
- [x] 4.2 Add `to_dict` round-trip test and `from_dict` restoration test
- [x] 4.3 Add `resetear_estadisticas` test (non-zero → zero), and initial-state test (all counters zero)

## Phase 5: CI Integration

- [x] 5.1 Add a `test` job to `.github/workflows/betube64.yml` (runs-on: windows-latest, python 3.13, x64) executing in order: `uv sync --dev`, `pytest`, `ruff check`, `ty check`
- [x] 5.2 Update `python-version` in `.github/workflows/betube64.yml` `build` job from `3.12.4` to `3.13`
- [x] 5.3 Update `python-version` in `.github/workflows/betube32.yml` `build` job from `3.11.9` to `3.13`
