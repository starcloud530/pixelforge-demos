"""Load fixture RGBA and write the procedural PNGs."""

from __future__ import annotations

import json

from .paths import BENCH_DIR, HASHES_PATH, fixture_path, manifest
from .pngutil import encode_rgba, read_rgba, write_rgba
from .record import sha256_bytes
from .render import render_fixture, validate_scene


def load_rgba(fixture: dict) -> tuple[int, int, bytes]:
    if fixture["source_kind"] == "procedural":
        rgba = render_fixture(fixture)
        return fixture["width"], fixture["height"], rgba
    width, height, rgba = read_rgba(fixture_path(fixture))
    if (width, height) != (fixture["width"], fixture["height"]):
        raise ValueError(f"{fixture['id']} size {width}x{height} does not match the manifest")
    return width, height, rgba


def fixture_errors() -> list[str]:
    errors = []
    seen = set()
    required = set(manifest()["categories_required"])
    covered = set()
    for fixture in manifest()["fixtures"]:
        if fixture["id"] in seen or fixture["character_id"] in seen:
            errors.append(f"duplicate id {fixture['id']}")
        seen.add(fixture["id"])
        if fixture["character_id"] != fixture["id"]:
            errors.append(f"{fixture['id']} v1 character_id must equal the fixture id")
        if fixture["split"] != "protocol-v1":
            errors.append(f"{fixture['id']} must stay on split protocol-v1")
        covered.update(fixture["categories"])
        if fixture["source_kind"] == "procedural":
            rgba = render_fixture(fixture)
            errors.extend(validate_scene(fixture, rgba))
        else:
            try:
                load_rgba(fixture)
            except (OSError, ValueError) as exc:
                errors.append(str(exc))
    missing = required - covered
    if missing:
        errors.append("missing categories: " + ", ".join(sorted(missing)))
    return errors


def hash_document() -> dict:
    files = {}
    for fixture in manifest()["fixtures"]:
        if fixture["source_kind"] == "procedural":
            width, height, rgba = fixture["width"], fixture["height"], render_fixture(fixture)
            png = encode_rgba(width, height, rgba)
            png_sha = sha256_bytes(png)
        else:
            blob = fixture_path(fixture).read_bytes()
            width, height, rgba = read_rgba(fixture_path(fixture))
            png = blob
            png_sha = sha256_bytes(blob)
        files[fixture["id"]] = {
            "path": fixture["file"],
            "root": fixture["root"],
            "width": width,
            "height": height,
            "png_sha256": png_sha,
            "rgba_sha256": sha256_bytes(rgba),
            "png_bytes": len(png),
        }
    return {"benchmark_id": "pixel-convert-v1", "files": files}


def write_fixtures() -> dict:
    errors = fixture_errors()
    if errors:
        raise SystemExit("fixture errors:\n" + "\n".join(errors))
    for fixture in manifest()["fixtures"]:
        if fixture["source_kind"] != "procedural":
            continue
        rgba = render_fixture(fixture)
        write_rgba(fixture_path(fixture), fixture["width"], fixture["height"], rgba)
    document = hash_document()
    HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    HASHES_PATH.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return document


def locked_hashes() -> dict:
    return json.loads(HASHES_PATH.read_text(encoding="utf-8"))
