#!/usr/bin/env python3
"""Validate authored frame content and exports, not aesthetic quality."""

from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile


def fail(message: str) -> None:
    raise SystemExit(message)


def run_batch(binary: str, project: Path, requests: list[dict]) -> list[dict]:
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    try:
        for request in requests:
            handle.write(json.dumps(request) + "\n")
        handle.close()
        proc = subprocess.run(
            [binary, "call", "--project", str(project), "--request-file", handle.name],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        os.unlink(handle.name)
    results = []
    for line in proc.stdout.splitlines():
        if not line.startswith("{"):
            continue
        body = json.loads(line)
        if body.get("ok") is not True:
            fail(json.dumps(body, ensure_ascii=False))
        results.append(body["result"])
    if proc.returncode != 0 or len(results) != len(requests):
        fail(f"batch exit {proc.returncode} {len(results)}/{len(requests)}\n{proc.stderr[-1000:]}")
    return results


def media_timing(root: Path, expected: list[int]) -> dict:
    """Read animation control blocks; do not infer timing from average FPS."""
    final = root / "final"
    png = (final / "nezha-attack.apng").read_bytes()
    position = 8
    apng = []
    while position < len(png):
        length = struct.unpack_from(">I", png, position)[0]
        kind = png[position + 4 : position + 8]
        data = png[position + 8 : position + 8 + length]
        if kind == b"fcTL":
            numerator, denominator = struct.unpack_from(">HH", data, 20)
            apng.append(numerator * 1000 / (denominator or 100))
        position += length + 12
    if apng != expected:
        fail(f"APNG frame timing differs from project: {apng}")
    gif = (final / "nezha-attack.gif").read_bytes()
    position = 13 + (3 * (2 ** ((gif[10] & 7) + 1)) if gif[10] & 128 else 0)
    delays = []
    pending = 0

    def skip_blocks(pos):
        while gif[pos]:
            pos += gif[pos] + 1
        return pos + 1

    while position < len(gif):
        marker = gif[position]
        position += 1
        if marker == 0x3B:
            break
        if marker == 0x21:
            label = gif[position]
            position += 1
            if label == 0xF9:
                if gif[position] != 4:
                    fail("bad GIF graphic-control block")
                pending = int.from_bytes(gif[position + 2 : position + 4], "little") * 10
            position = skip_blocks(position)
        elif marker == 0x2C:
            packed = gif[position + 8]
            position += 9
            if packed & 128:
                position += 3 * (2 ** ((packed & 7) + 1))
            position += 1
            position = skip_blocks(position)
            delays.append(pending)
            pending = 0
        else:
            fail(f"unexpected GIF block {marker:#x}")
    if (
        len(delays) != len(expected)
        or any(abs(a - b) > 10 for a, b in zip(delays, expected))
        or abs(sum(delays) - sum(expected)) > 10
    ):
        fail(
            f"GIF frame timing does not preserve authored cadence within centisecond precision: {delays}"
        )
    return {"apngDelaysMs": apng, "gifDelaysMs": delays, "durationMs": sum(delays)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixelforge", default=os.environ.get("PIXELFORGE", "pixelforge"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    binary = shutil.which(args.pixelforge)
    if not binary:
        fail("set PIXELFORGE or pass --pixelforge")
    root = args.root.resolve()
    project = root / "final/nezha-attack.pxf.json"
    brief = json.loads((root / "brief.json").read_text())
    frames = json.loads((root / "source/poses.json").read_text())["frames"]
    expected = [f["delayMs"] for f in frames]
    scene = run_batch(binary, project, [{"tool": "scene"}])[0]
    if (scene["width"], scene["height"], scene["frameCount"]) != (128, 128, 12):
        fail("unexpected canvas/frame count")
    if [l["name"] for l in scene["layers"]] != brief["layers"]:
        fail("layer layout changed")
    if any(scene[k] for k in ["parts", "curves", "constraints"]):
        fail("this example must stay frame-authored without rig metadata")
    if [f["delayMs"] for f in scene["frames"]] != expected:
        fail("frame timing differs from explicit poses")
    if scene["activeFrame"] != 0:
        fail("project should reopen on the ready frame")
    tags = {t["name"]: t for t in scene["tags"]}
    if "attack_right" not in tags or (tags["attack_right"]["from"], tags["attack_right"]["to"]) != (
        0,
        11,
    ):
        fail("attack tag is incomplete")
    views = run_batch(
        binary,
        project,
        [
            {"tool": "previewFrame", "params": {"frame": i, "layer": l}}
            for i in range(12)
            for l in range(4)
        ],
    )
    lower = []
    shaft = []
    for i, f in enumerate(frames):
        for l in range(4):
            if not any(views[i * 4 + l]["pixels"]):
                fail(f"empty layer {l} on frame {i}")
        leg = views[i * 4 + 1]["pixels"]
        for x, y in [f["feet"]["front"], f["feet"]["rear"]]:
            if leg[(y - 7) * 128 + x] == 0:
                fail(f"ankle/wheel connection is empty on frame {i}")
        changed = sum(a != b for a, b in zip(views[1]["pixels"], leg))
        if i and not changed:
            fail(f"lower body is frozen on frame {i}")
        lower.append({"frame": i, "changedLegLayerPixelsVsReady": changed})
        hx, hy = f["weapon"]["grip"]
        theta = math.radians(f["weapon"]["angleDegrees"])
        ux, uy = math.cos(theta), math.sin(theta)
        gear = views[i * 4 + 3]["pixels"]
        for t in range(-21, 29):
            x, y = round(hx + t * ux), round(hy + t * uy)
            if gear[y * 128 + x] == 0:
                fail(f"spear has a hole on frame {i} at {x},{y}")
        shaft.append({"frame": i, "centerline": "continuous"})
    seed = run_batch(binary, root / "source/body.pxf.json", [{"tool": "scene"}])[0]
    if seed["frameCount"] != 1 or seed["paletteHash"] != scene["paletteHash"]:
        fail("body seed or palette changed unexpectedly")
    atlas = root / "final/nezha-attack.atlas.json"
    sheet = root / "final/nezha-attack-sheet.png"
    checked = subprocess.run(
        [
            binary,
            "validate-atlas",
            "--atlas",
            str(atlas),
            "--sheet",
            str(sheet),
            "--four-direction",
            "off",
        ],
        capture_output=True,
        text=True,
    )
    if checked.returncode:
        fail(checked.stdout + checked.stderr)
    media = media_timing(root, expected)
    stamp = json.loads((root / "reports/stamp.json").read_text())
    for name, digest in stamp["sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            fail(f"hash mismatch: {name}")
    report = {
        "status": "passed",
        "method": "frame-by-frame",
        "frameCount": 12,
        "durationMs": sum(expected),
        "rigMetadata": "absent",
        "lowerBody": lower,
        "rigidShaft": shaft,
        "media": media,
        "aestheticApproval": False,
        "limits": "Checks cover pixel continuity, structure, timing and artifact identity, not naturalness or artistic approval.",
    }
    (root / "reports/validate.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Frame animation checks passed: 12 frames,", sum(expected), "ms; no rig metadata")


if __name__ == "__main__":
    main()
