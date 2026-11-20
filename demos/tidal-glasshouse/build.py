#!/usr/bin/env python3
"""Draw the tidal glasshouse and build its orthogonal map using PixelForge."""
import argparse
import json
import os
import random
import shutil
import struct
import subprocess
from pathlib import Path

PALETTE = {
    "ink": "111e2c", "midnight": "142b3b", "water": "173849",
    "water_light": "204a5b", "wave": "2c5b68", "foam": "418089",
    "moss_dark": "233c3a", "moss": "334f43", "grass": "425c49",
    "blade": "526e52", "leaf": "66815b", "sage": "7c956d",
    "stone_dark": "373b43", "stone": "555357", "paver": "696768",
    "stone_light": "848174", "sand": "a99a79",
    "metal_dark": "223c47", "metal": "405d62", "metal_light": "758e89",
    "glass_dark": "284f53", "glass": "3d7774", "glass_light": "58a097",
    "light": "8ec8a5", "shine": "acd9be",
    "wood_dark": "513c3a", "wood": "785348", "copper": "a67553",
    "rust_light": "c68f61", "gold": "e6b269", "cream": "ffe6a8",
    "pink_dark": "965771", "pink": "d397a2",
}
COLOR = {name: i for i, name in enumerate(PALETTE, 1)}
TILE = 32
COLS = 8
MAP_WIDTH = 13
MAP_HEIGHT = 9
LAYERS = ("Base", "Structure", "Details")


def request(tool, **params):
    return {"tool": tool, "params": params}


class Drawing:
    def __init__(self, layer=0):
        self.ops = []
        self.layer = layer

    def rect(self, c, x, y, width, height):
        self.ops.append(request("fillRect", x=x, y=y, width=width, height=height,
                                colorIndex=COLOR[c], layer=self.layer))

    def line(self, c, x0, y0, x1, y1):
        self.ops.append(request("line", x0=x0, y0=y0, x1=x1, y1=y1,
                                colorIndex=COLOR[c], layer=self.layer))

    def dot(self, c, x, y):
        self.rect(c, x, y, 1, 1)

    def oval(self, c, x, y, width, height):
        self.ops.append(request("ellipse", x=x, y=y, width=width, height=height,
                                colorIndex=COLOR[c], fill=True, layer=self.layer))

    def poly(self, c, *points):
        self.ops.append(request("polygon", points=[{"x": x, "y": y} for x, y in points],
                                colorIndex=COLOR[c], fill=True, layer=self.layer))


