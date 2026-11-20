"""Draw original 32px inventory icons with the published PixelForge CLI."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

COLORS = {
    "ink": "182b37",
    "slate": "304856",
    "steel": "536d78",
    "silver": "87a6a7",
    "foam": "d4ebd6",
    "deep": "225856",
    "sea": "40877b",
    "mint": "79bd9d",
    "warm": "81453a",
    "copper": "b76246",
    "amber": "df9556",
    "gold": "f5c47b",
    "paper_shadow": "a78359",
    "paper": "dec18e",
    "cream": "ffdfa2",
}
DUSK_COLORS = dict(zip(COLORS, (
    "211e35", "3b3458", "645580", "ae8eb8", "ddfaf2",
    "234c60", "327c8d", "60cad2", "713952", "a65070",
    "d67e89", "f4aba4", "856888", "b798b7", "f4cbd8",
)))
INDEX = {name: index for index, name in enumerate(COLORS, start=1)}


def request(tool, **params):
    return {"tool": tool, "params": params}


def box(color, x, y, width, height):
    return request("fillRect", x=x, y=y, width=width, height=height, colorIndex=INDEX[color])


def dot(color, x, y):
    return request("paint", x=x, y=y, colorIndex=INDEX[color])


def line(color, x0, y0, x1, y1):
    return request("line", x0=x0, y0=y0, x1=x1, y1=y1, colorIndex=INDEX[color], pixelPerfect=True)


def oval(color, x, y, width, height):
    return request("ellipse", x=x, y=y, width=width, height=height, colorIndex=INDEX[color], fill=True)


def shape(color, *coordinates):
    points = [{"x": x, "y": y} for x, y in coordinates]
    return request("polygon", points=points, colorIndex=INDEX[color], fill=True)


ICONS = {
    "brass_compass": [
        oval("ink", 14, 2, 6, 7), box("silver", 16, 4, 2, 3),
        oval("ink", 4, 6, 24, 23), oval("warm", 5, 7, 22, 21),
        oval("amber", 5, 7, 21, 19), oval("gold", 7, 8, 17, 17),
        oval("ink", 8, 9, 16, 16), oval("slate", 9, 10, 14, 14),
        oval("deep", 10, 11, 12, 12),
        dot("mint", 16, 11), dot("mint", 16, 22), dot("mint", 10, 17), dot("mint", 21, 17),
        shape("foam", (19, 13), (15, 19), (12, 21), (14, 16)),
        shape("copper", (19, 13), (17, 18), (15, 19), (14, 16)),
        line("gold", 15, 16, 19, 13), dot("cream", 15, 17),
        line("cream", 10, 9, 13, 8), dot("gold", 21, 25),
    ],
    "sample_vial": [
        shape("ink", (10, 3), (20, 3), (22, 6), (21, 10), (25, 15), (25, 24), (22, 28), (9, 28), (6, 24), (6, 15), (10, 10), (9, 7)),
        shape("steel", (11, 9), (20, 9), (20, 12), (24, 16), (24, 23), (21, 27), (10, 27), (7, 23), (7, 16), (11, 12)),
        shape("deep", (8, 19), (13, 17), (20, 19), (23, 17), (23, 23), (21, 25), (10, 25), (8, 23)),
        shape("sea", (8, 19), (13, 17), (19, 19), (22, 18), (21, 23), (16, 24), (10, 23)),
        line("mint", 9, 19, 13, 18), line("silver", 9, 15, 12, 12), box("foam", 9, 16, 1, 4),
        dot("foam", 13, 21), dot("mint", 16, 22), dot("mint", 19, 20),
        box("warm", 10, 4, 11, 5), box("copper", 11, 4, 9, 4), line("gold", 12, 4, 19, 4),
        line("ink", 11, 9, 20, 9), dot("amber", 13, 6), dot("amber", 17, 6),
        box("paper_shadow", 16, 13, 5, 4), box("paper", 16, 13, 4, 3), dot("warm", 18, 14),
        line("silver", 11, 26, 19, 26),
    ],
    "sample_tongs": [
        shape("ink", (6, 4), (10, 6), (16, 13), (23, 8), (27, 8), (28, 12), (25, 15), (20, 16), (28, 25), (27, 28), (23, 28), (14, 19), (11, 25), (7, 26), (4, 23), (4, 19), (10, 15), (4, 8)),
        shape("steel", (6, 5), (10, 7), (26, 25), (26, 27), (24, 27), (7, 10), (5, 8)),
        shape("silver", (6, 5), (9, 7), (25, 24), (24, 25), (7, 9), (5, 7)),
        shape("slate", (5, 20), (10, 17), (23, 10), (27, 9), (26, 12), (24, 14), (18, 15), (12, 20), (10, 24), (8, 25), (5, 23)),
        line("silver", 8, 22, 23, 11), line("foam", 24, 10, 26, 9),
        shape("warm", (5, 20), (8, 18), (11, 21), (10, 24), (8, 25), (5, 23)),
        line("amber", 6, 21, 9, 19), dot("gold", 6, 22),
        oval("ink", 12, 12, 7, 7), oval("amber", 13, 13, 5, 5), oval("copper", 14, 14, 3, 3),
        dot("cream", 14, 14), line("slate", 20, 21, 21, 20), line("slate", 22, 23, 23, 22), dot("foam", 24, 25),
    ],
    "tide_chart": [
        shape("ink", (5, 4), (13, 6), (21, 4), (26, 6), (27, 25), (20, 26), (14, 29), (5, 27), (3, 24)),
        shape("paper_shadow", (5, 5), (13, 7), (21, 5), (25, 7), (26, 24), (20, 25), (14, 28), (6, 26), (4, 24)),
        shape("paper", (5, 5), (13, 7), (21, 5), (25, 7), (25, 22), (20, 23), (14, 26), (6, 24), (4, 22)),
        shape("cream", (5, 6), (12, 8), (12, 24), (6, 23), (5, 21)),
        line("warm", 13, 8, 13, 25), line("cream", 14, 8, 14, 23),
        line("paper_shadow", 20, 6, 20, 22),
        line("sea", 7, 20, 10, 18), line("sea", 10, 18, 14, 18), line("sea", 14, 18, 18, 13), line("sea", 18, 13, 23, 15),
        line("mint", 7, 21, 11, 19), line("mint", 16, 19, 20, 16), dot("deep", 23, 15),
        line("paper_shadow", 7, 10, 10, 11), line("paper_shadow", 7, 12, 9, 13),
        line("warm", 21, 9, 23, 11), line("warm", 23, 9, 21, 11), dot("copper", 10, 16),
    ],
    "beacon_buoy": [
        shape("ink", (13, 4), (18, 4), (19, 11), (22, 15), (25, 18), (26, 23), (22, 27), (9, 27), (5, 24), (5, 19), (9, 15), (12, 11)),
        shape("warm", (12, 13), (19, 13), (21, 17), (24, 19), (25, 23), (21, 26), (10, 26), (6, 23), (6, 20), (10, 17)),
        shape("copper", (12, 13), (18, 13), (20, 17), (23, 19), (23, 22), (20, 24), (10, 24), (7, 22), (7, 20), (11, 16)),
        shape("amber", (12, 14), (15, 14), (14, 18), (10, 22), (8, 21), (10, 18)),
        box("slate", 13, 5, 6, 7), box("sea", 14, 6, 4, 5), box("mint", 14, 6, 2, 4), dot("foam", 14, 6),
        box("gold", 13, 12, 6, 1), line("paper", 7, 19, 12, 20), line("cream", 12, 20, 20, 20), line("paper_shadow", 20, 20, 24, 19),
        line("deep", 9, 24, 13, 25), line("deep", 18, 25, 23, 23), dot("gold", 12, 16),
        dot("mint", 10, 7), dot("mint", 22, 7), dot("foam", 16, 2),
    ],
    "field_lens": [
        shape("ink", (17, 17), (21, 17), (29, 25), (29, 27), (26, 30), (24, 30), (16, 22)),
        shape("warm", (18, 18), (21, 18), (28, 25), (28, 27), (26, 29), (24, 29), (17, 22)),
        shape("copper", (18, 19), (20, 18), (27, 25), (24, 27), (17, 21)),
        line("gold", 21, 21, 25, 25), line("ink", 24, 27, 27, 24), dot("amber", 25, 28),
        oval("ink", 3, 3, 21, 21), oval("warm", 4, 4, 19, 19),
        oval("amber", 4, 4, 17, 17), oval("gold", 5, 5, 15, 15),
        oval("slate", 6, 6, 14, 14), oval("deep", 7, 7, 12, 12),
        shape("sea", (9, 9), (12, 8), (16, 9), (9, 16), (8, 13)),
        line("mint", 9, 13, 13, 9), line("foam", 9, 11, 11, 9),
        dot("silver", 15, 16), dot("mint", 16, 15), line("gold", 13, 21, 17, 20),
    ],
    "specimen_case": [
        shape("ink", (7, 8), (11, 5), (20, 5), (26, 8), (29, 13), (29, 24), (25, 28), (6, 28), (3, 25), (3, 13)),
        box("steel", 12, 6, 8, 4), box("ink", 13, 7, 6, 3), line("silver", 13, 6, 18, 6),
        shape("deep", (4, 13), (26, 12), (28, 14), (28, 24), (25, 27), (6, 27), (4, 24)),
        shape("sea", (4, 15), (25, 15), (25, 23), (22, 25), (6, 25), (4, 23)),
        shape("steel", (7, 9), (23, 9), (27, 12), (27, 15), (4, 15), (4, 12)),
        shape("silver", (7, 9), (22, 9), (24, 11), (6, 12)),
        box("ink", 4, 15, 24, 1), box("warm", 7, 12, 4, 10), box("warm", 21, 12, 4, 10),
        box("copper", 8, 12, 2, 9), box("copper", 22, 12, 2, 9),
        box("gold", 8, 15, 2, 2), box("gold", 22, 15, 2, 2),
        box("deep", 13, 19, 6, 4), line("mint", 14, 20, 17, 20), dot("foam", 15, 21),
        line("mint", 12, 24, 19, 24),
    ],
    "shell_sample": [
        shape("ink", (15, 3), (18, 4), (21, 7), (25, 9), (28, 13), (29, 18), (27, 24), (24, 27), (8, 27), (4, 24), (3, 19), (5, 14), (9, 11), (12, 10)),
        shape("warm", (15, 4), (19, 6), (22, 9), (26, 12), (28, 17), (27, 22), (24, 26), (9, 26), (5, 23), (4, 19), (6, 15), (10, 12), (13, 11)),
        shape("copper", (15, 4), (18, 6), (22, 10), (25, 12), (27, 17), (25, 22), (21, 24), (8, 24), (5, 20), (7, 15), (11, 12), (14, 11)),
        shape("amber", (15, 5), (18, 7), (20, 11), (24, 13), (25, 17), (22, 21), (19, 22), (8, 23), (6, 20), (8, 15), (13, 12)),
        shape("gold", (15, 6), (18, 9), (18, 12), (15, 14), (11, 15), (8, 18), (8, 15), (14, 11)),
        line("gold", 16, 10, 14, 13), line("gold", 17, 15, 22, 15), line("cream", 9, 17, 12, 15),
        shape("warm", (13, 19), (17, 17), (21, 18), (22, 21), (20, 23), (13, 23), (11, 21)),
        shape("slate", (14, 20), (17, 18), (20, 19), (21, 21), (18, 22), (14, 22), (12, 21)),
        line("copper", 18, 24, 24, 22), line("gold", 22, 16, 24, 18),
        line("cream", 16, 7, 17, 8), line("warm", 11, 15, 9, 18),
    ],
}


def build(cli, output):
    output.mkdir(parents=True, exist_ok=True)
    project = "tide-survey-icons.pxf.json"
    if (output / project).exists():
        raise SystemExit("Choose a fresh output folder.")

    def run(*args):
        return subprocess.run([cli, *args], cwd=output, check=True, text=True, capture_output=True).stdout

    def call(operations, target=project):
        args = []
        for operation in operations:
            args.extend(("--request", json.dumps(operation, separators=(",", ":"))))
        return run("call", "--project", target, *args)

    run("--version")
    run("new", "--width", "32", "--height", "32", "--output", project)
    colors = "\n".join("#" + color for color in COLORS.values()) + "\n"
    (output / "tide-survey-palette.hex").write_text(colors)
    call([request("importPalette", text=colors, mode="replace"), request("setPaletteLocked", locked=True)])
    for frame_index, (name, operations) in enumerate(ICONS.items()):
        if frame_index:
            call([request("addFrame"), request("setActiveFrame", index=frame_index)])
        call([*operations, request("addTag", name=name, **{"from": frame_index, "to": frame_index}, loop="once")])
    call([request("setActiveFrame", index=0)])

    dusk = "tide-survey-icons-dusk.pxf.json"
    shutil.copyfile(output / project, output / dusk)
    recolor = [request("setPaletteLocked", locked=False)]
    for name, color in DUSK_COLORS.items():
        r, g, b = bytes.fromhex(color)
        recolor.append(request("setPaletteColor", index=INDEX[name], r=r, g=g, b=b))
    recolor.append(request("setPaletteLocked", locked=True))
    call(recolor, target=dusk)

    checks = ["--size", "32"]
    for name in ICONS:
        checks.extend(("--require-tag", name))
    reports = {}
    for stem in ("tide-survey-icons", "tide-survey-icons-dusk"):
        atlas = stem + ".atlas.json"
        run("export", "sheet", "--project", stem + ".pxf.json", "--cols", "4",
            "--output", stem + ".png", "--atlas", atlas)
        run("export", "sheet", "--project", stem + ".pxf.json", "--cols", "4", "--scale", "4",
            "--output", stem + "-preview.png")
        reports[stem] = json.loads(run("validate-atlas", "--atlas", atlas, *checks))

    base_data = json.loads((output / project).read_text())
    dusk_data = json.loads((output / dusk).read_text())
    assert base_data["frames"] == dusk_data["frames"]
    assert base_data["tags"] == dusk_data["tags"]
    assert base_data["palette"] != dusk_data["palette"]
    checks = {"atlases": reports, "sameIndexedPixelsAndTags": True, "aestheticApproval": False}
    (output / "validation.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixelforge", default=os.environ.get("PIXELFORGE_BIN", "pixelforge"))
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    build(options.pixelforge, options.out.resolve())
