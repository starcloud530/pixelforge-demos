#!/usr/bin/env python3
"""Build the side-view lunge thrust with the PixelForge CLI.

The binary must be compiled from engine SHA
b647dc1631e639b34279e6027825430b0a3ce1b2. That commit still prints version
0.1.0-rc.5; the script checks the bundled action-motion text instead of
trusting the version string.

Pixels are written only by the CLI. This file picks keys, footprint cells,
and export paths. It does not rasterize frames itself.

    PIXELFORGE=/path/to/pixelforge python3 demos/spear-lunge/build.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

ENGINE_SHA = "b647dc1631e639b34279e6027825430b0a3ce1b2"
WIDTH = 128
HEIGHT = 128
FRAMES = 16
FPS = 12

# Rest joints, canvas cells. Side view, facing right. Both feet on y=116.
TORSO = (46, 78)
PELVIS = (46, 78)
HEAD = (50, 50)
SPEAR = (70, 66)
UPPER_NEAR = (56, 54)
ELBOW_NEAR = (64, 68)
UPPER_FAR = (52, 56)
ELBOW_FAR = (58, 76)
THIGH_NEAR = (50, 82)
KNEE_NEAR = (66, 100)
THIGH_FAR = (42, 82)
KNEE_FAR = (24, 102)
RIBBON_ROOT = (34, 78)
RIBBON_MID = (24, 81)
RIBBON_TIP = (14, 85)
FLAME = (104, 50)

# Sparse body keys. Spear translation carries the pelvis plus this extra.
# frame: px, py, pelvis_rot, torso_rot, spear_extra_x, spear_extra_y, spear_rot
BODY_KEYS = {
    0: (0, 0, 0, 0, 0, 0, 0),
    3: (-2, 4, -3, -10, -3, 1, -14),
    5: (3, 3, 0, 0, 0, 0, -2),
    7: (6, 1, 2, 12, 4, 1, 18),
    9: (7, 0, 1, 6, 2, 0, 14),
    12: (5, 0, 0, 3, 0, 0, 8),
    15: (4, 0, 0, 2, 0, 0, 6),
}

LAYERS = [
    "ground",
    "ribbon-tip",
    "ribbon-mid",
    "ribbon-root",
    "thigh-far",
    "shin-far",
    "upper-far",
    "fore-far",
    "hand-far",
    "pelvis",
    "torso",
    "thigh-near",
    "shin-near",
    "spear",
    "tassel-root",
    "tassel-tip",
    "flame",
    "upper-near",
    "fore-near",
    "hand-near",
    "head",
]

MECHANICS_HIDDEN = {
    "ribbon-tip",
    "ribbon-mid",
    "ribbon-root",
    "tassel-root",
    "tassel-tip",
    "flame",
}

KEY_POSES = [
    (0, "ready"),
    (3, "charge"),
    (5, "stride"),
    (7, "thrust"),
    (9, "follow"),
    (15, "settle"),
]


class Cli:
    def __init__(self, binary: str, project: Path) -> None:
        self.binary = binary
        self.project = project

    def run(self, args: list[str]) -> dict:
        result, error = self.try_run(args)
        if error is not None or result is None:
            raise SystemExit(error or f"failed: {args}")
        return result

    def try_run(self, args: list[str]) -> tuple[dict | None, str | None]:
        cmd_args = list(args)
        if cmd_args[0] != "new":
            cmd_args = self._with_project(cmd_args)
        proc = subprocess.run(
            [self.binary, *cmd_args],
            check=False,
            capture_output=True,
            text=True,
        )
        lines = [line for line in proc.stdout.splitlines() if line.startswith("{")]
        if proc.returncode != 0 or not lines:
            return None, f"exit {proc.returncode}: {' '.join(cmd_args)}\n{proc.stderr}\n{proc.stdout}"
        body = json.loads(lines[-1])
        if body.get("ok") is not True:
            return None, json.dumps(body, ensure_ascii=False)
        return body["result"], None

    def batch(self, requests: list[dict]) -> list[dict]:
        results, error = self.try_batch(requests)
        if error is not None or results is None:
            raise SystemExit(error or "batch failed")
        return results

    def try_batch(self, requests: list[dict]) -> tuple[list[dict] | None, str | None]:
        if not requests:
            return [], None
        handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        try:
            for request in requests:
                handle.write(json.dumps(request, ensure_ascii=False) + "\n")
            handle.close()
            proc = subprocess.run(
                [self.binary, "call", "--project", str(self.project), "--request-file", handle.name],
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
                return None, json.dumps(body, ensure_ascii=False)
            results.append(body["result"])
        if proc.returncode != 0 or len(results) != len(requests):
            return None, f"exit {proc.returncode}: batch {len(results)}/{len(requests)}\n{proc.stderr[-1500:]}\n{proc.stdout[-1500:]}"
        return results, None

    def _with_project(self, args: list[str]) -> list[str]:
        for index, arg in enumerate(args):
            if arg.startswith("--"):
                return [*args[:index], "--project", str(self.project), *args[index:]]
        return [*args, "--project", str(self.project)]


def require_engine(binary: str) -> str:
    proc = subprocess.run([binary, "--version"], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)
    version = proc.stdout.strip()
    skill = subprocess.run(
        [binary, "skills", "read", "pixel-art-craft", "references/action-motion.md"],
        check=False,
        capture_output=True,
        text=True,
    )
    if skill.returncode != 0 or "跨步刺击" not in skill.stdout or "不是物理模拟" not in skill.stdout and "物理模拟" not in skill.stdout:
        raise SystemExit("this pixelforge binary does not contain the pinned action-motion reference")
    if "跨步刺击" not in skill.stdout:
        raise SystemExit("action-motion.md in this binary is missing 跨步刺击")
    return version


def load_brief(path: Path) -> dict:
    brief = json.loads(path.read_text(encoding="utf-8"))
    if brief["engineSha"] != ENGINE_SHA:
        raise SystemExit("brief engine SHA does not match the script pin")
    if brief["canvas"] != [WIDTH, HEIGHT] or brief["frameCount"] != FRAMES or brief["fps"] != FPS:
        raise SystemExit("brief canvas, frame count, or fps does not match the script")
    return brief


def setup_palette(cli: Cli, brief: dict) -> dict[str, int]:
    names = list(brief["palette"])
    indexes: dict[str, int] = {}
    for offset, name in enumerate(names[:8]):
        red, green, blue = brief["palette"][name]
        cli.run(["palette", "set", "--index", str(offset + 1), "--r", str(red), "--g", str(green), "--b", str(blue)])
        indexes[name] = offset + 1
    for name in names[8:]:
        red, green, blue = brief["palette"][name]
        result = cli.run(["palette", "add", "--r", str(red), "--g", str(green), "--b", str(blue)])
        indexes[name] = int(result["index"])
    return indexes


def setup_layers(cli: Cli) -> dict[str, int]:
    cli.run(["layer", "rename", "--name", LAYERS[0]])
    for name in LAYERS[1:]:
        cli.run(["layer", "add", "--name", name])
    document = json.loads(cli.project.read_text(encoding="utf-8"))
    found = [layer["name"] for layer in document["layers"]]
    if found != LAYERS:
        raise SystemExit(f"layer order {found}")
    return {name: index for index, name in enumerate(found)}


class Ink:
    def __init__(self) -> None:
        self.cells: dict[int, dict[int, set[tuple[int, int]]]] = defaultdict(lambda: defaultdict(set))

    def dot(self, layer: int, x: int, y: int, color: int) -> None:
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            raise SystemExit(f"paint off canvas {x},{y}")
        for other in self.cells[layer].values():
            other.discard((x, y))
        self.cells[layer][color].add((x, y))

    def rect(self, layer: int, x: int, y: int, width: int, height: int, color: int) -> None:
        for row in range(y, y + height):
            for column in range(x, x + width):
                self.dot(layer, column, row, color)

    def local_rect(self, layer: int, origin: tuple[int, int], x: int, y: int, width: int, height: int, color: int) -> None:
        self.rect(layer, origin[0] + x, origin[1] + y, width, height, color)

    def line(self, layer: int, start: tuple[int, int], end: tuple[int, int], color: int) -> None:
        for point in bresenham(start, end):
            self.dot(layer, point[0], point[1], color)

    def capsule(self, layer: int, start: tuple[int, int], end: tuple[int, int], radius: int, shade: int, mid: int, light: int | None = None) -> None:
        self._disk(layer, start, end, radius, shade)
        if radius >= 1:
            self._disk(layer, start, end, radius - 1, mid)
        if light is not None:
            self.line(layer, (start[0] + 1, start[1] - 1), (end[0] + 1, end[1] - 1), light)

    def _disk(self, layer: int, start: tuple[int, int], end: tuple[int, int], radius: int, color: int) -> None:
        for x, y in bresenham(start, end):
            for oy in range(-radius, radius + 1):
                for ox in range(-radius, radius + 1):
                    if max(abs(ox), abs(oy)) <= radius:
                        self.dot(layer, x + ox, y + oy, color)

    def requests(self) -> list[dict]:
        requests = []
        for layer, colors in self.cells.items():
            for color, cells in colors.items():
                for x, y, width, height in horizontal_runs(cells):
                    requests.append(
                        {
                            "tool": "fillRect",
                            "params": {
                                "layer": layer,
                                "x": x,
                                "y": y,
                                "width": width,
                                "height": height,
                                "colorIndex": color,
                            },
                        }
                    )
        return requests


def bresenham(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    x0, y0 = start
    x1, y1 = end
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        doubled = 2 * err
        if doubled > -dy:
            err -= dy
            x += sx
        if doubled < dx:
            err += dx
            y += sy
    return points


def horizontal_runs(cells: set[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    rows: dict[int, list[int]] = defaultdict(list)
    for x, y in cells:
        rows[y].append(x)
    runs = []
    for y, xs in rows.items():
        ordered = sorted(set(xs))
        start = previous = ordered[0]
        for x in ordered[1:]:
            if x == previous + 1:
                previous = x
                continue
            runs.append((start, y, previous - start + 1, 1))
            start = previous = x
        runs.append((start, y, previous - start + 1, 1))
    return runs


def paint(ink: Ink, layer: dict[str, int], color: dict[str, int]) -> None:
    c = color
    L = layer
    # Ground is a contact ruler. It is not a foot and it has no part.
    ink.rect(L["ground"], 12, 117, 104, 1, c["ground"])

    # Far leg, bent back, darker because it sits on the shadow side.
    ink.capsule(L["thigh-far"], THIGH_FAR, KNEE_FAR, 2, c["trouser_shade"], c["trouser_shade"], None)
    ink.capsule(L["shin-far"], KNEE_FAR, (30, 116), 2, c["boot_shade"], c["trouser_shade"], None)
    ink.rect(L["shin-far"], 26, 108, 10, 9, c["boot_shade"])
    ink.dot(L["shin-far"], 30, 116, c["boot_shade"])

    # Far arm, low elbow, hand at the rear grip.
    ink.capsule(L["upper-far"], UPPER_FAR, ELBOW_FAR, 1, c["tunic_shade"], c["tunic"], None)
    ink.capsule(L["fore-far"], ELBOW_FAR, SPEAR, 1, c["leather"], c["skin_shade"], None)
    ink.rect(L["fore-far"], 60, 70, 6, 4, c["gold_shade"])
    paint_hand(ink, L["hand-far"], SPEAR, c["skin_shade"], c["leather"], c["ink"])

    # Pelvis and torso. Waist origin is shared. Clothing covers the torso.
    ink.local_rect(L["pelvis"], PELVIS, -10, -2, 18, 12, c["trouser"])
    ink.local_rect(L["pelvis"], PELVIS, -10, -2, 5, 12, c["trouser_shade"])
    ink.local_rect(L["pelvis"], PELVIS, -12, -4, 4, 16, c["gold_shade"])
    ink.local_rect(L["pelvis"], PELVIS, 2, 6, 6, 4, c["trouser_shade"])

    ink.local_rect(L["torso"], TORSO, -8, -24, 16, 24, c["tunic"])
    ink.local_rect(L["torso"], TORSO, -8, -22, 5, 20, c["tunic_shade"])
    ink.local_rect(L["torso"], TORSO, 4, -26, 10, 8, c["tunic"])
    ink.local_rect(L["torso"], TORSO, 6, -18, 5, 12, c["tunic_light"])
    ink.local_rect(L["torso"], TORSO, -2, -26, 10, 3, c["gold"])
    ink.local_rect(L["torso"], TORSO, -8, -4, 18, 4, c["gold_shade"])
    ink.local_rect(L["torso"], TORSO, -6, -3, 14, 2, c["gold"])
    ink.local_rect(L["torso"], TORSO, 8, -24, 4, 6, c["metal"])

    # Near leg steps forward. Boot includes the sole cell.
    ink.capsule(L["thigh-near"], THIGH_NEAR, KNEE_NEAR, 2, c["trouser_shade"], c["trouser"], c["boot_light"])
    ink.capsule(L["shin-near"], KNEE_NEAR, (56, 116), 2, c["boot"], c["trouser"], c["boot_light"])
    ink.rect(L["shin-near"], 50, 106, 12, 11, c["boot"])
    ink.rect(L["shin-near"], 52, 108, 6, 6, c["boot_light"])
    ink.dot(L["shin-near"], 56, 116, c["boot"])

    # Spear, rigid fire-tip metal, knot where the tassel will hang.
    ink.capsule(L["spear"], SPEAR, (96, 54), 1, c["metal_shade"], c["metal"], c["metal_light"])
    ink.capsule(L["spear"], (96, 54), FLAME, 2, c["metal_shade"], c["metal_light"], c["teeth"])
    ink.rect(L["spear"], 94, 52, 4, 4, c["gold"])
    ink.dot(L["spear"], 70, 66, c["leather"])
    ink.dot(L["spear"], 84, 59, c["leather"])

    # Tassel hangs off the knot. Two segments so the free end can lag.
    ink.capsule(L["tassel-root"], (96, 54), (94, 62), 1, c["tassel_shade"], c["tassel"], c["ribbon_light"])
    ink.capsule(L["tassel-tip"], (94, 62), (93, 69), 1, c["tassel_shade"], c["fire"], None)

    # Flame stays on the tip. It is part of the head of the spear, not a cover over the body.
    ink.line(L["flame"], FLAME, (108, 47), c["fire"])
    ink.line(L["flame"], FLAME, (107, 49), c["fire_light"])
    ink.dot(L["flame"], 106, 48, c["fire_shade"])
    ink.dot(L["flame"], 109, 46, c["fire_light"])

    # Near arm over the shaft.
    ink.capsule(L["upper-near"], UPPER_NEAR, ELBOW_NEAR, 2, c["tunic_shade"], c["tunic"], c["tunic_light"])
    ink.capsule(L["fore-near"], ELBOW_NEAR, (84, 59), 1, c["skin_shade"], c["skin"], c["skin_light"])
    ink.rect(L["fore-near"], 70, 60, 8, 4, c["gold"])
    paint_hand(ink, L["hand-near"], (84, 59), c["skin"], c["leather"], c["ink"])

    # Ribbon trails behind the waist. Root is wider than the free end.
    ink.capsule(L["ribbon-root"], RIBBON_ROOT, RIBBON_MID, 2, c["ribbon_shade"], c["ribbon"], c["ribbon_light"])
    ink.capsule(L["ribbon-mid"], RIBBON_MID, RIBBON_TIP, 1, c["ribbon_shade"], c["ribbon"], c["ribbon_light"])
    ink.capsule(L["ribbon-tip"], RIBBON_TIP, (6, 89), 1, c["ribbon_shade"], c["ribbon_light"], None)

    paint_head(ink, L["head"], c)


def paint_hand(ink: Ink, layer: int, origin: tuple[int, int], skin: int, leather: int, ink_color: int) -> None:
    ox, oy = origin
    ink.rect(layer, ox - 3, oy - 2, 7, 5, skin)
    ink.rect(layer, ox - 2, oy - 1, 5, 3, leather)
    ink.dot(layer, ox + 3, oy - 2, skin)
    ink.dot(layer, ox + 4, oy - 1, skin)
    ink.dot(layer, ox - 3, oy + 2, ink_color)


def paint_head(ink: Ink, layer: int, c: dict[str, int]) -> None:
    # Local to the neck joint. Nose points right. Hair and beard mark an adult.
    ink.local_rect(layer, HEAD, -8, -16, 8, 12, c["hair"])
    ink.local_rect(layer, HEAD, -2, -15, 11, 13, c["skin"])
    ink.local_rect(layer, HEAD, -2, -14, 4, 11, c["skin_shade"])
    ink.local_rect(layer, HEAD, 5, -12, 4, 7, c["skin_light"])
    ink.local_rect(layer, HEAD, 9, -9, 3, 4, c["skin"])
    ink.local_rect(layer, HEAD, 10, -8, 2, 2, c["skin_light"])
    ink.local_rect(layer, HEAD, 0, -3, 8, 4, c["skin_shade"])
    ink.local_rect(layer, HEAD, 1, -1, 7, 3, c["hair"])
    ink.local_rect(layer, HEAD, -1, -16, 12, 2, c["gold"])
    ink.local_rect(layer, HEAD, 4, -11, 3, 3, c["teeth"])
    ink.local_rect(layer, HEAD, 5, -10, 2, 2, c["eye"])
    ink.dot(layer, HEAD[0] + 6, HEAD[1] - 9, c["teeth"])
    ink.local_rect(layer, HEAD, 0, -2, 5, 4, c["skin"])
    ink.local_rect(layer, HEAD, -6, -12, 3, 3, c["gold_shade"])


def add_parts(cli: Cli, layer: dict[str, int]) -> None:
    parts = [
        ("ribbon-tip", RIBBON_TIP, "ribbon-tip"),
        ("ribbon-mid", RIBBON_MID, "ribbon-mid"),
        ("ribbon-root", RIBBON_ROOT, "ribbon-root"),
        ("thigh-far", THIGH_FAR, "thigh-far"),
        ("shin-far", KNEE_FAR, "shin-far"),
        ("upper-far", UPPER_FAR, "upper-far"),
        ("fore-far", ELBOW_FAR, "fore-far"),
        ("hand-far", SPEAR, "hand-far"),
        ("pelvis", PELVIS, "pelvis"),
        ("torso", TORSO, "torso"),
        ("thigh-near", THIGH_NEAR, "thigh-near"),
        ("shin-near", KNEE_NEAR, "shin-near"),
        ("spear", SPEAR, "spear"),
        ("tassel-root", (96, 54), "tassel-root"),
        ("tassel-tip", (94, 62), "tassel-tip"),
        ("flame", FLAME, "flame"),
        ("upper-near", UPPER_NEAR, "upper-near"),
        ("fore-near", ELBOW_NEAR, "fore-near"),
        ("hand-near", (84, 59), "hand-near"),
        ("head", HEAD, "head"),
    ]
    for name, origin, layer_name in parts:
        cli.run(
            [
                "part",
                "add",
                "--name",
                name,
                "--x",
                str(origin[0]),
                "--y",
                str(origin[1]),
                "--layer",
                str(layer[layer_name]),
            ]
        )
    anchors = [
        ("shin-far", "sole", 6, 14),
        ("shin-near", "sole", -10, 16),
        ("fore-far", "wrist", 12, -10),
        ("fore-near", "wrist", 20, -9),
        ("hand-far", "palm", 0, 0),
        ("hand-near", "palm", 0, 0),
        ("pelvis", "hip-far", -4, 4),
        ("pelvis", "hip-near", 4, 4),
        ("pelvis", "ribbon", -12, 0),
        ("torso", "neck", 4, -28),
        ("torso", "shoulder-far", 6, -22),
        ("torso", "shoulder-near", 10, -24),
        ("head", "neck", 0, 0),
        ("spear", "grip-rear", 0, 0),
        ("spear", "grip-fore", 14, -7),
        ("spear", "tassel", 26, -12),
        ("spear", "tip", 34, -16),
        ("ribbon-root", "end", -10, 3),
        ("ribbon-mid", "end", -10, 4),
        ("ribbon-tip", "end", -8, 4),
        ("tassel-root", "end", -2, 8),
        ("tassel-tip", "end", -1, 7),
        ("flame", "root", 0, 0),
    ]
    for part, name, x, y in anchors:
        cli.run(["part", "anchor", "set", "--part", part, "--name", name, "--x", str(x), "--y", str(y)])


def curve_request(part: str, channel: str, frame: int, value: float, ease: str | None = None) -> dict:
    channels = {"translate-x": "translateX", "translate-y": "translateY", "rotation": "rotation"}
    eases = {"ease-in-out": "easeInOut"}
    params: dict = {
        "part": part,
        "channel": channels.get(channel, channel),
        "frame": frame,
        "value": value,
    }
    if ease:
        params["ease"] = eases.get(ease, ease)
    return {"tool": "setCurveKey", "params": params}


def curve_requests(part: str, channel: str, keys: dict[int, float], ease: str | None = None) -> list[dict]:
    return [curve_request(part, channel, frame, value, ease) for frame, value in keys.items()]


def sparse_body(cli: Cli) -> None:
    ease = "ease-in-out"
    pelvis_x = {frame: values[0] for frame, values in BODY_KEYS.items()}
    pelvis_y = {frame: values[1] for frame, values in BODY_KEYS.items()}
    pelvis_rot = {frame: values[2] for frame, values in BODY_KEYS.items()}
    torso_rot = {frame: values[3] for frame, values in BODY_KEYS.items()}
    spear_x = {frame: values[0] + values[4] for frame, values in BODY_KEYS.items()}
    spear_y = {frame: values[1] + values[5] for frame, values in BODY_KEYS.items()}
    spear_rot = {frame: values[6] for frame, values in BODY_KEYS.items()}
    requests = []
    requests += curve_requests("pelvis", "translate-x", pelvis_x, ease)
    requests += curve_requests("pelvis", "translate-y", pelvis_y, ease)
    requests += curve_requests("pelvis", "rotation", pelvis_rot, ease)
    requests += curve_requests("torso", "translate-x", pelvis_x, ease)
    requests += curve_requests("torso", "translate-y", pelvis_y, ease)
    requests += curve_requests("torso", "rotation", torso_rot, ease)
    requests += curve_requests("spear", "translate-x", spear_x, ease)
    requests += curve_requests("spear", "translate-y", spear_y, ease)
    requests += curve_requests("spear", "rotation", spear_rot, ease)
    cli.batch(requests)


def series(cli: Cli, part: str, channel: str) -> list[float]:
    channels = {"translate-x": "translateX", "translate-y": "translateY", "rotation": "rotation"}
    requests = [
        {"tool": "sampleCurve", "params": {"part": part, "channel": channels.get(channel, channel), "frame": frame}}
        for frame in range(FRAMES)
    ]
    return [float(result["value"]) for result in cli.batch(requests)]


def lag_series(driver: list[float], delay: int, follow: float, gain: float) -> dict[int, float]:
    """Authored delay. Not a physics step. The last frames blend back to the driver."""
    previous = driver[0]
    values = []
    for frame, _value in enumerate(driver):
        source = driver[max(0, frame - delay)] * gain
        previous = follow * previous + (1.0 - follow) * source
        values.append(previous)
    for frame in range(12, FRAMES):
        blend = (frame - 12) / 3.0
        values[frame] = values[frame] * (1.0 - blend) + driver[frame] * blend
    values[0] = 0.0
    return {frame: round(value, 2) for frame, value in enumerate(values)}


def authored_follow(cli: Cli) -> dict[str, dict[int, float]]:
    spear_rot = series(cli, "spear", "rotation")
    torso_rot = series(cli, "torso", "rotation")
    pelvis_x = series(cli, "pelvis", "translate-x")
    ribbon_driver = [-(pelvis_x[frame] * 2.4 + torso_rot[frame] * 0.45) for frame in range(FRAMES)]
    keys = {
        "hand-near": {frame: round(spear_rot[frame], 2) for frame in range(FRAMES)},
        "hand-far": {frame: round(spear_rot[frame], 2) for frame in range(FRAMES)},
        "flame": {frame: round(spear_rot[frame], 2) for frame in range(FRAMES)},
        "head": lag_series(torso_rot, 1, 0.25, 0.35),
        "tassel-root": lag_series(spear_rot, 1, 0.45, 1.0),
        "tassel-tip": lag_series(spear_rot, 3, 0.62, 1.15),
        "ribbon-root": lag_series(ribbon_driver, 1, 0.2, 0.55),
        "ribbon-mid": lag_series(ribbon_driver, 2, 0.4, 1.15),
        "ribbon-tip": lag_series(ribbon_driver, 3, 0.58, 1.9),
    }
    requests = []
    for part, part_keys in keys.items():
        requests += curve_requests(part, "rotation", part_keys)
    cli.batch(requests)
    return keys


def add_attaches(cli: Cli) -> None:
    links = [
        ("head-neck", "head", "neck", "torso", "neck"),
        ("hand-near-grip", "hand-near", "palm", "spear", "grip-fore"),
        ("hand-far-grip", "hand-far", "palm", "spear", "grip-rear"),
        ("flame-tip", "flame", "root", "spear", "tip"),
        ("ribbon-root-hip", "ribbon-root", "end", "pelvis", "ribbon"),
        ("ribbon-mid-root", "ribbon-mid", "end", "ribbon-root", "end"),
        ("ribbon-tip-mid", "ribbon-tip", "end", "ribbon-mid", "end"),
        ("tassel-root-spear", "tassel-root", "end", "spear", "tassel"),
        ("tassel-tip-root", "tassel-tip", "end", "tassel-root", "end"),
    ]
    # Ribbon and tassel attach at their root origin, not at the free end.
    # The tuples above named "end" by mistake for the root joint. Re-state them.
    del links[4:]
    links.extend(
        [
            ("ribbon-root-hip", "ribbon-root", "root", "pelvis", "ribbon"),
            ("ribbon-mid-root", "ribbon-mid", "root", "ribbon-root", "end"),
            ("ribbon-tip-mid", "ribbon-tip", "root", "ribbon-mid", "end"),
            ("tassel-root-spear", "tassel-root", "root", "spear", "tassel"),
            ("tassel-tip-root", "tassel-tip", "root", "tassel-root", "end"),
        ]
    )
    cli.run(["part", "anchor", "set", "--part", "ribbon-root", "--name", "root", "--x", "0", "--y", "0"])
    cli.run(["part", "anchor", "set", "--part", "ribbon-mid", "--name", "root", "--x", "0", "--y", "0"])
    cli.run(["part", "anchor", "set", "--part", "ribbon-tip", "--name", "root", "--x", "0", "--y", "0"])
    cli.run(["part", "anchor", "set", "--part", "tassel-root", "--name", "root", "--x", "0", "--y", "0"])
    cli.run(["part", "anchor", "set", "--part", "tassel-tip", "--name", "root", "--x", "0", "--y", "0"])
    for name, part, anchor, target, target_anchor in links:
        cli.run(
            [
                "constraint",
                "add",
                "--name",
                name,
                "--kind",
                "attach",
                "--part",
                part,
                "--anchor",
                anchor,
                "--target",
                target,
                "--target-anchor",
                target_anchor,
            ]
        )


def solve_many(cli: Cli, frames: list[int]) -> list[dict] | None:
    requests = [{"tool": "solveConstraints", "params": {"frame": frame}} for frame in frames]
    results, error = cli.try_batch(requests)
    if error and "IkUnreachable" in error:
        return None
    if error or results is None:
        raise SystemExit(error or "solve failed")
    return results


def solve(cli: Cli, frame: int) -> dict | None:
    reports = solve_many(cli, [frame])
    if reports is None:
        return None
    return reports[0]


def part_map(report: dict) -> dict[str, dict]:
    return {part["name"]: part for part in report["parts"]}


def anchor_canvas(part: dict, name: str) -> tuple[int, int]:
    for anchor in part["anchors"]:
        if anchor["name"] == name:
            return int(anchor["canvasX"]), int(anchor["canvasY"])
    raise SystemExit(f"missing posed anchor {part['name']}.{name}")


def follow_joints(cli: Cli) -> list[dict]:
    """Move IK roots onto the posed hip and shoulder. Those canvas cells come from solve."""
    reports = solve_many(cli, list(range(FRAMES)))
    if reports is None:
        raise SystemExit("solve failed before IK")
    observations = []
    requests = []
    for frame, report in enumerate(reports):
        parts = part_map(report)
        shoulder_near = anchor_canvas(parts["torso"], "shoulder-near")
        shoulder_far = anchor_canvas(parts["torso"], "shoulder-far")
        hip_near = anchor_canvas(parts["pelvis"], "hip-near")
        hip_far = anchor_canvas(parts["pelvis"], "hip-far")
        observations.append(
            {
                "frame": frame,
                "evaluated": {
                    "shoulderNear": list(shoulder_near),
                    "shoulderFar": list(shoulder_far),
                    "hipNear": list(hip_near),
                    "hipFar": list(hip_far),
                    "neck": list(anchor_canvas(parts["torso"], "neck")),
                    "gripFore": list(anchor_canvas(parts["spear"], "grip-fore")),
                    "gripRear": list(anchor_canvas(parts["spear"], "grip-rear")),
                    "spearTassel": list(anchor_canvas(parts["spear"], "tassel")),
                    "spearLocalGripFore": [
                        next(anchor["x"] for anchor in parts["spear"]["anchors"] if anchor["name"] == "grip-fore"),
                        next(anchor["y"] for anchor in parts["spear"]["anchors"] if anchor["name"] == "grip-fore"),
                    ],
                }
            }
        )
        pairs = [
            ("upper-near", shoulder_near, UPPER_NEAR),
            ("upper-far", shoulder_far, UPPER_FAR),
            ("thigh-near", hip_near, THIGH_NEAR),
            ("thigh-far", hip_far, THIGH_FAR),
        ]
        for name, posed, rest in pairs:
            dx = posed[0] - rest[0]
            dy = posed[1] - rest[1]
            if frame == 0 and (dx != 0 or dy != 0):
                raise SystemExit(f"frame 0 {name} left its rest origin by {dx},{dy}")
            requests.append(curve_request(name, "translate-x", frame, dx))
            requests.append(curve_request(name, "translate-y", frame, dy))
    cli.batch(requests)
    return observations


def add_arm_ik(cli: Cli) -> None:
    cli.run(
        [
            "constraint",
            "add",
            "--name",
            "arm-near",
            "--kind",
            "ik",
            "--part",
            "fore-near",
            "--anchor",
            "wrist",
            "--chain",
            "upper-near",
            "--chain",
            "fore-near",
            "--target",
            "spear",
            "--target-anchor",
            "grip-fore",
        ]
    )
    cli.run(
        [
            "constraint",
            "add",
            "--name",
            "arm-far",
            "--kind",
            "ik",
            "--part",
            "fore-far",
            "--anchor",
            "wrist",
            "--chain",
            "upper-far",
            "--chain",
            "fore-far",
            "--target",
            "spear",
            "--target-anchor",
            "grip-rear",
        ]
    )
    if solve_many(cli, list(range(FRAMES))) is None:
        for frame in range(FRAMES):
            if solve(cli, frame) is None:
                raise SystemExit(f"arm IK cannot reach the spear grip on frame {frame}")
        raise SystemExit("arm IK failed without a per-frame IkUnreachable")


def contact_arg(frame: int, end: int, x: int, y: int) -> str:
    if end == frame:
        return f"{frame}:{x}:{y}"
    return f"{frame}:{end}:{x}:{y}"


def reaches(cli: Cli, name: str, part: str, anchor: str, chain: list[str], contacts: list[tuple[int, int, int, int]], frames: list[int]) -> bool:
    cli.try_run(["constraint", "remove", "--name", name])
    args = [
        "constraint",
        "add",
        "--name",
        name,
        "--kind",
        "ik",
        "--part",
        part,
        "--anchor",
        anchor,
    ]
    for joint in chain:
        args.extend(["--chain", joint])
    for frame, end, x, y in contacts:
        args.extend(["--contact", contact_arg(frame, end, x, y)])
    added, error = cli.try_run(args)
    if added is None:
        return False
    reports = solve_many(cli, frames)
    cli.try_run(["constraint", "remove", "--name", name])
    if reports is None:
        return False
    for report, frame in zip(reports, frames):
        parts = part_map(report)
        sole = anchor_canvas(parts[part], anchor)
        target = None
        for start, end, x, y in contacts:
            if start <= frame <= end:
                target = (x, y)
                break
        if sole != target:
            return False
    return True


def spiral(x: int, y: int, radius: int) -> list[tuple[int, int]]:
    points = [(x, y)]
    for ring in range(1, radius + 1):
        for oy in range(-ring, ring + 1):
            for ox in range(-ring, ring + 1):
                if max(abs(ox), abs(oy)) == ring:
                    points.append((x + ox, y + oy))
    return points


def choose_contacts(cli: Cli) -> dict:
    rest = solve(cli, 0)
    if rest is None:
        raise SystemExit("frame 0 solve failed")
    parts = part_map(rest)
    front_rest = anchor_canvas(parts["shin-near"], "sole")
    rear_rest = anchor_canvas(parts["shin-far"], "sole")
    if front_rest[1] != 116 or rear_rest[1] != 116:
        raise SystemExit(f"rest soles are not on the ground line: {front_rest} {rear_rest}")

    rear_contacts = [(0, FRAMES - 1, rear_rest[0], rear_rest[1])]
    if not reaches(cli, "leg-far", "shin-far", "sole", ["thigh-far", "shin-far"], rear_contacts, list(range(FRAMES))):
        raise SystemExit(f"rear sole {rear_rest} cannot stay planted for every frame at the authored hip travel")

    landing = None
    for x in list(range(front_rest[0] + 18, front_rest[0] + 6, -1)) + list(range(front_rest[0] + 19, front_rest[0] + 28)):
        contacts = [(7, FRAMES - 1, x, front_rest[1])]
        if reaches(cli, "leg-near", "shin-near", "sole", ["thigh-near", "shin-near"], contacts, list(range(7, FRAMES))):
            landing = (x, front_rest[1])
            break
    if landing is None:
        raise SystemExit("no forward ground cell stays reachable for the whole planted recovery")

    early = [(0, 3, front_rest[0], front_rest[1])]
    if not reaches(cli, "leg-near", "shin-near", "sole", ["thigh-near", "shin-near"], early, [0, 1, 2, 3]):
        raise SystemExit("front sole cannot stay planted through the charge")

    swing = []
    aims = {
        4: (front_rest[0] + 5, front_rest[1] - 7),
        5: (front_rest[0] + 11, front_rest[1] - 9),
        6: (landing[0] - 3, front_rest[1] - 5),
    }
    for frame, aim in aims.items():
        found = None
        for x, y in spiral(aim[0], aim[1], 6):
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                continue
            if y > front_rest[1] - 3:
                continue
            if x <= front_rest[0] + 1:
                continue
            contacts = [(frame, frame, x, y)]
            if reaches(cli, "leg-near", "shin-near", "sole", ["thigh-near", "shin-near"], contacts, [frame]):
                found = (x, y)
                break
        if found is None:
            raise SystemExit(f"front foot has no lifted step cell on frame {frame}")
        swing.append((frame, frame, found[0], found[1]))

    front_contacts = early + swing + [(7, FRAMES - 1, landing[0], landing[1])]
    return {
        "frontRest": list(front_rest),
        "rearRest": list(rear_rest),
        "landing": list(landing),
        "front": front_contacts,
        "rear": rear_contacts,
        "classification": {
            "rear": "support for the whole action; one world cell",
            "frontEarly": "support during the charge; one world cell",
            "frontSwing": "single-frame step targets; the solver flag planted is true for any contact span, including these",
            "frontLanding": "support from the hit through the settle; one world cell",
        },
    }


def add_leg_ik(cli: Cli, contacts: dict) -> None:
    def add(name: str, part: str, chain: list[str], items: list[tuple[int, int, int, int]]) -> None:
        args = [
            "constraint",
            "add",
            "--name",
            name,
            "--kind",
            "ik",
            "--part",
            part,
            "--anchor",
            "sole",
            "--chain",
            chain[0],
            "--chain",
            chain[1],
        ]
        for frame, end, x, y in items:
            args.extend(["--contact", contact_arg(frame, end, x, y)])
        cli.run(args)

    add("leg-far", "shin-far", ["thigh-far", "shin-far"], contacts["rear"])
    add("leg-near", "shin-near", ["thigh-near", "shin-near"], contacts["front"])
    if solve_many(cli, list(range(FRAMES))) is None:
        for frame in range(FRAMES):
            if solve(cli, frame) is None:
                raise SystemExit(f"leg IK missed a contact on frame {frame}")
        raise SystemExit("leg IK failed without a per-frame IkUnreachable")


def tag_phases(cli: Cli) -> None:
    cli.run(["tag", "add", "--name", "lunge", "--from", "0", "--to", "15", "--loop", "once"])
    cli.run(["tag", "add", "--name", "charge", "--from", "0", "--to", "3", "--loop", "once"])
    cli.run(["tag", "add", "--name", "stride", "--from", "4", "--to", "6", "--loop", "once"])
    cli.run(["tag", "add", "--name", "thrust", "--from", "7", "--to", "8", "--loop", "once"])
    cli.run(["tag", "add", "--name", "recover", "--from", "9", "--to", "15", "--loop", "once"])


def export_media(cli: Cli, binary: str, final_dir: Path, layer_names: list[str]) -> None:
    final_dir.mkdir(parents=True, exist_ok=True)
    frames = final_dir / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()
    cli.run(["export", "png", "--out-dir", str(frames), "--scale", "1"])
    cli.run(
        [
            "export",
            "sheet",
            "--output",
            str(final_dir / "spear-lunge-sheet.png"),
            "--cols",
            "8",
            "--atlas",
            str(final_dir / "spear-lunge-sheet.atlas.json"),
            "--scale",
            "1",
        ]
    )
    cli.run(
        [
            "export",
            "apng",
            "--output",
            str(final_dir / "spear-lunge.apng"),
            "--tag",
            "lunge",
            "--scale",
            "3",
        ]
    )
    posed = final_dir / "posed-frames"
    if posed.exists():
        shutil.rmtree(posed)
    posed.mkdir()
    cli.run(["export", "png", "--out-dir", str(posed), "--scale", "4"])

    mechanics = final_dir / "mechanics-frames"
    if mechanics.exists():
        shutil.rmtree(mechanics)
    copy_path = final_dir / "mechanics.pxf.json"
    shutil.copy(cli.project, copy_path)
    mech = Cli(binary, copy_path)
    for name in MECHANICS_HIDDEN:
        mech.run(["layer", "hide", "--index", str(layer_names.index(name))])
    mechanics.mkdir()
    mech.run(["export", "png", "--out-dir", str(mechanics), "--scale", "4"])
    mech.run(["export", "apng", "--output", str(final_dir / "spear-lunge-mechanics.apng"), "--tag", "lunge", "--scale", "3"])

    poses = final_dir / "poses"
    poses.mkdir(exist_ok=True)
    pairs = final_dir / "pairs"
    pairs.mkdir(exist_ok=True)
    for frame, name in KEY_POSES:
        full = posed / f"pixelforge-{frame:03d}.png"
        bare = mechanics / f"pixelforge-{frame:03d}.png"
        pose = poses / f"pose-{frame:02d}-{name}.png"
        compare = poses / f"pose-{frame:02d}-{name}-compare.png"
        shutil.copy(full, pose)
        run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(bare),
                "-i",
                str(full),
                "-filter_complex",
                "[0][1]hstack=inputs=2",
                str(compare),
            ]
        )
        pair = pairs / f"pair-{frame:02d}.png"
        shutil.copy(compare, pair)
    # Full timeline, mechanics on the left and costume on the right, nearest-neighbor pixels already scaled.
    pair_dir = final_dir / "pair-frames"
    if pair_dir.exists():
        shutil.rmtree(pair_dir)
    pair_dir.mkdir()
    for frame in range(FRAMES):
        run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(mechanics / f"pixelforge-{frame:03d}.png"),
                "-i",
                str(posed / f"pixelforge-{frame:03d}.png"),
                "-filter_complex",
                "[0][1]hstack=inputs=2",
                str(pair_dir / f"pair-{frame:02d}.png"),
            ]
        )
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            "12",
            "-i",
            str(pair_dir / "pair-%02d.png"),
            "-frames:v",
            "48",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(final_dir / "spear-lunge-review.mp4"),
        ]
    )


def run_ffmpeg(args: list[str]) -> None:
    # Repeat the 16-frame cycle three times only for the review movie.
    if args[0] == "ffmpeg" and "-frames:v" in args:
        args = [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "2",
            "-framerate",
            "12",
            "-i",
            args[args.index("-i") + 1],
            "-frames:v",
            "48",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            args[-1],
        ]
    proc = subprocess.run(args, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg failed\n{proc.stderr[-2000:]}")


def compact_project(path: Path) -> None:
    """Drop insignificant whitespace. Values stay the kernel's. The CLI writes pretty JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bake the spear lunge demo with pixelforge")
    parser.add_argument("--pixelforge", default=os.environ.get("PIXELFORGE", ""))
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    if not args.pixelforge:
        raise SystemExit("pass --pixelforge or set PIXELFORGE")
    binary = args.pixelforge
    version = require_engine(binary)
    script_root = Path(__file__).resolve().parent
    root = Path(args.out) if args.out else script_root
    brief = load_brief(script_root / "brief.json")
    source = root / "source"
    final = root / "final"
    reports = root / "reports"
    work = root / "work"
    for path in (source, final, reports, work):
        path.mkdir(parents=True, exist_ok=True)
    project = work / "lunge.pxf.json"
    if project.exists():
        project.unlink()
    cli = Cli(binary, project)
    print("palette, layers, rest pose", flush=True)
    cli.run(["new", "--width", str(WIDTH), "--height", str(HEIGHT), "--output", str(project)])
    colors = setup_palette(cli, brief)
    layers = setup_layers(cli)
    ink = Ink()
    paint(ink, layers, colors)
    cli.batch(ink.requests())
    add_parts(cli, layers)
    shutil.copy(project, source / "rest.pxf.json")
    compact_project(source / "rest.pxf.json")

    print("frames and curves", flush=True)
    cli.batch([{"tool": "duplicateFrame", "params": {"index": 0}} for _ in range(FRAMES - 1)])
    sparse_body(cli)
    follow_keys = authored_follow(cli)
    add_attaches(cli)
    print("joint follow from evaluated anchors", flush=True)
    joint_observations = follow_joints(cli)
    print("arm IK", flush=True)
    add_arm_ik(cli)
    print("foot contacts", flush=True)
    contacts = choose_contacts(cli)
    add_leg_ik(cli, contacts)
    tag_phases(cli)

    print("bake", flush=True)
    baked = cli.run(["bake", "--from", "0", "--to", str(FRAMES - 1), "--fps", str(FPS)])
    if baked.get("wrote") is not True or baked.get("delayMs") != 83:
        raise SystemExit(f"unexpected bake: delay={baked.get('delayMs')} wrote={baked.get('wrote')}")
    shutil.copy(project, final / "spear-lunge.pxf.json")
    compact_project(final / "spear-lunge.pxf.json")

    motion = {
        "engineSha": ENGINE_SHA,
        "versionString": version,
        "bodyKeys": {str(frame): values for frame, values in BODY_KEYS.items()},
        "followCurves": {part: {str(frame): value for frame, value in keys.items()} for part, keys in follow_keys.items()},
        "contacts": contacts,
        "jointObservationsBeforeIk": joint_observations,
        "note": "followCurves are authored lag keys. jointObservationsBeforeIk are constraint-solve canvas cells, not rest anchors.",
    }
    (source / "motion.json").write_text(json.dumps(motion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (reports / "bake.json").write_text(json.dumps(baked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("export", flush=True)
    export_media(cli, binary, final, LAYERS)
    sheet = final / "spear-lunge-sheet.png"
    stamp = {
        "engineSha": ENGINE_SHA,
        "versionString": version,
        "delayMs": baked["delayMs"],
        "sheetSha256": sha256(sheet),
        "projectSha256": sha256(final / "spear-lunge.pxf.json"),
        "dropped": baked.get("dropped"),
        "sealed": baked.get("sealed"),
        "breaks": baked.get("breaks"),
        "conflicts": baked.get("conflicts"),
    }
    (reports / "stamp.json").write_text(json.dumps(stamp, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stamp, indent=2))


if __name__ == "__main__":
    main()
