"""Identity of a model run.

Numeric assumptions stay in config/parameters.json. This module only names the
code version and fingerprints that file, so a quoted result can be tied back
to both.
"""
from __future__ import annotations

import hashlib
import os

MODEL_VERSION = "0.7.1"

_PARAMETERS = os.path.join(os.path.dirname(__file__), "..", "config", "parameters.json")


def parameters_sha256(path: str | None = None) -> str:
    """SHA-256 of the parameter file bytes, not of any session override."""
    path = path or _PARAMETERS
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        digest.update(fh.read())
    return digest.hexdigest()


def stamp(path: str | None = None) -> dict:
    return {
        "model_version": MODEL_VERSION,
        "parameters_sha256": parameters_sha256(path),
    }
