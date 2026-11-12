"""Method-agnostic measurements. Gates are the published protocol constants."""

from __future__ import annotations

import math

from .paths import protocol
from .render import box_alpha_span, box_bounds, cell_of


def round6(value: float) -> float:
    return round(float(value), 6)


def wilson(successes: int, trials: int, z: float | None = None) -> tuple[float, float] | None:
    if trials <= 0:
        return None
    if z is None:
        z = float(protocol()["wilson_z"])
    p = successes / trials
    z2 = z * z
    denom = 1.0 + z2 / trials
    center = (p + z2 / (2.0 * trials)) / denom
    margin = z * math.sqrt(p * (1.0 - p) / trials + z2 / (4.0 * trials * trials)) / denom
    return round6(max(0.0, center - margin)), round6(min(1.0, center + margin))


def pairwise_score(wins: int, ties: int, comparisons: int) -> float | None:
    if comparisons <= 0:
        return None
    return round6((wins + 0.5 * ties) / comparisons)


def median_int(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _composite(r: int, g: int, b: int, a: int, bg: list[int]) -> tuple[float, float, float]:
    t = a / 255.0
    return (
        r * t + bg[0] * (1.0 - t),
        g * t + bg[1] * (1.0 - t),
        b * t + bg[2] * (1.0 - t),
    )


def _box_display(
    rgba: bytes, width: int, x0: int, x1: int, y0: int, y1: int, bg: list[int]
) -> tuple[float, float, float]:
    acc = [0.0, 0.0, 0.0]
    n = 0
    for y in range(y0, y1):
        row = y * width * 4
        for x in range(x0, x1):
            i = row + x * 4
            pixel = _composite(rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3], bg)
            acc[0] += pixel[0]
            acc[1] += pixel[1]
            acc[2] += pixel[2]
            n += 1
    return acc[0] / n, acc[1] / n, acc[2] / n


def reference_rgb(rgba: bytes, src_w: int, src_h: int, dst_w: int, dst_h: int, bg: list[int]) -> list[tuple[float, float, float]]:
    out = []
    for ty in range(dst_h):
        for tx in range(dst_w):
            x0, x1, y0, y1 = box_bounds(tx, ty, src_w, src_h, dst_w, dst_h)
            out.append(_box_display(rgba, src_w, x0, x1, y0, y1, bg))
    return out


def output_rgb(indices: list[int], palette: list[dict], bg: list[int]) -> list[tuple[float, float, float]]:
    colors = []
    for index in indices:
        entry = palette[index]
        colors.append(_composite(entry["r"], entry["g"], entry["b"], entry["a"], bg))
    return colors


def psnr(reference: list[tuple[float, float, float]], candidate: list[tuple[float, float, float]]) -> float | None:
    if len(reference) != len(candidate) or not reference:
        return None
    err = 0.0
    for a, b in zip(reference, candidate):
        err += (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
    mse = err / (len(reference) * 3)
    if mse == 0:
        return None
    return round6(10.0 * math.log10((255.0 * 255.0) / mse))


def _gaussian_1d(size: int, sigma: float) -> list[float]:
    radius = size // 2
    raw = [math.exp(-(i * i) / (2.0 * sigma * sigma)) for i in range(-radius, radius + 1)]
    total = sum(raw)
    return [v / total for v in raw]


def _blur_channel(values: list[float], width: int, height: int, kernel: list[float]) -> list[float]:
    radius = len(kernel) // 2
    tmp = [0.0] * (width * height)
    for y in range(height):
        row = y * width
        for x in range(radius, width - radius):
            acc = 0.0
            for k, weight in enumerate(kernel):
                acc += values[row + x + k - radius] * weight
            tmp[row + x] = acc
    out = [0.0] * (width * height)
    for y in range(radius, height - radius):
        for x in range(radius, width - radius):
            acc = 0.0
            for k, weight in enumerate(kernel):
                acc += tmp[(y + k - radius) * width + x] * weight
            out[y * width + x] = acc
    return out


def ssim(reference: list[tuple[float, float, float]], candidate: list[tuple[float, float, float]], width: int, height: int) -> float | None:
    spec = protocol()
    window = int(spec["ssim_window"])
    if width < window or height < window or len(reference) != width * height:
        return None
    kernel = _gaussian_1d(window, float(spec["ssim_sigma"]))
    k1 = float(spec["ssim_k1"])
    k2 = float(spec["ssim_k2"])
    c1 = (k1 * 255.0) ** 2
    c2 = (k2 * 255.0) ** 2
    radius = window // 2
    scores = []
    for channel in range(3):
        left = [pixel[channel] for pixel in reference]
        right = [pixel[channel] for pixel in candidate]
        mu_l = _blur_channel(left, width, height, kernel)
        mu_r = _blur_channel(right, width, height, kernel)
        mu_l2 = _blur_channel([v * v for v in left], width, height, kernel)
        mu_r2 = _blur_channel([v * v for v in right], width, height, kernel)
        mu_lr = _blur_channel([a * b for a, b in zip(left, right)], width, height, kernel)
        acc = 0.0
        count = 0
        for y in range(radius, height - radius):
            row = y * width
            for x in range(radius, width - radius):
                i = row + x
                var_l = mu_l2[i] - mu_l[i] * mu_l[i]
                var_r = mu_r2[i] - mu_r[i] * mu_r[i]
                cov = mu_lr[i] - mu_l[i] * mu_r[i]
                num = (2.0 * mu_l[i] * mu_r[i] + c1) * (2.0 * cov + c2)
                den = (mu_l[i] * mu_l[i] + mu_r[i] * mu_r[i] + c1) * (var_l + var_r + c2)
                acc += num / den
                count += 1
        scores.append(acc / count)
    return round6(sum(scores) / 3.0)


def _dist_to_segment(px: float, py: float, x0: float, y0: float, x1: float, y1: float) -> float:
    dx, dy = x1 - x0, y1 - y0
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / length_sq))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _cell_on_stroke(
    rgba: bytes,
    src_w: int,
    src_h: int,
    dst_w: int,
    dst_h: int,
    tx: int,
    ty: int,
    line: dict,
) -> bool:
    if tx < 0 or ty < 0 or tx >= dst_w or ty >= dst_h:
        return False
    reach = float(line["reach"])
    x0, x1, y0, y1 = box_bounds(tx, ty, src_w, src_h, dst_w, dst_h)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if rgba[(y * src_w + x) * 4 + 3] == 0:
                continue
            if _dist_to_segment(x + 0.5, y + 0.5, line["x0"], line["y0"], line["x1"], line["y1"]) <= reach:
                return True
    return False


