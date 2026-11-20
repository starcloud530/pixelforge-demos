#!/usr/bin/env python3
"""Rebuild the Aster Wind Observatory using PixelForge kernel drawing requests."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile

SLUG = "aster-wind-observatory"
SIZE = 96
VERSION = "pixelforge 0.1.0-rc.6"

PALETTE = {
    "ink": "161b29",
    "stoneDeep": "283043",
    "stoneShadow": "3b445a",
    "stone": "58637a",
    "stoneLight": "7c8a95",
    "ironDark": "293237",
    "iron": "414c52",
    "ironLight": "677976",
    "copperDark": "533235",
    "copperShadow": "794839",
    "copper": "a16043",
    "copperLight": "d48e55",
    "brassDark": "8d6348",
    "brass": "b88b55",
    "gold": "dfb46c",
    "sun": "ffdfa0",
    "glassDeep": "193b40",
    "glassDark": "205759",
    "glass": "338483",
    "glassLight": "55b2a1",
    "mint": "91e1be",
    "spark": "d2f7d9",
    "reddark": "8a4546",
    "red": "c36c50",
}
COLORS = {name: index for index, name in enumerate(PALETTE, 1)}


class Drawing:
    def __init__(self, layer):
        self.layer = layer
        self.requests = []

    def add(self, tool, color=None, **params):
        params["layer"] = self.layer
        if color is not None:
            params["colorIndex"] = COLORS[color]
        self.requests.append({"tool": tool, "params": params})

    def rect(self, color, x, y, w, h=1):
        self.add("fillRect", color, x=x, y=y, width=w, height=h)

    def erase(self, x, y, w, h):
        self.add("eraseRect", x=x, y=y, width=w, height=h)

    def poly(self, color, *vertices):
        self.add("polygon", color, points=[{"x": x, "y": y} for x, y in vertices], fill=True)

    def oval(self, color, x, y, w, h, fill=True):
        self.add("ellipse", color, x=x, y=y, width=w, height=h, fill=fill)

    def line(self, color, x0, y0, x1, y1):
        self.add("line", color, x0=x0, y0=y0, x1=x1, y1=y1, pixelPerfect=True)

    def point(self, color, *points):
        for x, y in points:
            self.add("paint", color, x=x, y=y)


def silhouette():
    d = Drawing(1)
    d.poly("ink", (10, 75), (27, 65), (72, 65), (87, 74), (87, 82),
           (69, 91), (24, 91), (10, 83))
    d.poly("ink", (20, 42), (28, 34), (54, 34), (64, 41), (64, 73),
           (57, 80), (26, 80), (20, 74))
    d.poly("ink", (60, 48), (66, 43), (78, 45), (82, 52), (82, 70),
           (75, 75), (64, 74), (60, 69))
    d.poly("ink", (30, 34), (34, 29), (39, 29), (39, 14), (42, 11),
           (48, 11), (51, 14), (51, 29), (56, 29), (60, 33), (60, 40), (30, 40))
    return d.requests


def plinth():
    d = Drawing(0)
    d.poly("stoneDeep", (7, 78), (25, 67), (73, 67), (90, 76),
           (90, 84), (70, 94), (23, 94), (7, 85))
    d.poly("stoneShadow", (11, 74), (27, 65), (71, 65), (86, 74), (86, 83),
           (68, 92), (24, 92), (11, 84))
    d.poly("stone", (11, 74), (27, 65), (72, 65), (86, 74),
           (68, 83), (25, 83))
    d.poly("stoneLight", (14, 74), (28, 66), (70, 66), (82, 73),
           (67, 80), (25, 80))
    d.poly("stoneShadow", (23, 75), (32, 70), (71, 70), (79, 74),
           (68, 79), (27, 79))
    d.poly("stoneDeep", (68, 83), (86, 74), (86, 82), (68, 91))
    d.line("stoneLight", 15, 77, 25, 82)
    d.rect("stoneLight", 25, 82, 27)
    d.line("stone", 69, 83, 84, 75)
    d.line("stoneDeep", 29, 85, 29, 90)
    d.line("stoneDeep", 50, 84, 50, 89)
    d.line("stoneShadow", 75, 81, 75, 87)
    d.line("stoneDeep", 17, 81, 22, 83)
    d.line("stone", 32, 90, 45, 90)
    d.line("stoneDeep", 55, 85, 64, 85)
    d.point("stoneLight", (55, 88), (56, 88), (63, 86))
    return d.requests


def housing():
    d = Drawing(1)
    # Far right feet and the dark chassis beneath the chamfered bronze face.
    d.poly("ink", (19, 43), (28, 34), (56, 34), (67, 43), (67, 71),
           (62, 78), (29, 82), (19, 75))
    d.poly("ironDark", (54, 41), (64, 43), (65, 69), (59, 76), (52, 75))
    d.poly("copperShadow", (54, 38), (57, 36), (65, 42), (65, 65),
           (58, 68), (54, 65))
    d.poly("copperDark", (57, 62), (65, 58), (65, 71), (59, 77), (57, 76))
    d.line("copperLight", 57, 37, 64, 43)
    d.line("copper", 63, 45, 63, 62)
    d.poly("copperDark", (22, 43), (28, 36), (53, 36), (59, 43),
           (59, 71), (54, 78), (29, 81), (22, 75))
    d.poly("copper", (22, 43), (29, 36), (54, 36), (57, 43),
           (57, 69), (52, 76), (29, 78), (23, 73))
    d.poly("copperLight", (22, 43), (29, 36), (53, 36), (55, 40),
           (30, 40), (25, 45), (25, 68), (22, 71))
    d.poly("copperShadow", (25, 65), (32, 70), (49, 70), (57, 64),
           (57, 70), (52, 76), (29, 78), (25, 74))
    d.line("copperDark", 23, 72, 28, 76)
    d.line("gold", 28, 38, 46, 38)
    d.line("brass", 25, 44, 25, 64)
    d.line("copperDark", 52, 75, 56, 70)
    d.line("copperShadow", 25, 62, 25, 66)
    d.line("copperLight", 26, 65, 26, 67)
    d.point("gold", (54, 45), (55, 46))
    d.point("copperLight", (27, 64), (28, 65), (53, 72))
    # Cast footing, stepped panel, and brass neck.
    d.poly("ink", (25, 73), (30, 73), (32, 77), (55, 74), (58, 76),
           (55, 82), (48, 84), (27, 85), (21, 81), (21, 77))
    d.poly("iron", (25, 75), (29, 75), (32, 79), (53, 76), (55, 77),
           (53, 80), (47, 82), (28, 83), (23, 80), (23, 78))
    d.line("ironLight", 28, 80, 45, 79)
    d.line("stoneDeep", 29, 82, 47, 81)
    d.poly("ink", (29, 32), (35, 27), (39, 27), (39, 18), (41, 15),
           (49, 15), (52, 18), (52, 27), (56, 28), (61, 33), (59, 38), (29, 38))
    d.poly("brassDark", (31, 32), (36, 28), (55, 29), (59, 33), (57, 36), (31, 36))
    d.poly("gold", (32, 32), (37, 29), (53, 29), (57, 32), (52, 34), (33, 34))
    d.line("sun", 37, 29, 49, 29)
    d.rect("copperDark", 40, 19, 11, 12)
    d.rect("brass", 41, 18, 7, 12)
    d.rect("gold", 42, 18, 3, 10)
    d.rect("sun", 42, 18, 1, 7)
    d.rect("copper", 48, 20, 2, 10)
    d.rect("ink", 39, 25, 13, 2)
    d.rect("brass", 40, 25, 12)
    d.rect("gold", 41, 25, 7)
    # U-shaped copper feed carrying condensate to the glass tube.
    pipe = [(54, 39), (60, 38), (65, 38), (70, 42), (70, 50)]
    for color, offset in [("ink", 2), ("copperDark", 1), ("copper", 0)]:
        offsets = range(-offset, offset + 1)
        for shift in offsets:
            for (ax, ay), (bx, by) in zip(pipe, pipe[1:]):
                d.line(color, ax + shift, ay + abs(shift), bx + shift, by + abs(shift))
    d.line("copperLight", 58, 38, 65, 38)
    d.line("copperLight", 65, 38, 69, 41)
    d.line("brassDark", 66, 40, 68, 38)
    d.line("copperLight", 69, 43, 69, 46)
    d.poly("ink", (56, 67), (64, 68), (66, 72), (71, 72), (75, 69),
           (79, 69), (79, 76), (73, 80), (64, 80), (60, 77), (56, 75))
    d.poly("copperShadow", (57, 69), (63, 70), (66, 74), (72, 74),
           (77, 70), (78, 75), (73, 79), (65, 79), (61, 75), (57, 73))
    d.line("copperLight", 61, 72, 65, 76)
    d.line("copper", 65, 76, 73, 76)
    d.line("gold", 66, 75, 70, 75)
    return d.requests


def instruments():
    d = Drawing(2)
    # The inset front dial uses shaded concentric bezels and clustered reflections.
    d.oval("ink", 25, 41, 32, 31)
    d.oval("copperDark", 26, 41, 29, 28)
    d.oval("gold", 26, 41, 28, 27)
    d.oval("brassDark", 28, 43, 26, 25)
    d.oval("ink", 29, 44, 23, 22)
    d.oval("glassDark", 30, 45, 21, 20)
    d.oval("glassDeep", 33, 47, 18, 17)
    d.poly("glass", (32, 49), (35, 46), (41, 46), (36, 49),
           (34, 54), (34, 59), (31, 55), (31, 52))
    d.line("glassLight", 34, 49, 37, 47)
    d.point("mint", (34, 50), (35, 49))
    d.line("glassDark", 43, 62, 48, 60)
    d.point("sun", (34, 42), (35, 42), (39, 41), (40, 41), (41, 41))
    d.point("brass", (44, 66), (46, 65), (52, 57))
    d.line("glassLight", 40, 47, 40, 49)
    d.line("glass", 46, 50, 47, 49)
    d.line("glass", 46, 58, 48, 59)
    d.line("glassLight", 40, 60, 40, 62)
    d.point("glass", (35, 58))
    # Tube goes on its own layer with the dial and fixed trim.
    d.poly("ink", (65, 45), (69, 42), (77, 43), (81, 47), (81, 69),
           (78, 74), (70, 74), (65, 69))
    d.rect("glassDark", 67, 49, 13, 19)
    d.rect("glassDeep", 76, 49, 3, 20)
    d.rect("glass", 68, 50, 2, 17)
    d.rect("glassLight", 68, 51, 1, 7)
    d.rect("glass", 74, 53, 2, 2)
    d.rect("glass", 74, 58, 2, 2)
    d.rect("glass", 74, 63, 2, 2)
    for top in (43, 66):
        d.poly("brassDark", (66, top + 3), (70, top), (77, top + 1),
               (80, top + 4), (79, top + 7), (68, top + 6))
        d.poly("brass", (66, top + 3), (70, top), (77, top + 1), (79, top + 4), (69, top + 4))
        d.line("gold", 67, top + 3, 70, top + 1)
        d.rect("sun", 70, top + 1, 4)
        d.rect("copperShadow", 74, top + 5, 6)
    # Side louvers and inset brass service tag.
    for x, y in [(62, 47), (62, 52), (62, 57)]:
        d.line("copperDark", x, y, x + 3, y - 2)
        d.line("copperLight", x, y + 1, x + 3, y - 1)
    d.poly("ink", (32, 69), (48, 68), (50, 70), (48, 74), (33, 75), (31, 73))
    d.poly("brassDark", (33, 70), (48, 69), (48, 72), (34, 74), (32, 72))
    d.line("gold", 34, 70, 44, 69)
    d.line("sun", 34, 70, 37, 70)
    d.point("copperDark", (34, 72), (47, 71))
    d.line("gold", 40, 70, 40, 73)
    d.line("gold", 38, 71, 42, 71)
    d.point("sun", (40, 71))
    d.point("ink", (27, 45), (55, 43), (27, 69), (54, 68))
    d.point("gold", (27, 44), (55, 42), (27, 68), (54, 67))
    d.point("sun", (31, 32), (54, 33))
    return d.requests


def rotor(angle):
    d = Drawing(3)
    d.erase(23, 4, 45, 21)
    cx, cy = 45, 14
    endpoints = [(round(cx + 16 * math.cos(angle + i * math.tau / 3)),
                  round(cy + 6 * math.sin(angle + i * math.tau / 3))) for i in range(3)]
    for x, y in sorted(endpoints, key=lambda p: p[1]):
        d.line("ink", cx, cy - 1, x, y - 1)
        d.line("ink", cx, cy + 1, x, y + 1)
        d.line("brassDark", cx, cy, x, y)
        if y >= cy:
            d.line("gold", cx, cy, x, y)
        d.oval("ink", x - 4, y - 3, 9, 7)
        d.oval("copperShadow", x - 3, y - 2, 7, 5)
        d.oval("gold", x - 3, y - 2, 7, 4)
        d.rect("sun", x - 2, y - 2, 4)
        d.rect("copperDark", x - 2, y - 1, 4)
        d.rect("brassDark", x - 1, y, 4)
        d.rect("copper", x, y + 1, 3)
    d.poly("ink", (40, 11), (43, 8), (47, 8), (50, 11), (50, 16),
           (47, 19), (43, 19), (40, 16))
    d.oval("brassDark", 41, 10, 9, 8)
    d.oval("gold", 41, 9, 8, 7)
    d.oval("sun", 42, 9, 6, 4)
    d.point("brass", (43, 15), (47, 15))
    return d.requests


def signal(angle, strength, bubble_height=None):
    d = Drawing(4)
    d.erase(29, 44, 22, 22)
    d.erase(68, 50, 11, 16)
    d.erase(56, 62, 2, 5)
    cx, cy = 40, 55
    x, y = round(cx + 7 * math.cos(angle)), round(cy + 7 * math.sin(angle))
    needle = ("copperLight", "gold", "mint", "spark")[strength]
    d.line(needle, cx, cy, x, y)
    d.rect("ink", cx - 1, cy - 1, 3, 3)
    d.point("sun", (cx, cy))
    if strength:
        indexes = [(45, 48), (47, 52), (47, 56), (44, 61)]
        d.point("glassLight", *indexes[:strength + 1])
    if strength >= 2:
        d.line("glassLight", 44, 48, 47, 51)
        d.line("glass", 48, 52, 48, 56)
        if strength == 3:
            d.line("mint", 48, 53, 48, 55)
        d.point("mint", (31, 52), (32, 51))
        d.line("glassLight", 35, 61, 38, 63)
        d.rect("glass", 70, 63, 5, 3)
        d.rect("glassLight", 70, 63, 5)
        d.rect("mint", 70, 63, 2)
        if bubble_height is not None:
            d.point("mint", (73, bubble_height), (71, bubble_height + 2))
            d.point("glassLight", (74, bubble_height + 1))
    d.rect("glassDeep", 56, 63, 2, 3)
    d.point(("reddark", "red", "glassLight", "mint")[strength], (56, 64))
    return d.requests


def tool(command, **params):
    return {"tool": command, "params": params}


def check_binary(binary):
    actual = subprocess.check_output([binary, "--version"], text=True).strip()
    if actual != VERSION:
        raise SystemExit(f"Expected {VERSION}. Found {actual}.")


def build(binary, output, stages):
    project = output / f"{SLUG}.pxf.json"
    sheet = output / f"{SLUG}-sheet.png"
    atlas = output / f"{SLUG}.atlas.json"
    operation_counts = {}

    def run(*args):
        result = subprocess.run([binary, *map(str, args)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"{' '.join(map(str, args))}\n{result.stdout}\n{result.stderr}")
        return result

    def call(stage, requests):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / "requests.json"
            batch.write_text(json.dumps(requests), encoding="utf-8")
            run("call", "--project", project, "--request-file", batch)
        operation_counts[stage] = len(requests)

    run("new", "--width", SIZE, "--height", SIZE, "--output", project)
    palette = "GIMP Palette\n" + "\n".join(
        " ".join(str(value) for value in bytes.fromhex(color)) + f" {name}"
        for name, color in PALETTE.items()
    )
    call("prepare", [
        tool("importPalette", text=palette, mode="replace"),
        tool("renameLayer", name="Stone plinth"),
        tool("addLayer", name="Bronze chassis"),
        tool("addLayer", name="Instruments"),
        tool("addLayer", name="Cup rotor"),
        tool("addLayer", name="Signal and gauge"),
    ])
    if stages:
        call("silhouette", silhouette())
        run("preview", "--project", project, "--scale", 4, "--output", output / "stage-01-silhouette.png")
        clear = Drawing(1)
        clear.erase(0, 0, SIZE, SIZE)
        call("clear-silhouette", clear.requests)
    call("chassis", plinth() + housing())
    if stages:
        run("preview", "--project", project, "--scale", 4, "--output", output / "stage-02-chassis.png")
    call("details", instruments() + rotor(-0.22) + signal(math.pi * .82, 0))
    if stages:
        run("preview", "--project", project, "--scale", 4, "--output", output / "stage-03-details.png")

    # Dormant pose, then three accelerating detents, then an eight-frame orbit.
    poses = [
        (-0.22, math.pi * .82, 0, None, 320),
        (-0.10, math.pi * .63, 1, None, 145),
        (0.14, math.pi * .35, 2, 62, 115),
        (0.50, -math.pi * .12, 3, 60, 95),
    ]
    orbit_start = 1.02
    for i, bubble in enumerate((58, 56, 54, 52, 62, 60, 59, 57)):
        phase = i * math.tau / 8
        poses.append((orbit_start + phase, -1.18 + 0.36 * math.sin(phase), 3, bubble, 92))

    animation = [tool("setFrameDelay", index=0, delayMs=poses[0][4])]
    for index, (angle, needle, power, bubble, delay) in enumerate(poses[1:], 1):
        animation.extend([
            tool("duplicateFrame", index=index - 1),
            tool("setActiveFrame", index=index),
            tool("setFrameDelay", index=index, delayMs=delay),
            *rotor(angle),
            *signal(needle, power, bubble),
        ])
    animation.extend([
        tool("addTag", name="dormant", **{"from": 0, "to": 0}, loop="once"),
        tool("addTag", name="power_on", **{"from": 0, "to": 4}, loop="once"),
        tool("addTag", name="sampling", **{"from": 4, "to": 11}, loop="forward"),
        tool("setActiveFrame", index=4),
    ])
    call("animate", animation)
    run("export", "sheet", "--project", project, "--output", sheet, "--atlas", atlas, "--cols", 4)
    animations = {}
    for tag in ("power_on", "sampling"):
        animation_path = output / f"{SLUG}-{tag.replace('_', '-')}.png"
        result = json.loads(run("export", "apng", "--project", project, "--tag", tag,
                                "--scale", 4, "--output", animation_path).stdout)["result"]
        animations[tag] = {
            "frameCount": len(result["frames"]),
            "plays": result["plays"],
            "sha256": hashlib.sha256(animation_path.read_bytes()).hexdigest(),
        }
    run("preview", "--project", project, "--frame", 4, "--scale", 5, "--output", output / f"{SLUG}-poster.png")
    run("preview", "--project", project, "--frame", 4, "--scale", 1, "--output", output / f"{SLUG}-native.png")
    validation = json.loads(run("validate-atlas", "--atlas", atlas, "--sheet", sheet, "--strict",
                                "--require-tag", "dormant", "--require-tag", "power_on",
                                "--require-tag", "sampling").stdout)
    scene = json.loads(run("scene", "--project", project).stdout)["result"]
    # Read the source to compare fixed cels. The file is written exclusively by the CLI.
    document = json.loads(project.read_text())
    reference = document["frames"][0]
    # A build with an unexpected project shape should fail before reporting success.
    stable_structure = all(frame["layers"][:3] == reference["layers"][:3] for frame in document["frames"])
    orbit = document["frames"][4:]
    unique_sampling_poses = len({json.dumps(frame["layers"][3]) for frame in orbit})
    if (not validation.get("ok") or validation["result"]["warningCount"]
            or not stable_structure or unique_sampling_poses != 8):
        raise RuntimeError("Atlas, fixed-layer, or orbit validation failed")
    report = {
        "version": VERSION,
        "binarySha256": hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
        "validation": validation["result"],
        "fixedLayersUnchanged": stable_structure,
        "uniqueSamplingRotorPoses": unique_sampling_poses,
        "animations": animations,
        "frameCount": scene["frameCount"],
        "layers": [layer["name"] for layer in scene["layers"]],
        "delaysMs": [frame["delayMs"] for frame in scene["frames"]],
        "tags": scene["tags"],
        "toolRequestsByStage": operation_counts,
        "sheetSha256": hashlib.sha256(sheet.read_bytes()).hexdigest(),
        "aestheticApproval": False,
    }
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixelforge", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--stages", action="store_true", help="also export three work-in-progress tiles")
    args = parser.parse_args()
    binary = args.pixelforge.resolve()
    check_binary(binary)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    build(binary, output, args.stages)


if __name__ == "__main__":
    main()
