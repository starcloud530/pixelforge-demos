#!/usr/bin/env python3
"""Original program art via the pinned PixelForge CLI, never v1 fixture inputs."""

from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pixel-convert-v1"))
from lib.cli import resolve_bin
from lib.pngutil import read_rgba
from lib.splits import future_split

PIN = "9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d"
# Coordinates are authored in a 256px source space. Targets deliberately
# widen essential narrow details to >=1px; these are proxy labels, not artist edits.
DESIGNS = [
    (
        "antenna-bot",
        [
            (96, 72, 64, 48, 2),
            (88, 120, 80, 64, 3),
            (92, 184, 28, 44, 2),
            (140, 184, 28, 44, 2),
            (68, 124, 20, 48, 4),
            (168, 124, 20, 48, 4),
        ],
        [
            (108, 88, 12, 12, 7),
            (140, 88, 12, 12, 7),
            (112, 148, 32, 12, 5),
            (124, 40, 1, 32, 4),
        ],
        ["single-pixel antenna", "separate feet", "two eyes"],
    ),
    (
        "pennant-keeper",
        [
            (100, 56, 56, 48, 4),
            (92, 104, 72, 84, 5),
            (92, 188, 24, 40, 2),
            (140, 188, 24, 40, 2),
            (164, 112, 28, 16, 4),
            (192, 48, 4, 176, 2),
        ],
        [
            (196, 48, 36, 24, 6),
            (108, 72, 12, 8, 7),
            (140, 72, 8, 8, 7),
            (192, 48, 1, 176, 2),
        ],
        ["pennant and pole", "arm joins pole", "leg gap"],
    ),
    (
        "ring-diver",
        [
            (88, 48, 80, 64, 2),
            (80, 112, 96, 76, 3),
            (80, 188, 32, 36, 4),
            (144, 188, 32, 36, 4),
            (40, 124, 40, 24, 5),
            (176, 124, 40, 24, 5),
        ],
        [
            (100, 64, 56, 28, 7),
            (104, 68, 48, 20, 1),
            (112, 128, 32, 40, 6),
            (120, 136, 16, 24, 0),
        ],
        ["visor rim", "torso window", "wide fins"],
    ),
    (
        "lantern-moth",
        [
            (36, 88, 64, 104, 5),
            (156, 88, 64, 104, 5),
            (100, 64, 56, 132, 2),
            (108, 196, 12, 32, 4),
            (136, 196, 12, 32, 4),
        ],
        [
            (60, 112, 24, 56, 6),
            (172, 112, 24, 56, 6),
            (108, 80, 12, 12, 7),
            (136, 80, 12, 12, 7),
            (112, 40, 1, 24, 4),
            (144, 40, 1, 24, 4),
        ],
        ["paired antennae", "two wing panels", "body between wings"],
    ),
    (
        "twin-ear-scout",
        [
            (76, 28, 24, 52, 4),
            (156, 28, 24, 52, 4),
            (76, 80, 104, 56, 4),
            (88, 136, 80, 60, 6),
            (88, 196, 24, 32, 2),
            (144, 196, 24, 32, 2),
        ],
        [
            (88, 92, 20, 12, 7),
            (148, 92, 20, 12, 7),
            (120, 112, 16, 8, 5),
            (168, 148, 1, 64, 3),
            (168, 148, 44, 12, 3),
        ],
        ["two long ears", "thin side tool", "separated boots"],
    ),
    (
        "fork-crab",
        [
            (64, 96, 128, 72, 3),
            (40, 72, 24, 60, 4),
            (192, 72, 24, 60, 4),
            (64, 168, 20, 40, 2),
            (104, 168, 20, 48, 2),
            (144, 168, 20, 48, 2),
            (184, 168, 20, 40, 2),
        ],
        [
            (80, 80, 16, 28, 4),
            (160, 80, 16, 28, 4),
            (84, 84, 8, 8, 7),
            (164, 84, 8, 8, 7),
            (40, 40, 8, 32, 5),
            (56, 40, 8, 32, 5),
            (192, 40, 8, 32, 5),
            (208, 40, 8, 32, 5),
        ],
        ["forked claws", "eye stalks", "four leg gaps"],
    ),
]


def cli(binary, *args):
    proc = subprocess.run(
        [binary, *map(str, args)], capture_output=True, text=True, check=True
    )
    for line in proc.stdout.splitlines():
        if line.startswith("{") and json.loads(line).get("ok") is False:
            raise RuntimeError(line)
    return proc


