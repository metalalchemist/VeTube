# Testing Infrastructure Specification

## Purpose

Dev toolchain configuration, test layout, CI integration, and import-time guard for VeTube test isolation.

## Requirements

### Requirement: Dev Dependencies

The project MUST declare pytest, ruff, and ty as dev dependencies in `pyproject.toml` under `[dependency-groups]` with compatible version pins.

#### Scenario: Dev deps available

- GIVEN a clean checkout
- WHEN `uv sync --dev` executes
- THEN pytest, ruff, and ty are installed and available

### Requirement: Import-Time Side Effect Guard

`setup.py` MUST check `VETUBE_TEST_MODE` before initializing I/O-dependent hardware (sound_lib, espeak, accessible_output2). When `VETUBE_TEST_MODE=1`, `setup.py` MUST skip all I/O initialization. `conftest.py` MUST set `VETUBE_TEST_MODE=1` via `os.environ` before any application imports.

#### Scenario: Test mode suppresses I/O

- GIVEN `VETUBE_TEST_MODE=1`
- WHEN `setup.py` is imported
- THEN no audio/IO subsystem initialization occurs

#### Scenario: Normal mode initializes

- GIVEN `VETUBE_TEST_MODE` is unset
- WHEN `setup.py` is imported
- THEN audio and I/O subsystems initialize normally

#### Scenario: conftest blocks side effects

- GIVEN `conftest.py` loads first during test collection
- WHEN any test imports application code
- THEN `VETUBE_TEST_MODE` is already `1` before the import executes

### Requirement: Test Layout

All tests MUST reside in `tests/` at project root. `conftest.py` MUST provide reusable fixtures. `EstadisticasManager` tests MUST live in `tests/test_estadisticas_manager.py`.

#### Scenario: Standard discovery

- GIVEN `tests/` exists at project root
- WHEN `pytest` runs with no arguments
- THEN all tests under `tests/` are discovered and executed

### Requirement: EstadisticasManager Tests

Every public method of `EstadisticasManager` MUST be tested:

| Method | Requirement |
|--------|-------------|
| `agregar_mensaje()` | MUST increment message count by 1 |
| `agregar_seguidor()` | MUST increment follower count by 1 |
| `agregar_unido()` | MUST increment join count by 1 |
| `actualizar_megusta()` | MUST update like total to given value |
| `agregar_compartida()` | MUST increment share count by 1 |
| `to_dict()` | MUST return dict with correct current state |
| `from_dict()` | MUST restore state from serialized dict |
| `resetear_estadisticas()` | MUST zero all counters |
| Initial state | MUST report zero on all counters |

#### Scenario: Round-trip serialization

- GIVEN an instance with messages=2, followers=1
- WHEN `to_dict()` output is passed to `from_dict()` on a fresh instance
- THEN the fresh instance reports messages=2, followers=1

#### Scenario: Reset clears state

- GIVEN an instance with non-zero counters
- WHEN `resetear_estadisticas()` is called
- THEN every counter reports zero

### Requirement: Linting

ruff MUST pass with zero errors in CI. Configuration MUST live in `[tool.ruff]` in `pyproject.toml`. Initially MAY use `--permissive` or selective `ignore` rules.

#### Scenario: Zero lint errors

- GIVEN valid `[tool.ruff]` config in `pyproject.toml`
- WHEN `ruff check` executes
- THEN exit code is 0

### Requirement: Type Checking

ty MUST pass with zero errors on typed files. Configuration MUST live in `[tool.ty]` in `pyproject.toml`. Initially SHOULD only check files with explicit type annotations.

#### Scenario: Zero type errors

- GIVEN only typed files are targeted
- WHEN `ty` executes
- THEN exit code is 0

### Requirement: CI Integration

`.github/workflows/betube64.yml` MUST include a `test` job running on push and PR. The job MUST install dev deps via `uv`, then run `pytest`, `ruff check`, and `ty`. wx-dependent tests MUST use `@pytest.mark.skipif` for headless runners.

#### Scenario: CI passes on push

- GIVEN a commit is pushed
- WHEN the `test` job runs on GitHub Windows runner
- THEN `pytest`, `ruff check`, and `ty` all exit 0

#### Scenario: wx tests skip headless

- GIVEN a test uses `@pytest.mark.skipif` for headless detection
- WHEN the runner has no display server
- THEN the test is skipped, not failed

### Requirement: Rollback

It MUST be possible to revert all testing-infrastructure changes by reverting `pyproject.toml`, deleting `tests/`, reverting `setup.py`, and reverting `betube64.yml`.

#### Scenario: Clean rollback

- GIVEN all testing-infrastructure changes are applied
- WHEN the four artifacts are reverted/deleted
- THEN the project builds and runs as before the change
