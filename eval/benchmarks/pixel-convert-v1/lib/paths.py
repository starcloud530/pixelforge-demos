"""Paths for the benchmark tree. This file lives in lib/."""

from __future__ import annotations

import json
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
BENCH_DIR = LIB_DIR.parent
REPO_ROOT = BENCH_DIR.parents[2]
PROTOCOL_PATH = BENCH_DIR / "protocol.json"
MANIFEST_PATH = BENCH_DIR / "manifest.json"
FIELDS_PATH = BENCH_DIR / "templates" / "fields.json"
HASHES_PATH = BENCH_DIR / "fixtures" / "hashes.json"
RECORD_DIR = BENCH_DIR / "records" / "v1" / "center-sample"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def protocol() -> dict:
    return load_json(PROTOCOL_PATH)


def manifest() -> dict:
    return load_json(MANIFEST_PATH)


def fields() -> dict:
    return load_json(FIELDS_PATH)


def fixture_path(fixture: dict) -> Path:
    root = REPO_ROOT if fixture["root"] == "repo" else BENCH_DIR
    return root / fixture["file"]