def requests(rects, size, silhouette=False):
    out = []
    for x, y, w, h, c in rects:
        # Target proxy construction is fixed before seeing baseline outputs.
        x, y = x * size // 256, y * size // 256
        w, h = max(1, w * size // 256), max(1, h * size // 256)
        tool = "eraseRect" if c == 0 else "fillRect"
        params = dict(x=x, y=y, width=w, height=h)
        if c:
            params["colorIndex"] = 1 if silhouette else c
        out.append(dict(tool=tool, params=params))
    return out


def generate(dest, binary):
    dest.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix="pf-pair-art-") as temp:
        work = Path(temp)
        for i, (name, body, details, keep) in enumerate(DESIGNS, 1):
            ident = f"pf-pair-{i:03d}-{name}"
            images = []
            for size in (256, 64, 128):
                project = work / f"{ident}-{size}.json"
                cli(
                    binary,
                    "new",
                    "--width",
                    size,
                    "--height",
                    size,
                    "--output",
                    project,
                )
                # Staged authoring. Inspection previews remain local, not in git.
                for stage, rects, sil in (
                    ("silhouette", body, True),
                    ("flats", body, False),
                    ("details", details, False),
                ):
                    req = work / "requests.json"
                    req.write_text(json.dumps(requests(rects, size, sil)))
                    cli(binary, "call", "--project", project, "--request-file", req)
                    cli(
                        binary,
                        "preview",
                        "--project",
                        project,
                        "--scale",
                        4,
                        "--output",
                        work / f"{ident}-{size}-{stage}.png",
                    )
                outdir = work / f"export-{ident}-{size}"
                cli(binary, "export", "png", "--project", project, "--out-dir", outdir)
                src = next(outdir.glob("*.png"))
                role = "source" if size == 256 else f"target-{size}"
                rel = f"png/{ident}-{role}.png"
                path = dest / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, path)
                images.append(
                    dict(
                        role=role,
                        file=rel,
                        width=size,
                        height=size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    )
                )
            failure_images = []
            if i == 1:
                for size in (64, 128):
                    project = work / f"failure-{size}.json"
                    cli(
                        binary,
                        "convert",
                        "--file",
                        dest / images[0]["file"],
                        "--output",
                        project,
                        "--width",
                        size,
                        "--height",
                        size,
                        "--engine",
                        "center-sample",
                        "--palette-strategy",
                        "limit",
                        "--max-colors",
                        16,
                    )
                    outdir = work / f"failure-export-{size}"
                    cli(
                        binary,
                        "export",
                        "png",
                        "--project",
                        project,
                        "--out-dir",
                        outdir,
                    )
                    rel = f"failures/{ident}-center-sample-{size}.png"
                    path = dest / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(next(outdir.glob("*.png")), path)
                    # Direct pixel fact, not a human defect/preference label.
                    x, y = 124 * size // 256, 48 * size // 256
                    fw, fh, rgba = read_rgba(path)
                    _, _, target = read_rgba(
                        dest / images[1 if size == 64 else 2]["file"]
                    )
                    assert (
                        rgba[(y * fw + x) * 4 + 3] == 0
                        and target[(y * fw + x) * 4 + 3] == 255
                    )
                    failure_images.append(
                        dict(
                            file=rel,
                            width=size,
                            height=size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            method="center-sample",
                            observation=dict(
                                pixel=[x, y],
                                candidate_alpha=0,
                                proxy_target_alpha=255,
                                feature="antenna",
                            ),
                            human_severity=None,
                        )
                    )
            records.append(
                dict(
                    character_id=ident,
                    source_kind="original-program-art",
                    style="geometric-flat-proxy",
                    license="CC-BY-4.0",
                    attribution="PixelForge / starcloud530 (AI-assisted original program art)",
                    split="seed-unreviewed",
                    intended_split=future_split(ident),
                    training_eligible=False,
                    target_status="procedural-proxy-not-artist-corrected",
                    features_to_keep=keep,
                    images=images,
                    failure_samples=failure_images,
                )
            )
    manifest = dict(
        dataset_id="pixel-convert-pairs-v0",
        cli_commit=PIN,
        license_url="https://creativecommons.org/licenses/by/4.0/",
        provenance="Original geometry in generate.py; no external images or protocol-v1 inputs",
        characters=records,
    )
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    generate(args.output, resolve_bin())


if __name__ == "__main__":
    main()
