#!/usr/bin/env python3
"""Replay the Alpine Post Courier artwork through the PixelForge v0.1.0-rc.6 CLI."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


PALETTE = {
    "ink": "222437",
    "slate": "3D4059",
    "deep_teal": "234850",
    "teal": "32666B",
    "foam": "65A19A",
    "wine": "552E46",
    "berry": "8C425D",
    "rose": "BB6280",
    "blush": "E89599",
    "rust": "8E493A",
    "ochre": "C6753E",
    "honey": "ECAE5F",
    "sun": "F9CF82",
    "snow": "FFE4B0",
    "shadow_skin": "A96858",
    "skin": "DC9977",
    "moss": "465950",
    "sage": "77846B",
    "leaf": "A7AD85",
    "ice": "D7DFC4",
}
INDEX = {name: index for index, name in enumerate(PALETTE, start=1)}
LEGS, BODY, GEAR, ARMS, SCARF_TAIL = range(5)
FACINGS = ("down", "left", "right", "up")
DELAYS = (400, 155, 105, 155, 105)


class Drawing:
    def __init__(self, layer, *, mirror=False, dx=0, dy=0):
        self.layer = layer
        self.mirror = mirror
        self.dx = dx
        self.dy = dy
        self.ops = []

    def point(self, x, y):
        return {"x": (63 - x if self.mirror else x) + self.dx, "y": y + self.dy}

    def path(self, color, *points):
        self.ops.append(request(
            "polygon", points=[self.point(x, y) for x, y in points],
            colorIndex=INDEX[color], layer=self.layer, fill=True,
        ))

    def box(self, color, x, y, width, height):
        left = x + width - 1 if self.mirror else x
        self.ops.append(request(
            "fillRect", **self.point(left, y), width=width,
            height=height, colorIndex=INDEX[color], layer=self.layer,
        ))

    def line(self, color, start, end):
        a = self.point(*start)
        b = self.point(*end)
        self.ops.append(request(
            "line", x0=a["x"], y0=a["y"], x1=b["x"], y1=b["y"],
            colorIndex=INDEX[color], layer=self.layer, pixelPerfect=True,
        ))


def request(tool, **params):
    return {"tool": tool, **({"params": params} if params else {})}


def front_body(stage):
    """Cap, face, and puffer jacket. Light falls from the screen's upper left."""
    d = Drawing(BODY)
    d.path("ink", (24, 30), (29, 27), (35, 27), (41, 30), (43, 36), (41, 45),
           (39, 47), (24, 47), (22, 44), (22, 35))
    d.path("ink", (22, 17), (24, 12), (28, 10), (35, 10), (39, 12), (42, 16),
           (43, 23), (41, 27), (38, 29), (26, 29), (22, 26), (20, 22))
    d.path("ink", (29, 9), (29, 7), (32, 5), (35, 5), (37, 7), (36, 10), (33, 11))
    if stage == 1:
        return d.ops
    d.path("rust", (25, 31), (30, 29), (35, 29), (40, 31), (41, 36),
           (39, 44), (38, 46), (25, 46), (23, 43), (24, 34))
    d.path("ochre", (26, 31), (32, 30), (39, 32), (40, 37), (37, 44), (25, 44), (24, 40))
    d.path("honey", (27, 31), (33, 30), (38, 32), (38, 36), (34, 39),
           (25, 39), (25, 34))
    d.path("shadow_skin", (23, 19), (40, 18), (41, 22), (39, 26), (36, 28),
           (28, 28), (24, 26), (22, 23))
    d.path("skin", (25, 18), (39, 18), (40, 21), (38, 25), (35, 27), (28, 27), (24, 24))
    d.path("wine", (23, 17), (25, 13), (29, 11), (35, 11), (39, 13), (41, 17),
           (41, 21), (37, 20), (24, 20), (22, 21))
    d.path("berry", (24, 16), (27, 13), (30, 12), (35, 12), (38, 14), (39, 17),
           (34, 19), (24, 19))
    d.path("rose", (25, 16), (27, 14), (31, 12), (34, 12), (37, 14), (33, 14), (30, 16))
    d.path("rose", (30, 8), (32, 6), (35, 6), (36, 8), (34, 10), (31, 9))
    if stage == 2:
        return d.ops
    # Folded knit brim, little embroidered patch, and a stable pair of eyes.
    d.path("rose", (23, 18), (26, 17), (35, 17), (40, 18), (39, 19), (24, 19))
    d.box("blush", 26, 17, 6, 1)
    d.box("wine", 25, 20, 2, 2)
    d.box("wine", 38, 20, 2, 2)
    d.box("snow", 28, 17, 3, 2)
    d.box("ink", 27, 22, 2, 2)
    d.box("ink", 35, 22, 2, 2)
    d.box("snow", 27, 22, 1, 1)
    d.box("snow", 35, 22, 1, 1)
    d.box("shadow_skin", 26, 24, 2, 1)
    d.box("shadow_skin", 36, 24, 2, 1)
    d.box("snow", 31, 24, 2, 1)
    d.box("shadow_skin", 31, 26, 3, 1)
    d.line("sun", (26, 35), (31, 35))
    d.line("rust", (25, 38), (36, 38))
    d.line("rust", (25, 43), (38, 43))
    d.box("deep_teal", 32, 33, 2, 11)
    d.box("snow", 32, 34, 2, 2)
    d.box("snow", 25, 41, 4, 1)
    return d.ops


