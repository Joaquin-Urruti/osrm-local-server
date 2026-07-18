from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUTS_DIR = PROJECT_ROOT / "inputs"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SETTINGS_PATH = CONFIG_DIR / "settings.yaml"
SETTINGS_EXAMPLE = CONFIG_DIR / "settings.example.yaml"
OSRM_PORT_FILE = CONFIG_DIR / "osrm_port.txt"
DESTINATIONS_EXAMPLE_CONFIG = INPUTS_DIR / "destinations.example.yaml"


def resolve_project_path(path):
    """Resolve a path relative to the project root, leaving absolute paths intact."""
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_settings(settings_path=None):
    """Load project settings; OSRM port prefers config/osrm_port.txt when present."""
    path = Path(settings_path) if settings_path else SETTINGS_PATH
    if not path.is_file():
        path = SETTINGS_EXAMPLE
    if not path.is_file():
        raise FileNotFoundError(
            f"Settings not found. Copy {SETTINGS_EXAMPLE} to {SETTINGS_PATH}"
        )

    settings = yaml.safe_load(path.read_text(encoding="utf-8"))
    osrm = settings.setdefault("osrm", {})
    if OSRM_PORT_FILE.is_file():
        osrm["port"] = int(OSRM_PORT_FILE.read_text(encoding="utf-8").strip())
    osrm.setdefault("host", "localhost")
    osrm.setdefault("port", 5000)
    settings.setdefault("defaults", {})
    return settings
