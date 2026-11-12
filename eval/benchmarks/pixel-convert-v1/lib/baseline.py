"""One center-sample cell: three converts, then the published measurements."""

from __future__ import annotations

import json
from pathlib import Path

from .cli import CliError, convert_argv, parse_result, portable_argv, run_cli
from .metrics import measure_probes, output_rgb, psnr, reference_rgb, ssim
from .paths import protocol
from .record import canonical_report, project_index_sha, sha256_text


def run_target(
    binary: str,
    fixture: dict,
    rgba: bytes,
    src_w: int,
    src_h: int,
    dst_w: int,
    dst_h: int,
    work: Path,
    runs: int,
) -> tuple[dict, list[dict]]:
    spec = protocol()
    max_colors = int(spec["max_opaque_colors"])
    row_id = f"{fixture['id']}-{dst_w}x{dst_h}-center-sample"
    source = _source_path(fixture)
    durations = []
    hashes = []
    commands = []
    result = None
    project = None
    for run in range(1, runs + 1):
        output = work / "projects" / f"{row_id}-run{run}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()
        code, stdout, stderr, elapsed = run_cli(binary, convert_argv(source, output, dst_w, dst_h, max_colors))
        commands.append({
            "row_id": row_id,
            "run": run,
            "argv": portable_argv(fixture["file"], row_id, dst_w, dst_h, max_colors),
            "exit_code": code,
            "duration_ms": elapsed,
        })
        if code != 0:
            raise CliError(f"{row_id} run {run} exited {code}: {stderr.strip()}")
        durations.append(elapsed)
        document = json.loads(output.read_text(encoding="utf-8"))
        digest, indices, palette = project_index_sha(document)
        hashes.append(digest)
        if run == 1:
            result = parse_result(stdout)
            project = (document, indices, palette, digest)
    if project is None or result is None:
        raise CliError(f"{row_id} produced no project")
    document, indices, palette, digest = project
    if len(set(hashes)) != 1:
        raise CliError(f"{row_id} is not deterministic: {hashes}")
    if document["width"] != dst_w or document["height"] != dst_h:
        raise CliError(f"{row_id} canvas is {document['width']}x{document['height']}")
    if len(indices) != dst_w * dst_h:
        raise CliError(f"{row_id} index count is {len(indices)}")
    report = result.get("paletteReport")
    if not isinstance(report, dict):
        raise CliError(f"{row_id} has no paletteReport")
    engine = result.get("engine") or {}
    if engine.get("id") != "center-sample":
        raise CliError(f"{row_id} engine is {engine.get('id')}")
    bg = spec["review_backdrop_rgb"]
    reference = reference_rgb(rgba, src_w, src_h, dst_w, dst_h, bg)
    rendered = output_rgb(indices, palette, bg)
    image_psnr = psnr(reference, rendered)
    probes = measure_probes(rgba, src_w, src_h, indices, dst_w, dst_h, fixture.get("scene"))
    opaque_colors = sum(1 for entry in palette if entry["a"] >= spec["alpha_transparent_below"])
    for index in indices:
        if index < 0 or index >= len(palette):
            raise CliError(f"{row_id} index {index} is outside the palette")
        if index != 0 and palette[index]["a"] < spec["alpha_transparent_below"]:
            raise CliError(f"{row_id} paints a transparent palette entry")
    palette_colors = int(report["paletteColors"])
    within = opaque_colors <= max_colors and palette_colors <= max_colors
    ordered = sorted(durations)
    row = {
        "row_id": row_id,
        "benchmark_id": spec["benchmark_id"],
        "fixture_id": fixture["id"],
        "character_id": fixture["character_id"],
        "source_kind": fixture["source_kind"],
        "style": fixture["style"],
        "categories": list(fixture["categories"]),
        "split": fixture["split"],
        "target_width": dst_w,
        "target_height": dst_h,
        "max_colors": max_colors,
        "display_scale": spec["display_scale"],
        "method_id": "center-sample",
        "method_hidden_label": None,
        "engine_id": engine.get("id"),
        "engine_version": engine.get("version"),
        "palette_strategy": report.get("strategy"),
        "cli_version": "",
        "exit_code": 0,
        "duration_ms_min": ordered[0],
        "duration_ms_median": ordered[len(ordered) // 2],
        "duration_ms_max": ordered[-1],
        "deterministic": True,
        "index_sha256": digest,
        "palette_report_sha256": sha256_text(canonical_report(report)),
        "opaque_colors": opaque_colors,
        "palette_within_budget": within,
        "index0_transparent": palette[0]["a"] == 0,
        "opaque_pixels": int(report["opaquePixels"]),
        "transparent_pixels": int(report["transparentPixels"]),
        "source_colors": int(report["sourceColors"]),
        "palette_colors": palette_colors,
        "merged_colors": int(report["mergedColors"]),
        "dropped_colors": int(report["droppedColors"]),
        "inexact_pixels": int(report["inexactPixels"]),
        "max_distance": int(report["maxDistance"]),
        "total_distance": int(report["totalDistance"]),
        "solid_empty_matched": probes["solid_empty_matched"],
        "solid_empty_total": probes["solid_empty_total"],
        "solid_empty_rate": probes["solid_empty_rate"],
        "solid_empty_pass": probes["solid_empty_pass"],
        "bleed_cells": probes["bleed_cells"],
        "partial_cells": probes["partial_cells"],
        "lines_json": json.dumps(probes["lines"], ensure_ascii=False, separators=(",", ":")),
        "holes_json": json.dumps(probes["holes"], ensure_ascii=False, separators=(",", ":")),
        "feature_probes_passed": probes["feature_probes_passed"],
        "feature_probes_total": probes["feature_probes_total"],
        "feature_retention_auto": probes["feature_retention_auto"],
        "auto_severe": probes["auto_severe"],
        "auto_severe_flags": probes["auto_severe_flags"],
        "psnr_box": image_psnr,
        "psnr_box_exact": image_psnr is None,
        "ssim_box": ssim(reference, rendered, dst_w, dst_h),
        "lpips": None,
        "lpips_status": "not_computed",
        "blind_preference": None,
        "blind_preference_status": "pending_human",
        "feature_retention_human": None,
        "feature_retention_human_status": "pending_human",
        "severe_defect_human": None,
        "severe_defect_codes_human": None,
        "severe_defect_human_status": "pending_human",
        "retouch_minutes": None,
        "retouch_editor_id": None,
        "retouch_status": "pending_human",
        "cost_usd": None,
        "cost_status": "not_applicable_local_cli",
    }
    return row, commands


def _source_path(fixture: dict):
    from .paths import fixture_path

    return fixture_path(fixture)