def profile_body(mirror):
    d = Drawing(BODY, mirror=mirror)
    d.path("ink", (23, 33), (28, 27), (37, 28), (41, 32), (43, 42), (40, 46),
           (36, 47), (24, 46), (21, 41))
    d.path("rust", (24, 34), (29, 29), (36, 29), (40, 33), (41, 41), (38, 45),
           (25, 45), (23, 41))
    d.path("ochre", (26, 33), (29, 30), (36, 30), (39, 34), (39, 39),
           (35, 43), (24, 43), (23, 39))
    d.path("honey", (26, 33), (29, 30), (34, 30), (37, 34), (36, 38), (24, 38))
    d.line("rust", (24, 39), (37, 39))
    d.line("sun", (26, 34), (31, 34))
    d.path("ink", (20, 23), (22, 21), (22, 17), (25, 12), (30, 10), (36, 10),
           (40, 13), (42, 19), (41, 25), (38, 28), (31, 29), (24, 27), (22, 25), (20, 25))
    d.path("ink", (30, 9), (31, 7), (34, 5), (37, 6), (38, 8), (36, 11), (32, 11))
    d.path("shadow_skin", (21, 23), (23, 22), (24, 18), (40, 18), (40, 24),
           (37, 27), (30, 28), (24, 26), (22, 24), (21, 24))
    d.path("skin", (22, 23), (24, 22), (25, 19), (34, 19), (35, 23),
           (33, 26), (28, 27), (24, 25), (23, 24))
    d.path("wine", (23, 17), (26, 13), (31, 11), (36, 11), (39, 14),
           (41, 18), (40, 23), (37, 25), (37, 20), (23, 20))
    d.path("berry", (24, 17), (27, 14), (31, 12), (36, 12), (39, 15),
           (40, 18), (37, 20), (25, 19))
    # Profile pose mirrors. The light clusters are reauthored on screen-left.
    if mirror:
        d.path("rose", (31, 13), (35, 12), (38, 14), (39, 16), (36, 15), (32, 15))
        d.line("blush", (37, 16), (39, 17))
        d.line("sun", (34, 33), (37, 34))
    else:
        d.path("rose", (25, 17), (28, 14), (32, 12), (35, 12), (32, 14), (30, 16))
        d.line("blush", (27, 16), (30, 15))
    d.path("rose", (24, 18), (28, 17), (37, 17), (40, 18), (38, 20), (24, 20))
    d.path("rose", (31, 8), (34, 6), (37, 7), (37, 8), (35, 10), (32, 10))
    d.box("snow", 27, 18, 3, 1)
    d.box("ink", 26, 22, 2, 2)
    d.box("snow", 26 + int(mirror), 22, 1, 1)
    d.box("snow", 23, 23, 1, 1)
    d.box("shadow_skin", 25, 25, 3, 1)
    d.path("skin", (35, 21), (37, 21), (38, 23), (36, 25), (34, 24))
    d.box("shadow_skin", 35, 22, 1, 2)
    return d.ops


