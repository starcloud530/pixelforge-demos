#!/usr/bin/env python3
"""Replay twelve explicitly authored poses using PixelForge pixel tools only.

No rig, IK, curves, or bake: copy the body frame, edit the pose delta, and
redraw moving layers with kernel primitives. Python only composes requests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess


class Canvas:
    def __init__(self, binary, project, work):
        self.binary, self.project, self.work = binary, project, work
        self.requests = []

    def cli(self, *args):
        proc = subprocess.run([self.binary, *map(str, args)], capture_output=True, text=True)
        bodies = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
        if proc.returncode or any(not b.get("ok") for b in bodies):
            raise RuntimeError(proc.stderr + "\n" + proc.stdout[-2000:])
        return bodies

    def req(self, tool, **params):
        self.requests.append(dict(tool=tool, params=params))

    def flush(self, name):
        path = self.work / (name + ".requests.json")
        path.write_text(json.dumps(self.requests))
        self.cli("call", "--project", self.project, "--request-file", path)
        self.requests.clear()

    def poly(self, points, color):
        self.req(
            "polygon",
            points=[dict(x=round(x), y=round(y)) for x, y in points],
            colorIndex=color,
            fill=True,
        )

    def rect(self, x, y, w, h, color):
        self.req(
            "fillRect",
            x=round(x),
            y=round(y),
            width=max(1, round(w)),
            height=max(1, round(h)),
            colorIndex=color,
        )

    def ell(self, x, y, w, h, color):
        self.req(
            "ellipse",
            x=round(x),
            y=round(y),
            width=max(1, round(w)),
            height=max(1, round(h)),
            colorIndex=color,
            fill=True,
        )

    def line(self, x, y, X, Y, color):
        self.req("line", x0=round(x), y0=round(y), x1=round(X), y1=round(Y), colorIndex=color)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(path):
    # Whitespace only; indexed pixels are authored exclusively by the CLI.
    path.write_text(json.dumps(json.loads(path.read_text()), separators=(",", ":")) + "\n")


def segment(a, b, width, outline, fill):
    x, y = a
    X, Y = b
    l = math.hypot(X - x, Y - y)
    if l == 0:
        d.ell(x - width / 2, y - width / 2, width, width, fill)
        return
    nx = -(Y - y) / l
    ny = (X - x) / l
    for w, c in [(width, outline), (width - 2, fill)]:
        d.poly(
            [
                (x + nx * w / 2, y + ny * w / 2),
                (X + nx * w / 2, Y + ny * w / 2),
                (X - nx * w / 2, Y - ny * w / 2),
                (x - nx * w / 2, y - ny * w / 2),
            ],
            c,
        )


def wheel(x, y, phase, lift=0):
    # Solid fire wheel core, moving flame tongues and rotating spoke marks.
    d.poly(
        [
            (x - 10, y),
            (x - 12 - phase % 3, y - 4),
            (x - 6, y - 2),
            (x - 5, y - 8 - phase % 2),
            (x - 1, y - 3),
            (x + 3, y - 7),
            (x + 6, y - 2),
            (x + 11, y - 3),
            (x + 8, y + 2),
            (x + 4, y + 5),
            (x - 6, y + 4),
        ],
        25,
    )
    d.ell(x - 9, y - 3, 19, 9, 26)
    d.ell(x - 7, y - 2, 15, 6, 28)
    d.ell(x - 5, y - 1, 11, 4, 16)
    a = phase * 0.8
    d.line(
        x - 4 * math.cos(a),
        y + 1 - 2 * math.sin(a),
        x + 4 * math.cos(a),
        y + 1 + 2 * math.sin(a),
        19,
    )
    d.line(
        x - 3 * math.sin(a),
        y + 1 + 2 * math.cos(a),
        x + 3 * math.sin(a),
        y + 1 - 2 * math.cos(a),
        18,
    )


def ribbon(x, y, lag, lower=False):
    # A trailing strip: end displacement lags the torso and overshoots on recovery.
    tail = lag * 1.5
    v = 4 if lower else 0
    pts = [
        (x, y),
        (x - 9, y - 5),
        (x - 18, y - 3),
        (x - 21 + lag * 0.3, y + 10),
        (x - 28 + lag, y + 20 + v),
        (x - 35 + tail, y + 14 + v),
        (x - 28 + tail, y + 28 + v),
        (x - 17 + lag, y + 22),
        (x - 14, y + 6),
        (x - 8, y + 1),
        (x, y + 4),
    ]
    d.poly(pts, 1)
    d.poly(
        [
            (x - 1, y + 1),
            (x - 9, y - 3),
            (x - 16, y - 1),
            (x - 18 + lag * 0.3, y + 11),
            (x - 27 + lag, y + 23 + v),
            (x - 31 + tail, y + 20 + v),
            (x - 27 + tail, y + 25 + v),
            (x - 20 + lag, y + 21),
            (x - 16, y + 5),
            (x - 8, y - 1),
        ],
        11 if lower else 12,
    )
    d.line(x - 15, y + 1, x - 18 + lag * 0.3, y + 10, 14)
    d.line(x - 23 + lag, y + 21, x - 27 + tail, y + 24 + v, 17)


def main():
    global d
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixelforge", default=os.environ.get("PIXELFORGE", "pixelforge"))
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    binary = shutil.which(args.pixelforge)
    if not binary:
        raise SystemExit("set PIXELFORGE or pass --pixelforge")
    script = Path(__file__).resolve().parent
    root = Path(args.out).resolve() if args.out else script
    work, final, reports = root / "work", root / "final", root / "reports"
    for path in [work, final / "frames", final / "poses", reports, root / "source"]:
        path.mkdir(parents=True, exist_ok=True)
    if root != script:
        shutil.copy(script / "brief.json", root / "brief.json")
        for name in ["body.pxf.json", "poses.json"]:
            shutil.copy(script / "source" / name, root / "source" / name)
    motion = json.loads((root / "source/poses.json").read_text())
    poses = [
        (*f["body"]["offset"], *f["weapon"]["grip"], f["weapon"]["angleDegrees"], f["delayMs"])
        for f in motion["frames"]
    ]
    feet = [(*f["feet"]["front"], *f["feet"]["rear"]) for f in motion["frames"]]
    lags = [f["ribbonLag"] for f in motion["frames"]]
    project = work / "nezha-attack.pxf.json"
    shutil.copy(root / "source/body.pxf.json", project)
    d = Canvas(binary, project, work)
    for i, (dx, dy, hx, hy, angle, delay) in enumerate(poses):
        if i:
            d.req("duplicateFrame", index=i - 1)
            d.req("setActiveFrame", index=i)
            d.req(
                "copyRect",
                fromFrame=0,
                toFrame=i,
                srcX=0,
                srcY=0,
                width=128,
                height=128,
                dstX=0,
                dstY=0,
                layer=2,
            )
            if dx or dy:
                d.req(
                    "moveRect",
                    srcX=34,
                    srcY=16,
                    width=45,
                    height=64,
                    dstX=34 + dx,
                    dstY=16 + dy,
                    layer=2,
                )
            # The head leads the thrust and recoils before the cloth settles.
            lean = motion["frames"][i]["body"]["headLean"]
            if lean:
                d.req(
                    "moveRect",
                    srcX=40 + dx,
                    srcY=20 + dy,
                    width=35,
                    height=39,
                    dstX=40 + dx + lean,
                    dstY=20 + dy,
                    layer=2,
                )
        # Independent secondary motion behind the body.
        d.req("setActiveLayer", index=0)
        d.req("eraseRect", x=0, y=0, width=128, height=128, layer=0)
        ribbon(55 + dx, 61 + dy, lags[i], True)
        ribbon(61 + dx, 63 + dy, lags[i] + 2)
        # Kinetic chain from hip through bent knees to planted or airborne feet.
        d.req("setActiveLayer", index=1)
        d.req("eraseRect", x=0, y=0, width=128, height=128, layer=1)
        fx, fy, bx, by = feet[i]
        wheel(bx, by, i)
        bk = (49 + dx * 0.3, 88 + dy * 0.4)
        segment((53 + dx, 79 + dy), bk, 8, 1, 6)
        segment(bk, (bx, by - 6), 6, 1, 7)
        d.poly([(bx - 4, by - 9), (bx + 2, by - 9), (bx + 5, by - 5), (bx - 4, by - 5)], 11)
        d.line(bx - 3, by - 9, bx + 2, by - 9, 17)
        wheel(fx, fy, i + 2)
        fk = ((57 + dx + fx) * 0.5 + 2, 87 + dy * 0.3 - (100 - fy) * 0.3)
        segment((59 + dx, 79 + dy), fk, 9, 1, 7)
        segment(fk, (fx, fy - 6), 7, 1, 8)
        d.poly([(fx - 4, fy - 9), (fx + 2, fy - 9), (fx + 6, fy - 5), (fx - 4, fy - 5)], 12)
        d.line(fx - 3, fy - 9, fx + 2, fy - 9, 18)
        d.poly(
            [
                (50 + dx, 75 + dy),
                (61 + dx, 75 + dy),
                (65 + dx, 81 + dy),
                (59 + dx, 85 + dy),
                (55 + dx, 82 + dy),
                (51 + dx, 85 + dy),
            ],
            11,
        )
        d.poly([(57 + dx, 77 + dy), (61 + dx, 77 + dy), (63 + dx, 81 + dy), (59 + dx, 83 + dy)], 13)
        d.req("setActiveLayer", index=3)
        d.req("eraseRect", x=0, y=0, width=128, height=128, layer=3)
        # Far arm supports the shaft; near arm drives the thrust.
        segment((52 + dx, 61 + dy), (56 + dx, 68 + dy), 6, 1, 6)
        segment((56 + dx, 68 + dy), (hx - 10, hy + 1), 5, 1, 7)
        segment((60 + dx, 60 + dy), (66 + dx, 65 + dy), 7, 1, 7)
        segment((66 + dx, 65 + dy), (hx, hy), 6, 1, 8)
        a = math.radians(angle)
        ux = math.cos(a)
        uy = math.sin(a)
        nx = -uy
        ny = ux

        def p(t, w=0):
            return (hx + t * ux + w * nx, hy + t * uy + w * ny)

        # Shaft, gold grip, metal point and a small persistent flame.
        segment(p(-24), p(35), 3, 1, 16)
        d.line(*p(-22, -0.6), *p(33, -0.6), 18)
        d.poly([p(42), p(34, 3), p(30, 2), p(30, -2), p(34, -3)], 1)
        d.poly([p(42), p(34, 2), p(31), p(34, -2)], 17)
        d.poly([p(43), p(38, 3), p(34, 5), p(36, 1), p(32, -2), p(37, -1), p(38, -3)], 26)
        d.poly([p(42), p(38, 1.5), p(36), p(38, -1)], 19)
        lag = lags[i] * 0.6
        d.poly([p(30, 2), p(26 + lag, 8), p(27, 3), p(22 + lag, 6), p(25 + lag, 1), p(30, -2)], 12)
        d.line(*p(30, -2), *p(30, 2), 18)
        # Warm knuckles and wrist cuff drawn above the weapon.
        d.ell(hx - 3, hy - 2, 6, 5, 6)
        d.rect(hx - 2, hy - 2, 4, 3, 9)
        d.ell(hx - 13, hy - 1, 5, 4, 7)
        d.line(hx - 12, hy, hx - 10, hy, 9)
        d.line(64 + dx, 64 + dy, 65 + dx, 67 + dy, 17)
        if i in [4, 5, 6, 7]:
            length = {4: 10, 5: 23, 6: 17, 7: 8}[i]
            d.line(92 - length, 60, 92, 60, 28)
            d.line(112 - length, 73, 112, 73, 17)
            if i in [5, 6]:
                d.line(104, 57, 118, 57, 19)
        if i in [4, 5, 6, 7, 8]:
            # Brief rear sparks record push-off; the front foot does not slide after contact.
            for x, y in [(bx - 15, by + 2), (bx - 20, by), (bx - 12, by - 5)]:
                if x > 0:
                    d.line(x - 3, y, x, y - 1, 27)
        d.req("setFrameDelay", index=i, delayMs=delay)
        d.flush("attack-" + str(i).zfill(2))
    d.req("setActiveFrame", index=0)
    d.req("addTag", name="attack_right", **{"from": 0, "to": 11, "loop": "forward"})
    for name, a, b in [("ready", 0, 0), ("charge", 1, 3), ("thrust", 4, 6), ("recover", 7, 11)]:
        d.req("addTag", name=name, **{"from": a, "to": b, "loop": "once"})
    d.flush("tags")
    d.cli("export", "png", "--project", project, "--out-dir", final / "frames")
    d.cli("export", "png", "--project", project, "--out-dir", work / "preview-frames", "--scale", 4)
    d.cli(
        "export",
        "sheet",
        "--project",
        project,
        "--output",
        final / "nezha-attack-sheet.png",
        "--cols",
        6,
        "--atlas",
        final / "nezha-attack.atlas.json",
    )
    d.cli(
        "export",
        "apng",
        "--project",
        project,
        "--output",
        final / "nezha-attack.apng",
        "--tag",
        "attack_right",
        "--scale",
        4,
    )
    for frame, name in [(0, "ready"), (2, "charge"), (5, "thrust"), (8, "recover")]:
        shutil.copy(
            work / "preview-frames" / f"pixelforge-{frame:03d}.png",
            final / "poses" / f"{frame:02d}-{name}.png",
        )
    # Packaging only; sprite pixels and nearest-neighbor scaling come from CLI.
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(final / "nezha-attack.apng"),
            "-filter_complex",
            "[0:v]split[s][m];[m]lutrgb=r=35:g=42:b=58,format=rgb24[bg];[bg][s]overlay=shortest=1,split[a][b];[a]palettegen=reserve_transparent=0[p];[b][p]paletteuse=dither=none",
            "-fps_mode",
            "passthrough",
            "-enc_time_base",
            "1:100",
            "-loop",
            "0",
            str(final / "nezha-attack.gif"),
        ],
        check=True,
        capture_output=True,
    )
    shutil.copy(project, final / "nezha-attack.pxf.json")
    compact(final / "nezha-attack.pxf.json")
    version = subprocess.check_output([binary, "--version"], text=True).strip()
    names = [
        "source/body.pxf.json",
        "source/poses.json",
        "final/nezha-attack.pxf.json",
        "final/nezha-attack-sheet.png",
        "final/nezha-attack.atlas.json",
        "final/nezha-attack.apng",
        "final/nezha-attack.gif",
    ]
    stamp = dict(
        cliVersion=version,
        cliSha256=sha256(Path(binary)),
        frameCount=12,
        frameDelaysMs=[p[-1] for p in poses],
        totalMs=sum(p[-1] for p in poses),
        method="explicit frame poses; no curves, IK, constraints, or bake",
        aestheticApproval=False,
        sha256={name: sha256(root / name) for name in names},
    )
    # Source files belong to the demo, so --out builds copy them too.
    (reports / "stamp.json").write_text(json.dumps(stamp, indent=2) + "\n")
    print("Built Nezha frame animation:", final / "nezha-attack.gif")


if __name__ == "__main__":
    main()
