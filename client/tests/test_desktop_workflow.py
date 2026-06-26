from pathlib import Path
import tomllib


CLIENT_DIR = Path(__file__).resolve().parents[1]


def test_client_dev_extra_installs_test_tools():
    pyproject = tomllib.loads((CLIENT_DIR / "pyproject.toml").read_text())

    dev_deps = pyproject["project"]["optional-dependencies"]["dev"]

    assert any(dep.startswith("pytest") for dep in dev_deps)
    assert any(dep.startswith("pytest-asyncio") for dep in dev_deps)
    assert any(dep.startswith("pytest-xdist") for dep in dev_deps)


def test_run_client_syncs_development_dependencies():
    script = (CLIENT_DIR / "run_client.bat").read_text(encoding="utf-8").lower()

    assert "uv sync --extra dev" in script
    assert "uv pip install" not in script


def test_main_window_applies_server_locale_without_restart_prompt():
    source = (CLIENT_DIR / "ui" / "main_window.py").read_text(encoding="utf-8")

    assert 'self._apply_locale_change(packet.get("locale", "en"))' in source
    assert "Localization.set_locale(locale)" in source
    assert "options-restart-required-message" not in source
