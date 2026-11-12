"""Build the committed record from row dictionaries."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from .metrics import median_int, round6, wilson
from .paths import fields


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_report(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def frame_indices(document: dict) -> tuple[list[int], list[dict]]:
    palette = document["palette"]
    frame = document["frames"][0]
    if "pixels" in frame:
        indices = [int(v) for v in frame["pixels"]]
    elif frame.get("layers") and len(frame["layers"]) == 1 and "pixels" in frame["layers"][0]:
        indices = [int(v) for v in frame["layers"][0]["pixels"]]
    else:
        raise ValueError("converted frame has no single pixel buffer")
    return indices, palette


def project_index_sha(document: dict) -> tuple[str, list[int], list[dict]]:
    indices, palette = frame_indices(document)
    blob = bytearray()
    blob += int(document["width"]).to_bytes(4, "big")
    blob += int(document["height"]).to_bytes(4, "big")
    for entry in palette:
        blob += bytes((int(entry["r"]), int(entry["g"]), int(entry["b"]), int(entry["a"])))
    blob += b"\xff"
    blob += bytes(indices)
    return sha256_bytes(bytes(blob)), indices, palette


def row_csv_value(row: dict, column: str) -> str:
    value = row[column]
    if column == "categories" or column == "auto_severe_flags":
        return "|".join(value)
    if column in ("lines_json", "holes_json"):
        return value
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def rows_to_csv(rows: list[dict]) -> str:
    columns = fields()["columns"]
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row_csv_value(row, column) for column in columns])
    return buffer.getvalue()


def aggregate_from_rows(rows: list[dict]) -> dict:
    probes_passed = sum(row["feature_probes_passed"] for row in rows)
    probes_total = sum(row["feature_probes_total"] for row in rows)
    severe_rows = sum(1 for row in rows if row["auto_severe"])
    feature_interval = wilson(probes_passed, probes_total)
    severe_interval = wilson(severe_rows, len(rows))
    exact_rows = sum(1 for row in rows if row["psnr_box_exact"])
    scored = [row["psnr_box"] for row in rows if row["psnr_box"] is not None]
    return {
        "benchmark_id": "pixel-convert-v1",
        "method_id": "center-sample",
        "rows": len(rows),
        "timing_runs_each": 3,
        "deterministic_rows": sum(1 for row in rows if row["deterministic"]),
        "palette_within_budget_rows": sum(1 for row in rows if row["palette_within_budget"]),
        "feature_probes_passed": probes_passed,
        "feature_probes_total": probes_total,
        "feature_retention_auto": round6(probes_passed / probes_total),
        "feature_retention_auto_wilson95": list(feature_interval) if feature_interval else None,
        "feature_retention_auto_wilson_note": "binomial interval on probe counts inside this protocol set, not a clustered interval for a future character sample",
        "auto_severe_rows": severe_rows,
        "auto_severe_rate": round6(severe_rows / len(rows)),
        "auto_severe_rate_wilson95": list(severe_interval) if severe_interval else None,
        "auto_severe_rate_note": "share of these protocol rows with an automatic structural flag; not the human severe-defect rate",
        "psnr_box_mean": round6(sum(scored) / len(scored)) if scored else None,
        "psnr_box_exact_rows": exact_rows,
        "psnr_box_mean_note": "mean of rows whose box-filter PSNR is defined; exact rows are excluded",
        "ssim_box_mean": round6(sum(row["ssim_box"] for row in rows) / len(rows)),
        "duration_ms_min": min(row["duration_ms_min"] for row in rows),
        "duration_ms_median_of_row_medians": median_int([row["duration_ms_median"] for row in rows]),
        "duration_ms_max": max(row["duration_ms_max"] for row in rows),
        "blind_win_rate": None,
        "blind_win_rate_status": "pending_human",
        "blind_comparisons": 0,
        "feature_retention_human": None,
        "feature_retention_human_status": "pending_human",
        "severe_defect_rate_human": None,
        "severe_defect_rate_human_status": "pending_human",
        "retouch_minutes_median": None,
        "retouch_minutes_min": None,
        "retouch_minutes_max": None,
        "retouch_minutes_status": "pending_human",
        "cost_usd": None,
        "cost_status": "not_applicable_local_cli",
        "lpips": None,
        "lpips_status": "not_computed",
    }