def glaze_building():
    art = Drawing()
    # Footprint, stone stairs, and silhouette share one canvas before CLI tiling.
    art.oval("moss_dark", 2, 65, 124, 29)
    art.poly("ink", (7, 68), (14, 34), (21, 21), (31, 12), (42, 6),
             (87, 6), (100, 13), (110, 23), (117, 37), (122, 68),
             (120, 82), (114, 88), (13, 88), (7, 84))
    art.poly("stone_dark", (8, 69), (119, 69), (120, 81), (114, 86),
             (13, 86), (8, 82))
    art.rect("stone", 12, 77, 104, 5)
    art.rect("paver", 16, 77, 96, 1)
    for x in range(17, 114, 9):
        art.rect("stone_dark", x, 80, 1, 3)
    art.poly("metal_dark", (10, 61), (15, 43), (21, 25), (34, 13),
             (44, 8), (85, 8), (98, 15), (108, 26), (114, 43), (119, 61),
             (117, 76), (11, 76))
    art.poly("glass_dark", (13, 48), (20, 27), (31, 16), (44, 11),
             (82, 11), (96, 17), (107, 28), (114, 47))
    art.poly("glass", (17, 43), (25, 25), (38, 16), (46, 13), (81, 13),
             (94, 19), (104, 29), (111, 43))
    art.poly("glass_light", (26, 24), (40, 15), (46, 13), (81, 13),
             (94, 19), (98, 23), (55, 25))
    art.poly("light", (33, 21), (45, 14), (62, 14), (48, 19))
    art.poly("glass_dark", (30, 41), (45, 34), (67, 34), (57, 41))
    art.rect("glass_dark", 12, 48, 105, 25)
    art.rect("glass", 21, 48, 84, 22)
    art.rect("glass_light", 31, 48, 64, 15)
    art.rect("glass", 14, 52, 10, 16)
    art.rect("glass", 105, 52, 12, 17)

    art.layer = 1
    # Plants inside the glazing create a lit silhouette behind the ironwork.
    for x, y, size in [(22,60,9),(30,63,11),(38,60,9),(46,65,8),
                        (83,66,8),(91,60,10),(99,62,9),(107,64,8)]:
        art.oval("moss", x-size//2, y-5, size, 9)
        art.oval("grass", x-size//2+1, y-5, size-3, 5)
        art.line("moss_dark", x, y-3, x+1, 70)
        art.line("leaf", x-1, y-4, x+1, y-3)
    # Tall facade section, interrupted by the lit arched entrance.
    for x in (12, 26, 43, 82, 101, 115):
        art.rect("metal_dark", x, 45, 3, 31)
        art.rect("metal_light", x, 49, 1, 21)
    for y in (46, 55, 70):
        art.rect("metal_dark", 12, y, 105, 2)
        art.rect("metal_light", 16, y, 94, 1)
    art.rect("metal", 11, 73, 107, 4)
    art.rect("metal_light", 15, 73, 99, 1)
    # Roof ribs flow from one side to the other with a shared light direction.
    for x_top, x_middle, x_bottom in [(44,25,13),(51,39,29),(60,55,48),
                                       (68,72,78),(76,87,98),(84,102,115)]:
        art.line("metal_dark", x_top, 12, x_middle, 26)
        art.line("metal_dark", x_middle, 26, x_bottom, 45)
        art.line("metal_light", x_top, 13, x_middle+1, 27)
        art.line("metal_light", x_middle+1, 27, x_bottom+1, 45)
    art.rect("metal_dark", 20, 30, 88, 2)
    art.rect("metal", 20, 30, 88, 1)
    art.line("metal_light", 20, 26, 30, 17)
    art.line("metal_light", 30, 17, 42, 10)
    art.rect("metal_light", 43, 8, 42, 2)
    art.rect("shine", 44, 7, 19, 1)
    art.line("metal_light", 86, 9, 99, 17)
    art.line("metal", 99, 17, 110, 28)
    art.rect("metal_dark", 59, 3, 12, 4)
    art.rect("metal_light", 60, 3, 10, 1)
    art.rect("copper", 63, 0, 3, 4)
    art.dot("gold", 64, 0)

    art.layer = 2
    # Copper doorway and its stepped sill are the focal point.
    art.poly("ink", (48, 82), (48, 60), (52, 51), (57, 47), (71, 47),
             (77, 51), (81, 60), (81, 82))
    art.poly("copper", (50, 81), (50, 61), (54, 53), (59, 49), (69, 49),
             (75, 53), (79, 61), (79, 81))
    art.poly("wood_dark", (53, 80), (53, 62), (56, 56), (60, 52), (68, 52),
             (73, 56), (76, 62), (76, 80))
    art.poly("gold", (55, 73), (55, 62), (58, 57), (61, 54), (67, 54),
             (71, 57), (74, 62), (74, 73))
    art.poly("cream", (58, 68), (58, 61), (62, 56), (67, 56), (71, 61), (71, 63))
    art.rect("wood_dark", 64, 54, 1, 23)
    art.rect("wood_dark", 55, 62, 20, 1)
    art.rect("wood", 55, 72, 8, 8)
    art.rect("wood", 66, 72, 8, 8)
    art.line("rust_light", 55, 74, 61, 74)
    art.line("rust_light", 67, 74, 73, 74)
    art.dot("cream", 62, 70)
    art.dot("cream", 66, 70)
    art.rect("sand", 49, 82, 31, 1)
    art.rect("stone", 48, 83, 33, 3)
    art.rect("paver", 46, 86, 37, 2)
    art.rect("stone_light", 44, 88, 41, 2)
    art.rect("stone_dark", 44, 90, 41, 2)
    # Warm wall lamps and selective reflective edges.
    for x in (40, 87):
        art.oval("copper", x-2, 61, 9, 9)
        art.rect("wood_dark", x, 60, 5, 9)
        art.rect("gold", x+1, 61, 3, 6)
        art.rect("cream", x+2, 62, 1, 3)
        art.rect("rust_light", x-1, 60, 7, 1)
        art.rect("metal_dark", x+1, 69, 3, 2)
    for x0, y0, x1, y1 in [(27,24,35,19),(29,26,34,23),(51,22,58,22),
                            (67,20,76,20),(90,37,99,34),(32,51,38,51),
                            (33,53,35,53),(91,51,97,51)]:
        art.line("shine", x0, y0, x1, y1)
    for x in (13,26,43,83,101,115):
        art.dot("sand", x, 72)
    return art.ops


def water(variant):
    art = Drawing()
    art.rect("water", 0, 0, TILE, TILE)
    ripples = [
        [(0,4,6),(12,7,7),(5,22,12),(21,26,9),(23,12,7)],
        [(15,2,10),(3,13,12),(12,24,9),(28,30,4),(0,18,4)],
        [(22,6,10),(7,9,12),(3,26,10),(18,17,7),(23,27,6)],
        [(2,2,8),(19,3,9),(16,14,12),(2,27,14),(8,19,5)],
    ]
    for j, (x, y, span) in enumerate(ripples[variant]):
        art.rect("water_light", x, y, span, 1)
        if j % 2 == 0 and x+span < 32 and y+1 < 32:
            art.rect("water_light", x+2, y+1, span-2, 1)
        if j == 2:
            art.rect("wave", x+2, y, max(2, span//2), 1)
    return art.ops


def shore(mask, variant=0):
    art = Drawing()
    north, east, south, west = [bool(mask & bit) for bit in (1,2,4,8)]

    def land(c, top, right, bottom, left, bevel):
        x0, x1 = left if west else 0, 31-right if east else 31
        y0, y1 = top if north else 0, 31-bottom if south else 31
        nw = bevel if north and west else 0
        ne = bevel if north and east else 0
        se = bevel if south and east else 0
        sw = bevel if south and west else 0
        art.poly(c, (x0+nw,y0),(x1-ne,y0),(x1,y0+ne),(x1,y1-se),
                 (x1-se,y1),(x0+sw,y1),(x0,y1-sw),(x0,y0+nw))

    land("midnight", 1,1,1,1,6)
    land("stone_dark", 2,2,3,2,5)
    land("stone", 3,3,5,3,5)
    land("moss_dark", 4,4,7,4,5)
    land("moss", 5,5,8,5,5)
    land("grass", 6,6,9,6,5)
    if south:
        art.rect("stone_light", 10 if west else 0, 25,
                 12 if west and east else (22 if west or east else 32), 1)
    if north:
        art.rect("blade", 11 if west else 0, 6,
                 10 if west and east else (21 if west or east else 32), 1)
    rng = random.Random(mask * 141 + variant * 311 + 23)
    for i in range(12):
        x, y = rng.randrange(8,24), rng.randrange(9,22)
        art.rect(rng.choice(("moss", "blade", "leaf")), x, y, 2 if i < 3 else 1, 1)
    if variant > 1:
        for x, y in [(7,10),(24,22)]:
            art.line("blade", x, y+3, x-2, y)
            art.line("leaf", x, y+3, x+1, y)
            art.dot("sage", x+2, y+1)
    return art.ops


def paving(variant):
    art = Drawing()
    art.rect("stone_dark", 0, 0, 32, 32)
    for row, (y, height) in enumerate(((0,6),(7,7),(15,7),(23,8))):
        joints = (0, 11, 23, 32) if (row+variant)%2 == 0 else (0, 5, 17, 29, 32)
        for i, (x, end) in enumerate(zip(joints, joints[1:])):
            width = end-x-(end!=32)
            art.rect(("stone", "paver", "stone", "paver")[(i+row+variant)%4], x, y, width, height)
            art.rect("stone_light", x, y, width, 1)
            if width > 6 and (row+i+variant)%3 == 1:
                art.rect("paver", x+2, y+4, 3, 1)
    return art.ops


def bridge(section):
    art = Drawing()
    x0, width = (4, 28) if section == "west" else (0, 28)
    art.rect("midnight", max(0,x0-2), 1, min(32,width+2), 31)
    art.rect("wood_dark", x0, 0, width, 32)
    for y in range(0,32,8):
        art.rect("wood", x0+2 if section=="west" else 0, y, width-2, 6)
        art.rect("copper", x0+2 if section=="west" else 0, y, width-2, 1)
        sx = x0+8 if section=="west" else 12
        art.rect("wood_dark", sx, y+4, 10, 1)
    rail = 4 if section == "west" else 26
    art.rect("metal_dark", rail, 0, 2, 32)
    art.rect("metal_light", rail, 0, 1, 32)
    for y in (0, 17):
        art.rect("wood_dark", rail-2, y, 5, 6)
        art.rect("copper", rail-2, y, 5, 2)
        art.dot("gold", rail-1, y)
    return art.ops


def prop(name):
    art = Drawing(layer=2)
    if name == "lamp":
        art.oval("stone_dark", 9, 24, 16, 5)
        art.rect("paver", 12, 24, 9, 3)
        art.rect("metal_dark", 15, 8, 3, 17)
        art.rect("metal_light", 15, 10, 1, 13)
        art.poly("wood_dark", (10,8),(12,4),(15,2),(18,2),(21,4),(23,8),
                 (21,15),(12,15))
        art.poly("copper", (12,7),(15,4),(19,4),(21,7),(20,13),(13,13))
        art.rect("gold", 13, 7, 7, 5)
        art.rect("cream", 14, 7, 4, 3)
        art.rect("wood_dark", 16, 6, 1, 7)
        art.rect("rust_light", 10, 7, 13, 1)
        art.dot("cream", 12, 7)
    elif name in {"left_planter", "right_planter"}:
        art.oval("moss_dark", 3, 22, 27, 8)
        art.poly("stone_dark", (5,16),(26,16),(25,25),(21,28),(9,28),(6,24))
        art.rect("wood", 7, 18, 18, 7)
        art.rect("copper", 7, 19, 18, 1)
        art.rect("stone_dark", 4, 15, 24, 5)
        art.rect("rust_light", 5, 15, 22, 1)
        for x,y in [(8,10),(12,8),(16,5),(20,8),(24,10)]:
            art.oval("moss_dark", x-3,y,7,10)
            art.oval("leaf", x-2,y,5,6)
            art.line("sage", x,y+4,x-1,y+1)
            if (x <= 16) == (name == "left_planter"):
                art.oval("pink_dark", x-3,y-2,7,6)
                art.oval("pink", x-2,y-2,4,4)
                art.dot("cream",x,y)
    elif name == "reeds":
        art.oval("water_light", 3, 23, 25, 6)
        for x,y,tx in [(10,9,7),(12,7,11),(15,13,18),(18,5,17),(20,11,22),(25,14,26)]:
            art.line("moss_dark", x, 25, tx, y)
            art.line("leaf", x, 25, tx, y+3)
            art.rect("wood", tx, y-3, 2, 5)
            art.rect("rust_light", tx, y-2, 1, 3)
        art.line("wave", 5, 27, 15, 27)
    elif name == "lily":
        for x,y,w,h in [(16,3,12,8),(2,13,15,8),(17,21,11,7)]:
            art.oval("water_light", x-1,y+1,w+2,h+2)
            art.oval("moss", x,y,w,h)
            art.oval("blade", x,y,w,h-2)
            art.line("leaf", x+2,y+2,x+w-3,y+1)
            art.line("water", x+w//2,y+h//2,x+w-2,y+h-1)
        art.oval("pink_dark", 7, 10, 8, 5)
        art.oval("pink", 8, 9, 6, 4)
        art.dot("cream", 11, 10)
    elif name == "wildflowers":
        for x,y in [(6,19),(10,13),(14,19),(18,10),(22,17),(25,21)]:
            art.line("moss_dark", x,y,x+1,y+5)
            art.line("leaf", x+1,y+3,x+3,y+1)
            art.dot("pink_dark", x, y+1)
            art.dot("gold", x, y)
            art.dot("sage", x+2, y+1)
    elif name == "garden_shrub":
        art.oval("moss_dark", 3, 21, 27, 7)
        art.poly("ink", (3,22),(5,15),(9,13),(10,8),(15,6),(19,7),(22,10),
                 (26,11),(29,16),(29,23),(26,25),(9,25))
        for x,y,w,h in [(4,14,15,10),(10,7,13,13),(17,10,11,12),(18,16,11,8)]:
            art.oval("moss", x,y,w,h)
            art.oval("blade", x+1,y+1,w-4,h-4)
        for x,y in [(9,17),(12,12),(16,9),(20,13),(23,17)]:
            art.rect("leaf", x,y,3,1)
        for x,y in [(8,18),(13,13),(22,16),(25,20)]:
            art.dot("pink", x,y)
        art.dot("cream", 13,12)
    elif name == "service_steps":
        art.poly("midnight", (1,1),(30,1),(28,24),(24,28),(7,28),(3,24))
        art.poly("stone_dark", (2,0),(29,0),(27,24),(23,27),(8,27),(4,24))
        for y,x,w,c in [(0,2,28,"stone"),(6,3,26,"paver"),(13,4,24,"stone"),
                         (20,6,20,"stone")]:
            art.rect(c,x,y,w,5)
            art.rect("stone_light",x,y,w,1)
            art.dot("stone_dark",x+w//2,y+3)
        art.rect("moss", 8,25,5,1)
        art.rect("moss", 19,24,6,1)
    elif name == "rowboat":
        art.oval("water_light", 3, 20, 28, 7)
        art.poly("midnight", (1,21),(5,14),(11,10),(24,8),(29,10),(31,12),
                 (28,17),(23,22),(13,25),(5,25))
        art.poly("wood_dark", (2,21),(7,15),(12,12),(23,10),(28,10),(30,12),
                 (26,17),(22,20),(11,24),(5,24))
        art.poly("wood", (5,21),(9,16),(13,14),(24,11),(28,12),(24,16),
                 (19,19),(10,22))
        art.line("rust_light", 5,20,13,14)
        art.line("rust_light", 13,14,24,11)
        art.line("stone_dark", 11,16,15,21)
        art.line("copper", 11,15,15,20)
        art.line("stone_dark", 20,13,23,18)
        art.line("copper", 20,12,23,17)
        art.line("gold", 16,18,7,10)
        art.rect("rust_light", 5,8,4,2)
        art.dot("cream", 25,11)
    elif name == "lamp_reflection":
        art.rect("wave", 6,3,17,1)
        art.rect("foam", 10,7,14,1)
        art.rect("copper", 14,7,7,1)
        art.rect("foam", 11,10,12,1)
        art.rect("rust_light", 14,10,5,1)
        art.rect("wave", 13,15,12,1)
        art.rect("copper", 15,15,4,1)
        art.rect("wave", 14,20,5,1)
    elif name == "glints":
        for x,y,w,c in [(6,6,7,"wave"),(19,12,9,"foam"),(7,17,11,"wave"),
                         (12,21,8,"foam"),(20,26,7,"wave"),(11,28,3,"metal_light")]:
            art.rect(c,x,y,w,1)
    return art.ops


def run(cli, directory, *args, payload=None):
    result = subprocess.run(
        [cli, *args], input=payload, text=True, capture_output=True,
        cwd=directory, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)}\n{result.stderr}\n{result.stdout}")
    return result.stdout


def batch(cli, directory, project, ops):
    return run(cli, directory, "call", "--project", project, payload=json.dumps(ops))


def build_tiles(cli, directory):
    facade = "glasshouse-facade.pxf.json"
    tiles = "tiles.pxf.json"
    run(cli, directory, "new", "--width", "128", "--height", "96", "--output", facade)
    init = [request("renameLayer", index=0, name=LAYERS[0])]
    init.extend(request("addLayer", name=name) for name in LAYERS[1:])
    for index, hex_rgb in enumerate(PALETTE.values(), 1):
        r, g, b = bytes.fromhex(hex_rgb)
        if index <= 8:
            init.append(request("setPaletteColor", index=index, r=r, g=g, b=b))
        else:
            init.append(request("addPaletteColor", r=r, g=g, b=b))
    init.append(request("setPaletteLocked", locked=True))
    batch(cli, directory, facade, init + glaze_building())
    run(cli, directory, "preview", "--project", facade,
        "--scale", "3", "--output", "glasshouse-facade-preview.png")

    shutil.copyfile(directory / facade, directory / tiles)
    split = []
    for tile_index in range(12):
        tile_x, tile_y = tile_index % 4, tile_index // 4
        split.append(request("addFrame"))
        for layer_index in range(len(LAYERS)):
            split.append(request("copyRect", srcX=tile_x*TILE, srcY=tile_y*TILE,
                                 width=TILE, height=TILE, dstX=0, dstY=0, fromFrame=0,
                                 toFrame=tile_index+1, layer=layer_index))
    split.append(request("deleteFrame", index=0))
    batch(cli, directory, tiles, split)
    run(cli, directory, "resize", "--project", tiles, "--width", "32", "--height", "32",
        "--offset-x", "0", "--offset-y", "0")

    art_names = {f"facade_{index:02}": index for index in range(12)}

    def add_tile(name, ops):
        tile_index = len(art_names)
        art_names[name] = tile_index
        batch(cli, directory, tiles, [request("addFrame"),
              request("setActiveFrame", index=tile_index), *ops])

    for index in range(4):
        add_tile(f"water_{index}", water(index))
    for bits in range(16):
        add_tile(f"islet_{bits:02}", shore(bits))
    for index in range(1, 4):
        add_tile(f"grass_{index}", shore(0, index))
    for index in range(3):
        add_tile(f"paving_{index}", paving(index))
    for side in ("west", "east"):
        add_tile(f"bridge_{side}", bridge(side))
    prop_names = ("lamp", "left_planter", "right_planter", "reeds", "lily", "wildflowers",
                  "glints", "garden_shrub", "service_steps", "rowboat", "lamp_reflection")
    for name in prop_names:
        add_tile(name, prop(name))
    run(cli, directory, "frame", "select", "--project", tiles, "--index", "0")
    run(cli, directory, "tileset", "set", "--project", tiles, "--tile-width", str(TILE),
        "--tile-height", str(TILE))
    return art_names


ISLET = [
    ".............",
    "...########..",
    "..##########.",
    ".###########.",
    ".###########.",
    "..##########.",
    "...##..###...",
    ".............",
    ".............",
]


def build_map(cli, directory, art_names):
    layers = ("Canal", "Bank", "Paths", "Conservatory", "Props")
    run(cli, directory, "tilemap", "new", "--width", str(MAP_WIDTH), "--height",
        str(MAP_HEIGHT), "--tile-width", str(TILE), "--tile-height", str(TILE),
        "--tileset", "tiles.pxf.json", "--output", "map.pxf-tilemap.json",
        *(item for name in layers for item in ("--layer", name)))

    def stamp(name, x, y, tile, *, flip_h=False):
        args = ["tilemap", "set", "--map", "map.pxf-tilemap.json", "--name", name,
                "--x", str(x), "--y", str(y), "--tile", str(art_names[tile])]
        if flip_h:
            args.append("--flip-h")
        run(cli, directory, *args)

    def is_ground(x, y):
        return 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and ISLET[y][x] == "#"

    rng = random.Random(6214)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            stamp("Canal", x, y, f"water_{rng.randrange(4)}")
            if not is_ground(x, y):
                continue
            exposed = sum(bit for dx, dy, bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]
                          if not is_ground(x+dx, y+dy))
            grass_variant = rng.randrange(4)
            tile = f"islet_{exposed:02}" if exposed or not grass_variant else f"grass_{grass_variant}"
            stamp("Bank", x, y, tile)

    for y in range(3, 6):
        for x in (5, 6):
            stamp("Paths", x, y, f"paving_{(x+y)%3}")
    for x, y in [(4,4),(7,4),(8,4),(9,4),(9,5)]:
        stamp("Paths", x, y, f"paving_{(x+y)%3}")
    for y in range(6, 9):
        stamp("Paths", 5, y, "bridge_west")
        stamp("Paths", 6, y, "bridge_east")

    for index in range(12):
        stamp("Conservatory", 4 + index%4, 1 + index//4, f"facade_{index:02}")

    for tile, cells in {
        "lamp": [(4,5),(7,5),(4,2),(8,3)],
        "left_planter": [(4,4),(10,3)],
        "right_planter": [(7,4),(8,5),(3,3)],
        "reeds": [(2,6),(10,6),(11,1),(1,2),(4,7),(12,6)],
        "lily": [(12,2),(1,5),(2,8),(9,8),(2,1),(12,8)],
        "wildflowers": [(3,4),(3,5),(10,2),(10,4),(2,3),(8,6),(9,2)],
        "glints": [(7,7),(12,5),(2,7),(1,0)],
        "garden_shrub": [(3,2),(8,2),(9,1),(11,3),(11,4),(4,6)],
        "service_steps": [(9,6)],
        "lamp_reflection": [(8,7),(4,8)],
        "rowboat": [(11,7)],
    }.items():
        for i, (x, y) in enumerate(cells):
            stamp("Props", x, y, tile, flip_h=bool(i % 2 and tile != "lamp"))


def check_tiled_export(directory, tile_count):
    source = json.loads((directory / "map.pxf-tilemap.json").read_text(encoding="utf-8"))
    tiled = json.loads((directory / "tidal-glasshouse.tmj").read_text(encoding="utf-8"))
    metadata = json.loads((directory / "tileset.json").read_text(encoding="utf-8"))
    tileset = tiled["tilesets"][0]

    def gid(cell):
        if cell is None:
            return 0
        if isinstance(cell, int):
            return cell + tileset["firstgid"]
        flags = (0x80000000 if cell["flipH"] else 0) | (0x40000000 if cell["flipV"] else 0)
        return (cell["tile"] + tileset["firstgid"]) | flags

    expected_layers = [
        (layer["name"], [gid(cell) for cell in layer["cells"]])
        for layer in source["layers"]
    ]
    actual_layers = [(layer["name"], layer["data"]) for layer in tiled["layers"]]

    def png_dimensions(filename):
        with (directory / filename).open("rb") as image:
            header = image.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError(f"Invalid PNG header: {filename}")
        return struct.unpack(">II", header[16:24])

    map_size = MAP_WIDTH * TILE, MAP_HEIGHT * TILE
    image_size = metadata["imageWidth"], metadata["imageHeight"]
    checks = {
        "all_layer_cells_match": actual_layers == expected_layers,
        "tile_dimensions_match": (tiled["tilewidth"], tiled["tileheight"]) == (TILE, TILE),
        "tile_count_matches": tileset["tilecount"] == metadata["tileCount"] == tile_count,
        "tileset_image_matches": tileset["image"] == metadata["image"] == "tiles.png",
        "tileset_png_size_matches": png_dimensions("tiles.png") == image_size
            == (tileset["imagewidth"], tileset["imageheight"]),
        "map_png_size_matches": png_dimensions("tidal-glasshouse.png") == map_size,
        "preview_png_size_matches": png_dimensions("tidal-glasshouse-preview.png")
            == tuple(edge * 2 for edge in map_size),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Tiled export verification failed: {checks}")
    return checks


def check_and_export(cli, directory, art_names):
    validate = run(cli, directory, "validate-tiles", "--project", "tiles.pxf.json",
                   "--map", "map.pxf-tilemap.json")
    (directory / "validation.json").write_text(validate, encoding="utf-8")
    run(cli, directory, "export", "tileset", "--project", "tiles.pxf.json",
        "--output", "tiles.png", "--meta", "tileset.json", "--cols", str(COLS),
        "--image", "tiles.png")
    map_args = ["export", "tilemap", "--map", "map.pxf-tilemap.json", "--tileset",
                "tiles.pxf.json", "--cols", str(COLS), "--image", "tiles.png"]
    run(cli, directory, *map_args, "--output", "tidal-glasshouse.png",
        "--tmj", "tidal-glasshouse.tmj")
    run(cli, directory, *map_args, "--scale", "2", "--output", "tidal-glasshouse-preview.png",
        "--tmj", ".preview.tmj")
    (directory / ".preview.tmj").unlink()
    checks = check_tiled_export(directory, len(art_names))
    (directory / "export-checks.json").write_text(json.dumps(checks, indent=2) + "\n",
                                                  encoding="utf-8")
    (directory / "tile-names.json").write_text(json.dumps(art_names, indent=2) + "\n",
                                               encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixelforge", default=os.environ.get("PIXELFORGE_BIN", "pixelforge"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    cli = shutil.which(args.pixelforge)
    if cli is None:
        parser.error(f"Cannot find PixelForge binary: {args.pixelforge}")
    cli = str(Path(cli).resolve())
    directory = args.output.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    print(run(cli, directory, "--version").strip(), flush=True)
    art_names = build_tiles(cli, directory)
    print(f"Drew {len(art_names)} tile slots", flush=True)
    build_map(cli, directory, art_names)
    check_and_export(cli, directory, art_names)
    print(f"Validated and exported {MAP_WIDTH}×{MAP_HEIGHT} map to {directory}")


if __name__ == "__main__":
    main()
