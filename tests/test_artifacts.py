"""Inspect the actual built distributions when MIMEGUESS_DIST_DIR is supplied."""

from __future__ import annotations

import email
import os
import tarfile
import zipfile
from pathlib import Path

import pytest


def test_built_distributions_contain_only_intended_files() -> None:
    folder = os.environ.get("MIMEGUESS_DIST_DIR")
    if folder is None:
        pytest.skip("set MIMEGUESS_DIST_DIR to inspect built artifacts")
    wheel = Path(folder) / "mimeguess-1.0.0-py3-none-any.whl"
    sdist = Path(folder) / "mimeguess-1.0.0.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert all(n.startswith(("mimeguess/", "mimeguess-1.0.0.dist-info/")) for n in names)
        assert "mimeguess/py.typed" in names
        assert "mimeguess/_data.json.gz" in names
        for notice in ("LICENSE", "LICENSES/mime-db.txt", "LICENSES/mime-types.txt"):
            assert f"mimeguess-1.0.0.dist-info/licenses/{notice}" in names
        metadata = email.message_from_bytes(archive.read("mimeguess-1.0.0.dist-info/METADATA"))
        assert metadata["Version"] == "1.0.0"
        assert metadata["Requires-Python"] == ">=3.10"
        assert metadata["License-Expression"] == "MIT"
        assert "Development Status :: 5 - Production/Stable" in metadata.get_all("Classifier", [])
        assert all("extra == 'dev'" in value for value in metadata.get_all("Requires-Dist", []))
    with tarfile.open(sdist) as archive:
        names += archive.getnames()
        base = "mimeguess-1.0.0/"
        for name in ("README.md", "GUIDE.md", "CHANGELOG.md", "LICENSE", "pyproject.toml"):
            assert base + name in archive.getnames()
        assert base + "src/mimeguess/py.typed" in archive.getnames()
        assert base + "data/MANIFEST.json" in archive.getnames()
        for notice in ("mime-db.txt", "mime-types.txt"):
            assert base + "LICENSES/" + notice in archive.getnames()
    for name in names:
        assert not any(
            bad in name for bad in ("__pycache__", ".pyc", ".venv", "scratch", ".pytest")
        )
        assert not name.endswith(("mimesniff.html", "rfc9110.txt", ".tgz", "mime-db-1.54.0.json"))
        assert "CERT-" not in name and "IMPROVEMENTS" not in name