def back_body():
    d = Drawing(BODY)
    d.path("ink", (23, 31), (28, 27), (35, 27), (41, 30), (43, 37), (41, 44),
           (38, 47), (25, 47), (22, 44), (21, 37))
    d.path("rust", (24, 32), (28, 29), (35, 29), (40, 32), (41, 38), (40, 43),
           (37, 46), (25, 46), (23, 43), (23, 36))
    d.path("honey", (25, 32), (29, 29), (34, 29), (39, 32), (39, 36),
           (35, 39), (24, 39), (24, 35))
    d.path("ochre", (24, 38), (36, 37), (39, 40), (37, 44), (25, 44))
    d.path("ink", (21, 21), (22, 16), (26, 12), (29, 10), (36, 10),
           (40, 13), (42, 16), (43, 23), (40, 27), (37, 29), (26, 29), (22, 26))
    d.path("ink", (29, 9), (29, 7), (32, 5), (35, 5), (37, 7), (36, 10), (33, 11))
    d.path("wine", (22, 21), (24, 16), (27, 13), (30, 11), (36, 11),
           (40, 15), (41, 20), (40, 24), (36, 28), (27, 28), (24, 26))
    d.path("berry", (24, 19), (26, 15), (30, 12), (35, 12), (38, 15),
           (39, 19), (36, 24), (28, 25), (25, 23))
    d.path("rose", (26, 17), (27, 15), (31, 12), (34, 12), (35, 14),
           (31, 14), (28, 17))
    d.path("rose", (30, 8), (32, 6), (35, 6), (36, 8), (34, 10), (31, 9))
    d.path("rose", (23, 21), (26, 20), (35, 20), (40, 19), (40, 22),
           (36, 23), (26, 24), (24, 23))
    d.line("blush", (25, 21), (33, 21))
    d.box("slate", 29, 26, 5, 2)
    return d.ops


def gear(facing, stage=3):
    mirror = facing == "right"
    d = Drawing(GEAR, mirror=mirror)
    if facing in ("left", "right"):
        d.path("ink", (34, 31), (38, 28), (43, 28), (47, 30), (49, 37),
               (49, 44), (46, 46), (38, 45), (34, 41))
        if stage > 1:
            d.path("moss", (35, 32), (39, 29), (43, 29), (47, 31), (48, 37),
                   (48, 43), (45, 45), (39, 44), (36, 41))
            d.path("sage", (37, 33), (40, 30), (44, 31), (46, 34),
                   (46, 41), (44, 43), (40, 42), (37, 40))
            d.path("leaf", (38, 33), (40, 31), (44, 32), (45, 34), (38, 35))
            d.line("ink", (37, 36), (46, 36))
            d.box("snow", 43, 36, 2, 3)
            d.line("leaf", (41, 40), (45, 40))
            if mirror:
                d.line("ice", (46, 32), (47, 35))
            else:
                d.line("ice", (38, 32), (40, 31))
    elif facing == "up":
        d.path("ink", (23, 34), (27, 30), (37, 30), (41, 33), (42, 41),
               (40, 45), (35, 47), (27, 47), (23, 44), (22, 38))
        d.path("moss", (24, 34), (28, 31), (37, 31), (40, 34), (41, 40),
               (39, 44), (34, 46), (28, 46), (24, 43), (23, 37))
        d.path("sage", (25, 34), (29, 32), (36, 32), (39, 35), (39, 41),
               (36, 44), (27, 44), (25, 42))
        d.path("leaf", (25, 34), (28, 32), (36, 32), (39, 34), (36, 37),
               (29, 38), (25, 37))
        d.path("ice", (27, 35), (28, 33), (32, 33), (34, 34), (30, 34), (28, 36))
        d.line("ink", (29, 38), (36, 37))
        d.box("snow", 31, 37, 3, 3)
        d.box("rust", 32, 38, 1, 1)
        d.line("leaf", (27, 42), (37, 42))
        d.path("ice", (30, 43), (32, 40), (34, 43))
        d.box("moss", 31, 43, 2, 1)
    elif stage > 1:
        d.line("ink", (37, 30), (28, 44))
        d.line("moss", (37, 31), (29, 43))
        d.path("ink", (22, 39), (26, 38), (30, 40), (29, 46), (27, 48), (22, 47), (21, 43))
        d.path("moss", (22, 41), (26, 39), (29, 41), (28, 46), (23, 47), (22, 45))
        d.path("sage", (23, 41), (26, 40), (28, 41), (27, 45), (23, 45))
        d.line("leaf", (23, 42), (27, 41))
        d.box("snow", 25, 42, 2, 2)
    else:
        d.path("ink", (22, 39), (26, 38), (30, 40), (29, 46), (27, 48), (22, 47), (21, 43))
    if facing == "down":
        d.path("ink", (24, 26), (28, 27), (35, 27), (39, 25), (40, 29),
               (37, 32), (29, 34), (24, 31))
        if stage > 1:
            d.path("wine", (25, 27), (29, 28), (35, 28), (38, 27), (39, 29),
                   (36, 31), (29, 33), (25, 31))
            d.line("rose", (26, 29), (34, 29))
            d.line("berry", (30, 32), (36, 30))
    elif facing == "up":
        d.path("ink", (24, 26), (28, 26), (37, 25), (40, 26), (39, 30), (34, 31), (25, 30))
        d.path("wine", (25, 27), (36, 26), (39, 27), (38, 29), (33, 30), (25, 29))
        d.line("rose", (26, 27), (34, 27))
    else:
        d.path("ink", (23, 26), (30, 27), (35, 26), (39, 24), (40, 28), (36, 32),
               (30, 33), (24, 31), (22, 29))
        d.path("wine", (24, 27), (31, 28), (38, 26), (38, 28), (35, 31),
               (30, 32), (24, 30))
        d.line("rose", (25, 28), (31, 29))
    return d.ops


