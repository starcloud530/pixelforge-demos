"""Render procedural fixtures and check that declared probes sit on real pixels.

Coordinates are source pixels. Pixel (x, y) covers [x, x+1) x [y, y+1).
A pixel center is (x+0.5, y+0.5). Shapes later in the list replace earlier ones.
"""

from __future__ import annotations

import math

from .paths import protocol


def stripe_rgb(index: int) -> list[int]:
    """Frozen 24-stripe formula. Not fitted to a converter."""
    return [40 + (index * 9) % 180, 30 + (index * 13) % 190, 50 + (index * 11) % 170]


def _put(buf: bytearray, width: int, x: int, y: int, rgba: list[int]) -> None:
    i = (y * width + x) * 4
    buf[i : i + 4] = bytes(rgba)


def render_fixture(fixture: dict) -> bytes:
    if fixture["source_kind"] != "procedural":
        raise ValueError(f"{fixture['id']} is not procedural")
    width = fixture["width"]
    height = fixture["height"]
    buf = bytearray(width * height * 4)
    for shape in fixture["scene"]["shapes"]:
        op = shape["op"]
        if op == "rect":
            _paint_rect(buf, width, height, shape)
        elif op == "ellipse":
            _paint_ellipse(buf, width, height, shape)
        elif op == "ring":
            _paint_ring(buf, width, height, shape)
        elif op == "stripes":
            _paint_stripes(buf, width, height, shape)
        else:
            raise ValueError(f"unknown shape {op}")
    return bytes(buf)


def _paint_rect(buf: bytearray, width: int, height: int, shape: dict) -> None:
    x0 = max(0, int(shape["x"]))
    y0 = max(0, int(shape["y"]))
    x1 = min(width, int(shape["x"]) + int(shape["w"]))
    y1 = min(height, int(shape["y"]) + int(shape["h"]))
    color = shape["rgba"]
    for y in range(y0, y1):
        for x in range(x0, x1):
            _put(buf, width, x, y, color)


def _paint_ellipse(buf: bytearray, width: int, height: int, shape: dict) -> None:
    cx, cy = float(shape["cx"]), float(shape["cy"])
    rx, ry = float(shape["rx"]), float(shape["ry"])
    color = shape["rgba"]
    for y in range(height):
        for x in range(width):
            px, py = x + 0.5, y + 0.5
            if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1.0:
                _put(buf, width, x, y, color)


def _paint_ring(buf: bytearray, width: int, height: int, shape: dict) -> None:
    cx, cy = float(shape["cx"]), float(shape["cy"])
    outer = float(shape["outer"])
    inner = float(shape["inner"])
    samples = int(shape["samples"])
    rgb = shape["rgba"][:3]
    n = samples * samples
    for y in range(height):
        for x in range(width):
            hit = 0
            for j in range(samples):
                for i in range(samples):
                    px = x + (i + 0.5) / samples
                    py = y + (j + 0.5) / samples
                    dist = math.hypot(px - cx, py - cy)
                    if inner < dist <= outer:
                        hit += 1
            if hit == 0:
                continue
            alpha = int(round(hit * 255 / n))
            if alpha <= 0:
                continue
            if alpha > 255:
                alpha = 255
            _put(buf, width, x, y, [rgb[0], rgb[1], rgb[2], alpha])


def _paint_stripes(buf: bytearray, width: int, height: int, shape: dict) -> None:
    count = int(shape["count"])
    if int(shape["w"]) % count != 0:
        raise ValueError("stripe width must divide the rectangle")
    colors = [stripe_rgb(i) + [255] for i in range(count)]
    if len({tuple(c) for c in colors}) != count:
        raise ValueError("stripe formula produced duplicate colors")
    stripe_w = int(shape["w"]) // count
    x0, y0 = int(shape["x"]), int(shape["y"])
    for y in range(y0, min(height, y0 + int(shape["h"]))):
        for s in range(count):
            color = colors[s]
            for x in range(x0 + s * stripe_w, x0 + (s + 1) * stripe_w):
                if 0 <= x < width:
                    _put(buf, width, x, y, color)


