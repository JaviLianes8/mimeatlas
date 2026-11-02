"""Run the pinned Node.js reference package from the fetched tarballs."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = Path(os.environ.get("MIMEGUESS_DATA_DIR", str(ROOT / "data")))
PROGRAM = """
const m = require('mime-types');
const db = require('mime-db');
const counts = {};
for (const row of Object.values(db)) {
  for (const ext of row.extensions || []) counts[ext] = (counts[ext] || 0) + 1;
}
const conflicts = Object.fromEntries(Object.keys(counts).sort()
  .filter(e => counts[e] > 1).map(e => [e, m.types[e]]));
console.log(JSON.stringify({types: m.types, extensions: m.extensions, conflicts}));
"""


def reference() -> str:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js is required for the reference comparison")
    manifest = json.loads((ROOT / "data" / "MANIFEST.json").read_text(encoding="utf-8"))
    work = FOLDER / "reference"
    for package, version in (("mime-types", "3.0.2"), ("mime-db", "1.54.0")):
        name = f"{package}-{version}.tgz"
        data = (FOLDER / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != manifest[name]["sha256"]:
            raise ValueError("reference archive does not match the manifest")
        target = work / "node_modules" / package
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive.getmembers():
                relative = Path(member.name).relative_to("package")
                destination = target / relative
                if not destination.resolve().is_relative_to(target.resolve()):
                    raise ValueError("reference archive path escapes its directory")
                if member.isfile():
                    handle = archive.extractfile(member)
                    assert handle is not None
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(handle.read())
    result = subprocess.run(
        [node, "-e", PROGRAM], cwd=work, capture_output=True, text=True, check=True, timeout=60
    )
    return result.stdout


if __name__ == "__main__":
    print(reference(), end="")