def scarf_tail(facing, pose, bob=0):
    if facing not in ("left", "right"):
        return []
    d = Drawing(SCARF_TAIL, mirror=facing == "right", dy=bob)
    sway = (0, 0, 2, 0, -1)[pose]
    d.path("ink", (38, 26), (43, 25), (48, 25 + sway), (53, 23 + sway),
           (51, 28 + sway), (47, 30 + sway), (40, 29), (36, 30))
    d.path("berry", (38, 27), (43, 26), (48, 26 + sway), (51, 25 + sway),
           (50, 28 + sway), (47, 29 + sway), (41, 28), (37, 29))
    d.line("rose", (41, 27), (49, 27 + sway))
    return d.ops


def boots(facing, pose, stage=3):
    lateral = facing in ("left", "right")
    d = Drawing(LEGS, mirror=facing == "right")
    if lateral:
        shifts = ((-2, 2, 0, -1), (-7, 5, 0, -1), (1, -1, -4, 0),
                  (6, -7, -1, 0), (0, -2, 0, -4))
        front, back, front_up, back_up = shifts[pose]
        feet = [(33, 35 + back, 57 + back_up, True), (29, 29 + front, 57 + front_up, False)]
    else:
        shifts = ((0, 0, 0, 0), (-1, 2, 0, -3), (0, 0, -4, 0),
                  (-2, 1, -3, 0), (0, 0, 0, -4))
        left, right, left_up, right_up = shifts[pose]
        feet = [(27, 27 + left, 57 + left_up, left_up < right_up),
                (36, 36 + right, 57 + right_up, right_up < left_up)]
        feet.sort(key=lambda foot: not foot[3])

    for hip, foot, heel_y, far in feet:
        toe = foot - (5 if lateral else 4)
        heel = foot + (3 if lateral else 4)
        d.path("ink", (hip - 4, 43), (hip + 4, 43), (foot + 4, heel_y - 5),
               (heel, heel_y), (toe, heel_y), (toe - 1, heel_y - 2),
               (toe + 1, heel_y - 5), (hip - 4, 49))
        if stage == 1:
            continue
        d.path("deep_teal", (hip - 3, 44), (hip + 3, 44), (foot + 3, heel_y - 5),
               (foot + 2, heel_y - 3), (foot - 2, heel_y - 3), (hip - 3, 49))
        if not far:
            d.path("teal", (hip - 3, 45), (hip + 1, 45), (foot + 1, heel_y - 6),
                   (foot - 2, heel_y - 5), (hip - 2, 49))
            d.line("foam", (hip - 2, 47), (foot - 1, heel_y - 6))
        d.path("slate", (toe + 2, heel_y - 4), (heel - 1, heel_y - 4),
               (heel - 1, heel_y - 1), (toe, heel_y - 1), (toe, heel_y - 2))
        if stage == 3:
            d.line("foam" if far else "ice", (toe + 1, heel_y - 1), (heel - 1, heel_y - 1))
            d.box("teal" if far else "foam", foot - 1, heel_y - 4, 3, 1)
    return d.ops


