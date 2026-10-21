"""Shared fixtures. The data tests read the committed outputs; the slow tests rebuild them from the raw files."""

from __future__ import annotations

import pytest

from fininc import paths
from fininc.results import Results, load


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: rebuilds tables from the raw files (about a minute)")


@pytest.fixture(scope="session")
def results() -> Results:
    if not (paths.PROCESSED / "summary.json").exists():
        pytest.skip("run `python -m fininc all` first")
    return load()


@pytest.fixture(scope="session")
def units(results):
    return results.units
