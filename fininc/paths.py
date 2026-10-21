"""Project folders. Everything is resolved from the repository root, so scripts run from anywhere."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"

DOCS = ROOT / "docs"
FIGURES = DOCS / "figures"
DASHBOARD = ROOT / "dashboard"
POWERBI = ROOT / "powerbi"
NOTEBOOKS = ROOT / "notebooks"
TEMPLATES = Path(__file__).resolve().parent / "templates"

MANIFEST = RAW / "MANIFEST.json"


def ensure_dirs() -> None:
    """Create the output folders if they do not exist yet."""
    for folder in (INTERIM, PROCESSED, FIGURES, DASHBOARD, POWERBI):
        folder.mkdir(parents=True, exist_ok=True)
