#!/usr/bin/env python3
"""Nearest-neighbor review sheet on the protocol backdrop. Does not call pixelforge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.paths import protocol
from lib.pngutil import write_rgba


def sheet_rgba(document: dict, scale: int, backdrop: list[int]) -> tuple[int, int, bytes]:
    from lib.record import frame_indices

    width = int(document["width"])
    height = int(document["height"])
    indices, palette = frame_indices(document)
    out_w, out_h = width * scale, height * scale
    out = bytearray(out_w * out_h * 4)
    for y in range(height):
        for x in range(width):
            entry = palette[int(indices[y * width + x])]
            if entry["a"] == 0:
                color = [backdrop[0], backdrop[1], backdrop[2], 255]
            else:
                color = [entry["r"], entry["g"], entry["b"], 255]
            for oy in range(scale):
                row = ((y * scale + oy) * out_w + x * scale) * 4
                pixel = bytes(color)
                for ox in range(scale):
                    out[row + ox * 4 : row + (ox + 1) * 4] = pixel
    return out_w, out_h, bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a scale-4 review PNG on #808080")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = protocol()
    document = json.loads(args.project.read_text(encoding="utf-8"))
    width, height, rgba = sheet_rgba(document, int(spec["display_scale"]), spec["review_backdrop_rgb"])
    write_rgba(args.output, width, height, rgba)
    print(f"wrote {args.output} {width}x{height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