def sleeve(d, shoulder, hand, bright, stage):
    sx, sy = shoulder
    hx, hy = hand
    d.path("ink", (sx - 3, sy), (sx + 2, sy - 1), (sx + 4, sy + 3),
           (hx + 3, hy - 1), (hx + 2, hy + 2), (hx - 2, hy + 2),
           (hx - 4, hy - 1), (sx - 4, sy + 4))
    if stage == 1:
        return
    d.path("ochre" if bright else "rust", (sx - 2, sy + 1), (sx + 2, sy + 1),
           (sx + 3, sy + 3), (hx + 2, hy - 1), (hx - 2, hy),
           (hx - 3, hy - 2), (sx - 3, sy + 4))
    if bright:
        d.path("honey", (sx - 2, sy + 1), (sx + 1, sy + 1), (sx + 1, sy + 4),
               (hx, hy - 2), (hx - 2, hy - 2), (sx - 2, sy + 4))
    d.line("sun" if bright else "honey", (hx - 2, hy - 2), (hx + 1, hy - 2))
    d.box("deep_teal", hx - 2, hy - 1, 4, 2)
    if stage == 3 and bright:
        d.box("foam", hx - 1, hy, 2, 1)


def arms(facing, pose, stage=3, bob=0):
    d = Drawing(ARMS, mirror=facing == "right", dy=bob)
    arm_swing = (0, 4, 0, -4, 0)[pose]
    if facing in ("left", "right"):
        sleeve(d, (31, 33), (31 + arm_swing, 44 - abs(arm_swing) // 2),
               facing == "left", stage)
    else:
        turn = 1 if facing == "down" else -1
        left, right = turn * arm_swing, -turn * arm_swing
        sleeve(d, (22, 33), (19 + left // 3, 43 + left // 2), True, stage)
        sleeve(d, (40, 33), (43 + right // 3, 43 + right // 2), False, stage)
    return d.ops


def build(cli, output, proof_dir=None):
    output.mkdir(parents=True, exist_ok=True)
    project = output / "alpine-courier.pxf.json"
    if project.exists():
        raise FileExistsError(f"Choose a fresh output directory: {project}")
    sheet = output / "alpine-courier.png"
    atlas = output / "alpine-courier.atlas.json"
    trajectory = []
    tool_request_count = 0

    def run(*args, **kwargs):
        proc = subprocess.run([cli, *map(str, args)], text=True, capture_output=True, **kwargs)
        trajectory.append({"argv": [str(arg) for arg in args], "exit_code": proc.returncode})
        if proc.returncode:
            raise RuntimeError(f"{args[0]} failed:\n{proc.stderr}\n{proc.stdout[-1500:]}")
        return proc.stdout

    def call(ops):
        nonlocal tool_request_count
        tool_request_count += len(ops)
        run("call", "--project", project, input=json.dumps(ops))

    version = run("--version").strip()
    if version != "pixelforge 0.1.0-rc.6":
        raise ValueError(f"Recipe pinned to pixelforge 0.1.0-rc.6, found {version}")
    run("new", "--width", 64, "--height", 64, "--output", project)
    palette_file = output / "alpine-courier.hex"
    palette_file.write_text("\n".join(PALETTE.values()) + "\n", encoding="utf-8")
    run("palette", "import", "--mode", "replace", "--file", palette_file, "--project", project)
    run("layer", "rename", "--name", "boots-and-trousers", "--project", project)
    for layer in ("face-and-jacket", "pack-and-scarf", "sleeves", "scarf-tail"):
        run("layer", "add", "--name", layer, "--project", project)
    if proof_dir:
        proof_dir.mkdir(parents=True, exist_ok=True)
        for stage, name in ((1, "silhouette"), (2, "flats")):
            call([request("eraseRect", x=0, y=0, width=64, height=64, layer=index)
                  for index in range(4)] + boots("down", 0, stage) + front_body(stage)
                 + gear("down", stage) + arms("down", 0, stage))
            result = run("preview", "--project", project, "--scale", 4, "--output", proof_dir / f"{name}.png")
            (proof_dir / f"{name}.json").write_text(result, encoding="utf-8")
        call([request("eraseRect", x=0, y=0, width=64, height=64, layer=index) for index in range(4)])

    for row, facing in enumerate(FACINGS):
        frame = row * len(DELAYS)
        head_and_jacket = (
            front_body(3) if facing == "down"
            else back_body() if facing == "up"
            else profile_body(facing == "right")
        )
        ops = []
        if frame:
            ops += [request("addFrame"), request("setActiveFrame", index=frame)]
        call(ops + boots(facing, 0) + head_and_jacket + gear(facing) + arms(facing, 0)
             + scarf_tail(facing, 0)
             + [request("setFrameDelay", index=frame, delayMs=DELAYS[0])])

        # Copies are inserted after idle. Add in reverse order so the final
        # row is idle, left contact, left passing, right contact, right passing.
        for pose in range(4, 0, -1):
            bob = (0, 0, -1, 0, -1)[pose]
            ops = [request("duplicateFrame", index=frame),
                   request("setActiveFrame", index=frame + 1)]
            moving_layers = (LEGS, ARMS, SCARF_TAIL) if facing in ("left", "right") else (LEGS, ARMS)
            for index in moving_layers:
                ops.append(request("eraseRect", x=0, y=0, width=64, height=64, layer=index))
            if bob:
                for index in (BODY, GEAR):
                    ops.append(request("moveRect", srcX=16, srcY=3, width=42, height=49,
                                       dstX=16, dstY=3 + bob, layer=index))
            ops += boots(facing, pose) + arms(facing, pose, bob=bob) + scarf_tail(facing, pose, bob=bob)
            call(ops + [request("setFrameDelay", index=frame + 1, delayMs=DELAYS[pose])])

    run("direction", "set", "--count", 4, "--columns", 5, "--apply", "--project", project)
    run("frame", "select", "--index", 0, "--project", project)
    run("layer", "select", "--index", BODY, "--project", project)
    direction = run("direction", "validate", "--project", project)
    run("export", "sheet", "--project", project, "--output", sheet, "--cols", 5, "--atlas", atlas)
    validation = run("validate-atlas", "--atlas", atlas, "--sheet", sheet, "--strict", "--four-direction", "on")
    for facing in FACINGS:
        run("export", "apng", "--project", project, "--output",
            output / f"walk-{facing}.apng", "--tag", f"walk_{facing}")
    run("preview", "--project", project, "--output", output / "courier-front.png", "--scale", 4)
    run("export", "sheet", "--project", project, "--output", output / "courier-preview.png", "--cols", 5, "--scale", 3)

    atlas_data = json.loads(atlas.read_text(encoding="utf-8"))
    if len(atlas_data["frames"]) != 20:
        raise ValueError("Expected 20 exported frames")
    if [f["delayMs"] for f in atlas_data["frames"]] != list(DELAYS) * 4:
        raise ValueError("Exported frame timing has changed")
    differences = {}
    for row, facing in enumerate(FACINGS):
        first = row * len(DELAYS) + 1
        last = first + 3
        differences[facing] = []
        for frame in range(first, last + 1):
            following = frame + 1 if frame < last else first
            with tempfile.TemporaryDirectory() as scratch:
                raw = run("diff", "--project", project, "--frame", frame, "--with", following,
                          "--output", Path(scratch) / "walk-diff.png")
            difference = json.loads(raw)["result"]["changed"]
            if not difference:
                raise ValueError(f"{facing} walk frames {frame} and {following} are duplicates")
            differences[facing].append(difference)
    report = {
        "cliVersion": version,
        "cliBinarySha256": hashlib.sha256(Path(cli).read_bytes()).hexdigest(),
        "direction": json.loads(direction)["result"],
        "atlas": json.loads(validation)["result"],
        "walkNeighborChangedPixels": differences,
        "toolRequestsInBatches": tool_request_count,
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (project, sheet, atlas)},
        "aestheticApproval": False,
    }
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "trajectory.jsonl").write_text(
        "\n".join(json.dumps(entry) for entry in trajectory) + "\n", encoding="utf-8"
    )
    print(f"{version} | {len(atlas_data['frames'])} frames | {len(trajectory)} CLI invocations | "
          f"{tool_request_count} batched tool requests | {output}")


if __name__ == "__main__":
    opts = argparse.ArgumentParser(description=__doc__)
    opts.add_argument("--pixelforge", type=Path, required=True, help="Path to official rc.6 executable")
    opts.add_argument("--out", type=Path, required=True)
    opts.add_argument("--proof-dir", type=Path)
    args = opts.parse_args()
    build(args.pixelforge.resolve(), args.out.resolve(), args.proof_dir)