def pixel(rgba: bytes, width: int, x: int, y: int) -> tuple[int, int, int, int]:
    i = (y * width + x) * 4
    return tuple(rgba[i : i + 4])  # type: ignore[return-value]


def box_bounds(tx: int, ty: int, src_w: int, src_h: int, dst_w: int, dst_h: int) -> tuple[int, int, int, int]:
    return (
        tx * src_w // dst_w,
        (tx + 1) * src_w // dst_w,
        ty * src_h // dst_h,
        (ty + 1) * src_h // dst_h,
    )


def box_alpha_span(rgba: bytes, width: int, x0: int, x1: int, y0: int, y1: int) -> tuple[int, int]:
    lo, hi = 255, 0
    for y in range(y0, y1):
        row = y * width * 4
        for x in range(x0, x1):
            a = rgba[row + x * 4 + 3]
            if a < lo:
                lo = a
            if a > hi:
                hi = a
    return lo, hi


def cell_of(x: float, y: float, src_w: int, src_h: int, dst_w: int, dst_h: int) -> tuple[int, int]:
    if x < 0:
        x = 0.0
    if y < 0:
        y = 0.0
    if x >= src_w:
        x = src_w - 1e-9
    if y >= src_h:
        y = src_h - 1e-9
    tx = min(dst_w - 1, int(x * dst_w / src_w))
    ty = min(dst_h - 1, int(y * dst_h / src_h))
    return tx, ty


def validate_scene(fixture: dict, rgba: bytes) -> list[str]:
    """Fixture invariants. These do not look at a converter result."""
    errors: list[str] = []
    if fixture["source_kind"] != "procedural":
        return errors
    width, height = fixture["width"], fixture["height"]
    scene = fixture["scene"]
    targets = protocol()["targets"]
    opaque = 0
    clear = 0
    for i in range(0, len(rgba), 4):
        if rgba[i + 3] == 0:
            clear += 1
        elif rgba[i + 3] == 255:
            opaque += 1
    if opaque == 0 or clear == 0:
        errors.append(f"{fixture['id']}: need both opaque and transparent source pixels")
    for hole in scene["holes"]:
        hx, hy = int(math.floor(hole["x"])), int(math.floor(hole["y"]))
        if pixel(rgba, width, hx, hy)[3] != 0:
            errors.append(f"{fixture['id']} hole {hole['id']} is not transparent at the source pixel")
        for target in targets:
            tx, ty = cell_of(hole["x"], hole["y"], width, height, target["width"], target["height"])
            x0, x1, y0, y1 = box_bounds(tx, ty, width, height, target["width"], target["height"])
            lo, hi = box_alpha_span(rgba, width, x0, x1, y0, y1)
            if hi != 0:
                errors.append(
                    f"{fixture['id']} hole {hole['id']} box at {target['width']} is not fully transparent"
                )
    for line in scene["lines"]:
        if "reach" not in line:
            errors.append(f"{fixture['id']} line {line['id']} has no reach")
            continue
        for t in (0.0, 0.5, 1.0):
            x = line["x0"] + (line["x1"] - line["x0"]) * t
            y = line["y0"] + (line["y1"] - line["y0"]) * t
            px, py = int(math.floor(x)), int(math.floor(y))
            if not (0 <= px < width and 0 <= py < height) or pixel(rgba, width, px, py)[3] == 0:
                errors.append(f"{fixture['id']} line {line['id']} centerline leaves the ink at t={t}")
                break
    for target in targets:
        solids = empties = 0
        dw, dh = target["width"], target["height"]
        for ty in range(dh):
            for tx in range(dw):
                x0, x1, y0, y1 = box_bounds(tx, ty, width, height, dw, dh)
                lo, hi = box_alpha_span(rgba, width, x0, x1, y0, y1)
                if lo == 255:
                    solids += 1
                if hi == 0:
                    empties += 1
        if solids == 0 or empties == 0:
            errors.append(f"{fixture['id']} has no unambiguous solid/empty cell at {dw}")
    return errors