def _line_samples(line: dict, src_w: int, dst_w: int) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = line["x0"], line["y0"], line["x1"], line["y1"]
    length = math.hypot(x1 - x0, y1 - y0)
    step = (src_w / dst_w) / 2.0
    n = max(1, int(round(length / step)))
    return [
        (x0 + (x1 - x0) * (i / n), y0 + (y1 - y0) * (i / n))
        for i in range(n + 1)
    ]


def measure_probes(
    rgba: bytes,
    src_w: int,
    src_h: int,
    indices: list[int],
    dst_w: int,
    dst_h: int,
    scene: dict | None,
) -> dict:
    spec = protocol()
    radius = int(spec["line_hit_radius_px"])
    solid_pass = float(spec["solid_empty_pass"])
    severe_below = float(spec["severe_solid_empty_below"])
    line_pass = float(spec["line_hit_pass"])
    opaque = [index != 0 for index in indices]

    def is_opaque(tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= dst_w or ty >= dst_h:
            return False
        return opaque[ty * dst_w + tx]

    matched = 0
    total = 0
    bleed = 0
    partial = 0
    for ty in range(dst_h):
        for tx in range(dst_w):
            x0, x1, y0, y1 = box_bounds(tx, ty, src_w, src_h, dst_w, dst_h)
            lo, hi = box_alpha_span(rgba, src_w, x0, x1, y0, y1)
            if lo == 255:
                total += 1
                if is_opaque(tx, ty):
                    matched += 1
            elif hi == 0:
                total += 1
                if not is_opaque(tx, ty):
                    matched += 1
                else:
                    bleed += 1
            else:
                partial += 1
    rate = matched / total
    holes = []
    lines = []
    if scene:
        for hole in scene["holes"]:
            tx, ty = cell_of(hole["x"], hole["y"], src_w, src_h, dst_w, dst_h)
            holes.append({
                "id": hole["id"],
                "transparent": not is_opaque(tx, ty),
                "pass": not is_opaque(tx, ty),
            })
        for line in scene["lines"]:
            samples = _line_samples(line, src_w, dst_w)
            hits = 0
            for x, y in samples:
                tx, ty = cell_of(x, y, src_w, src_h, dst_w, dst_h)
                found = False
                for oy in range(-radius, radius + 1):
                    for ox in range(-radius, radius + 1):
                        nx, ny = tx + ox, ty + oy
                        if not _cell_on_stroke(rgba, src_w, src_h, dst_w, dst_h, nx, ny, line):
                            continue
                        if is_opaque(nx, ny):
                            found = True
                            break
                    if found:
                        break
                if found:
                    hits += 1
            hit_rate = hits / len(samples)
            lines.append({
                "id": line["id"],
                "hits": hits,
                "samples": len(samples),
                "rate": round6(hit_rate),
                "pass": hit_rate >= line_pass,
            })
    passed = int(rate >= solid_pass) + sum(1 for hole in holes if hole["pass"]) + sum(1 for line in lines if line["pass"])
    probe_total = 1 + len(holes) + len(lines)
    flags = []
    if rate < severe_below:
        flags.append("S1")
    if any(line["rate"] == 0 for line in lines):
        flags.append("S2")
    if bleed > 0:
        flags.append("S3")
    if any(not hole["pass"] for hole in holes):
        flags.append("S5")
    return {
        "solid_empty_matched": matched,
        "solid_empty_total": total,
        "solid_empty_rate": round6(rate),
        "solid_empty_pass": rate >= solid_pass,
        "bleed_cells": bleed,
        "partial_cells": partial,
        "lines": lines,
        "holes": holes,
        "feature_probes_passed": passed,
        "feature_probes_total": probe_total,
        "feature_retention_auto": round6(passed / probe_total),
        "auto_severe": bool(flags),
        "auto_severe_flags": flags,
    }
