"""Deterministic 8-bit RGBA PNG read and write. Standard library only."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_rgba(width: int, height: int, rgba: bytes) -> bytes:
    if len(rgba) != width * height * 4:
        raise ValueError("rgba length does not match width*height*4")
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw += rgba[y * stride : (y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return PNG_SIG + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b"")


def write_rgba(path: Path, width: int, height: int, rgba: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_rgba(width, height, rgba))


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_rgba(data: bytes) -> tuple[int, int, bytes]:
    if not data.startswith(PNG_SIG):
        raise ValueError("not a png")
    pos = 8
    width = height = None
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        tag = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            width, height, bit, color, comp, filt, inter = struct.unpack(">IIBBBBB", chunk)
            if (bit, color, comp, filt, inter) != (8, 6, 0, 0, 0):
                raise ValueError("v1 fixtures must be 8-bit non-interlaced RGBA")
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
    if width is None or height is None:
        raise ValueError("png missing IHDR")
    raw = zlib.decompress(bytes(idat))
    stride = width * 4
    out = bytearray(width * height * 4)
    prev = bytearray(stride)
    src = 0
    for y in range(height):
        filt = raw[src]
        src += 1
        row = bytearray(raw[src : src + stride])
        src += stride
        if filt == 0:
            pass
        elif filt == 1:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                row[x] = (row[x] + left) & 255
        elif filt == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 255
        elif filt == 3:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                row[x] = (row[x] + ((left + prev[x]) // 2)) & 255
        elif filt == 4:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                up = prev[x]
                ul = prev[x - 4] if x >= 4 else 0
                row[x] = (row[x] + _paeth(left, up, ul)) & 255
        else:
            raise ValueError(f"unsupported png filter {filt}")
        out[y * stride : (y + 1) * stride] = row
        prev = row
    return width, height, bytes(out)


def read_rgba(path: Path) -> tuple[int, int, bytes]:
    return decode_rgba(path.read_bytes())
