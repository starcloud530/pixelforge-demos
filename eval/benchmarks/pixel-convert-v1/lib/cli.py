"""Call the installed pixelforge CLI. No engine source lives in this repo."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path


class CliError(RuntimeError):
    pass


def resolve_bin() -> str:
    chosen = os.environ.get("PIXELFORGE_BIN", "").strip()
    if chosen:
        if not Path(chosen).is_file():
            raise CliError(f"PIXELFORGE_BIN is not a file: {chosen}")
        return chosen
    found = shutil.which("pixelforge")
    if not found:
        raise CliError(
            "pixelforge is not on PATH; set PIXELFORGE_BIN to a CLI that has convert"
        )
    return found


def run_cli(
    binary: str, args: list[str], timeout: int = 60
) -> tuple[int, str, str, int]:
    started = time.perf_counter()
    proc = subprocess.run(
        [binary, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    elapsed = int(round((time.perf_counter() - started) * 1000))
    return proc.returncode, proc.stdout, proc.stderr, elapsed


def parse_result(stdout: str) -> dict:
    for line in stdout.splitlines():
        text = line.strip()
        if not text.startswith("{"):
            continue
        body = json.loads(text)
        if isinstance(body, dict) and "result" in body:
            return body["result"]
    raise CliError("convert stdout has no JSON result")


def convert_argv(
    source: Path,
    output: Path,
    width: int,
    height: int,
    max_colors: int,
    engine: str = "center-sample",
) -> list[str]:
    return [
        "convert",
        "--file",
        str(source),
        "--output",
        str(output),
        "--width",
        str(width),
        "--height",
        str(height),
        "--engine",
        engine,
        "--palette-strategy",
        "limit",
        "--max-colors",
        str(max_colors),
    ]


def portable_argv(
    fixture_file: str,
    row_id: str,
    width: int,
    height: int,
    max_colors: int,
    engine: str = "center-sample",
) -> list[str]:
    project = f"eval/runs/pixel-convert-v1/projects/{row_id}.json"
    return [
        "pixelforge",
        "convert",
        "--file",
        fixture_file,
        "--output",
        project,
        "--width",
        str(width),
        "--height",
        str(height),
        "--engine",
        engine,
        "--palette-strategy",
        "limit",
        "--max-colors",
        str(max_colors),
    ]
