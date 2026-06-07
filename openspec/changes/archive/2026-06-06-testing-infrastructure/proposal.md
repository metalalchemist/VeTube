# Proposal: Testing Infrastructure

## Intent

VeTube has zero testing infrastructure — no runner, no linter, no type checker. CI only builds binaries. This makes verification impossible and refactoring risky. Introduce the minimum viable testing toolchain so the project gains quality gates and a repeatable verification path.

## Scope

### In Scope
- pytest, ruff, and ty as dev dependencies
- `VETUBE_TEST_MODE` env var guard in `setup.py` to suppress import-time side effects
- `tests/` directory with `conftest.py`, fixtures, and `pyproject.toml` tool config
- Unit tests for `EstadisticasManager` (`servicios/estadisticas_manager.py`)
- Test + lint CI job in `.github/workflows/betube64.yml`

### Out of Scope
- Tests for controllers, services, or wxPython UI
- Adapter pattern refactors for testability
- Integration or end-to-end tests
- Linux or macOS CI
- Coverage thresholds or coverage reporting

## Capabilities

### New Capabilities
- `testing-infrastructure`: dev toolchain configuration, test layout, CI integration, and import-time guard for test isolation

### Modified Capabilities
- None

## Approach

Incremental — add toolchain config, guard import-time side effects, test pure business logic first, then wire into CI. `wx` imports that fail headless get a `pytest.mark.skipif`. ruff starts with permissive rules to avoid noise on legacy code. ty targets only typed files initially (py.typed markers).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `pyproject.toml` | Modified | Add dev deps, ruff/ty config sections |
| `setup.py` | Modified | Guard `VETUBE_TEST_MODE` to skip side effects |
| `tests/` | New | Test directory with conftest.py + test_estadisticas_manager.py |
| `.github/workflows/betube64.yml` | Modified | Add test+lint job |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| wx can't import headless | High | `pytest.mark.skipif` for wx-dependent imports |
| ruff flags legacy code heavily | Medium | Start with `--permissive` or selective ignores |
| CI Python version mismatch (3.13 dev vs 3.11/3.12 runner) | Medium | Install dev deps with matching Python or skip if incompatible |

## Rollback Plan

Revert `pyproject.toml` dev deps and tool config, delete `tests/`, revert `setup.py` guard, revert `betube64.yml`. No data migration needed — pure build-time config changes.

## Dependencies

- `pytest`, `ruff`, `ty` packages (installed via `uv`)

## Success Criteria

- [ ] CI runs `pytest` and reports green on every push/PR
- [ ] CI runs `ruff check` with zero errors
- [ ] CI runs `ty` with zero errors on typed files
- [ ] `EstadisticasManager` tests cover all public methods
- [ ] `python setup.py` under `VETUBE_TEST_MODE=1` skips side effects
