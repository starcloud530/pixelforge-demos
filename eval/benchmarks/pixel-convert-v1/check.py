#!/usr/bin/env python3
"""Check frozen v1 artifacts and both separately recorded classical methods.

Offline checks do not need pixelforge. `--with-cli` re-runs both methods
and compares index hashes and derived metrics to the committed record.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.baseline import run_target
from lib.cli import CliError, resolve_bin
from lib.fixtures import fixture_errors, hash_document, load_rgba, locked_hashes
from lib.metrics import median_int, pairwise_score, wilson
from lib.paths import (
    BENCH_DIR,
    FIELDS_PATH,
    HASHES_PATH,
    MANIFEST_PATH,
    PROTOCOL_PATH,
    RECORD_DIR,
    REPO_ROOT,
    fields,
    fixture_path,
    manifest,
    protocol,
)
from lib.pngutil import decode_rgba, encode_rgba, read_rgba
from lib.record import aggregate_from_rows, rows_to_csv, sha256_bytes
from lib.render import render_fixture, stripe_rgb
from lib.splits import future_split
from review_sheet import sheet_rgba as review_sheet_rgba


def check_text(path: Path, needles: list[str], errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing {path.relative_to(REPO_ROOT)}")
        return
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            errors.append(f"{path.relative_to(REPO_ROOT)} does not mention {needle}")


def check_contract(errors: list[str]) -> None:
    spec = protocol()
    if spec["benchmark_id"] != "pixel-convert-v1":
        errors.append("protocol benchmark_id")
    if spec["baseline_engine"] != "center-sample":
        errors.append("baseline engine")
    if spec["palette_strategy"] != "limit" or spec["max_opaque_colors"] != 16:
        errors.append("palette budget")
    if [item["width"] for item in spec["targets"]] != [64, 128]:
        errors.append("targets")
    if spec["display_scale"] != 4 or spec["review_backdrop_rgb"] != [128, 128, 128]:
        errors.append("display")
    if spec["solid_empty_pass"] != 0.99 or spec["line_hit_pass"] != 0.5:
        errors.append("probe gates")
    if spec["severe_solid_empty_below"] != 0.9 or spec["line_hit_radius_px"] != 1:
        errors.append("severe gates")
    methods = {item["id"]: item["status"] for item in spec["comparison_methods"]}
    if methods.get("center-sample") != "recorded":
        errors.append("center-sample slot")
    for slot in ("traditional", "service", "model"):
        if methods.get(slot) != "not-run":
            errors.append(f"{slot} slot should stay not-run in v1")
    spec_fields = fields()
    columns = spec_fields["columns"]
    for name in spec_fields["must_be_null"] + list(spec_fields["status"]):
        if name not in columns:
            errors.append(f"column missing {name}")
    if future_split("example-character") != "test":
        errors.append("future_split drifted")
    if future_split("example-character") != future_split("example-character"):
        errors.append("future_split unstable")
    if wilson(1, 1) != (round(1 / (1 + 1.959963984540054**2), 6), 1.0):
        errors.append(f"wilson(1,1) = {wilson(1, 1)}")
    if wilson(0, 1)[0] != 0.0:
        errors.append("wilson(0,1) lower bound")
    if wilson(0, 0) is not None:
        errors.append("wilson empty")
    if pairwise_score(1, 1, 4) != 0.375 or pairwise_score(0, 0, 0) is not None:
        errors.append("pairwise score")
    if median_int([3, 1, 2]) != 2:
        errors.append("median")
    colors = [tuple(stripe_rgb(i)) for i in range(24)]
    if len(set(colors)) != 24:
        errors.append("stripe colors collide")
    sample = bytes([10, 20, 30, 255, 0, 0, 0, 0])
    encoded = encode_rgba(2, 1, sample)
    if decode_rgba(encoded) != (2, 1, sample):
        errors.append("png roundtrip")
    project = {
        "width": 1,
        "height": 1,
        "palette": [
            {"r": 0, "g": 0, "b": 0, "a": 0},
            {"r": 1, "g": 2, "b": 3, "a": 255},
        ],
        "frames": [{"layers": [{"pixels": [1]}]}],
    }
    sw, sh, sheet = review_sheet_rgba(project, 4, [128, 128, 128])
    if (sw, sh) != (4, 4) or sheet[:4] != bytes([1, 2, 3, 255]):
        errors.append("review sheet")
    for name in ("PROTOCOL.md", "METRICS.md", "DATASET.md", "README.md"):
        if not (BENCH_DIR / name).is_file():
            errors.append(f"missing {name}")
    check_text(
        BENCH_DIR / "PROTOCOL.md",
        ["盲评", "平局", "精修", "center-sample", "traditional", "64", "128", "16"],
        errors,
    )
    check_text(
        BENCH_DIR / "METRICS.md",
        [
            "PSNR",
            "SSIM",
            "LPIPS",
            "Wilson",
            "pending_human",
            "S1",
            "S2",
            "S3",
            "S4",
            "S5",
            "0.99",
            "0.5",
        ],
        errors,
    )
    check_text(
        BENCH_DIR / "DATASET.md",
        ["100", "200", "protocol-v1", "character_id", "泄漏"],
        errors,
    )
    check_text(
        BENCH_DIR / "README.md",
        ["PIXELFORGE_BIN", "check.py", "run_baseline.py"],
        errors,
    )
    for name in (
        "blind-ballot.json",
        "blind-seal.json",
        "retouch-log.json",
        "fields.json",
    ):
        if not (BENCH_DIR / "templates" / name).is_file():
            errors.append(f"missing template {name}")
    ballot = json.loads(
        (BENCH_DIR / "templates" / "blind-ballot.json").read_text(encoding="utf-8")
    )
    if ballot["preference"] is not None or "tie" not in ballot["preference_values"]:
        errors.append("ballot template")
    retouch = json.loads(
        (BENCH_DIR / "templates" / "retouch-log.json").read_text(encoding="utf-8")
    )
    if retouch["minutes"] is not None:
        errors.append("retouch template minutes")


def check_fixtures(errors: list[str]) -> None:
    errors.extend(fixture_errors())
    if not HASHES_PATH.is_file():
        errors.append("missing fixtures/hashes.json")
        return
    locked = locked_hashes()
    fresh = hash_document()
    if fresh != locked:
        errors.append("fixtures/hashes.json does not match the manifest and renderer")
    for fixture in manifest()["fixtures"]:
        info = locked["files"][fixture["id"]]
        blob = fixture_path(fixture).read_bytes()
        if sha256_bytes(blob) != info["png_sha256"]:
            errors.append(f"{fixture['id']} png bytes drifted")
        width, height, rgba = read_rgba(fixture_path(fixture))
        if sha256_bytes(rgba) != info["rgba_sha256"] or (width, height) != (
            info["width"],
            info["height"],
        ):
            errors.append(f"{fixture['id']} rgba drifted")
        if fixture["source_kind"] == "procedural" and render_fixture(fixture) != rgba:
            errors.append(f"{fixture['id']} renderer does not match the committed png")
        if (
            fixture["source_kind"] == "procedural"
            and sha256_bytes(encode_rgba(width, height, rgba)) != info["png_sha256"]
        ):
            errors.append(f"{fixture['id']} encoder does not match the committed png")


def _loads(text: str, label: str, errors: list[str]):
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not JSON: {exc}")
        return None


def check_record(errors: list[str], method: str = "center-sample") -> dict | None:
    record_dir = RECORD_DIR.parent / method
    engine_id = {"center-sample": "center-sample", "traditional": "dominant"}[method]
    table_path = record_dir / "table.json"
    if not table_path.is_file():
        errors.append(f"missing records/v1/{method}/table.json")
        return None
    table = _loads(table_path.read_text(encoding="utf-8"), "table.json", errors)
    meta = _loads(
        (record_dir / "meta.json").read_text(encoding="utf-8"), "meta.json", errors
    )
    aggregate = _loads(
        (record_dir / "aggregate.json").read_text(encoding="utf-8"),
        "aggregate.json",
        errors,
    )
    if not table or not meta or not aggregate:
        return None
    for path, key in (
        (PROTOCOL_PATH, "protocol_sha256"),
        (MANIFEST_PATH, "manifest_sha256"),
        (FIELDS_PATH, "fields_sha256"),
        (HASHES_PATH, "hashes_sha256"),
    ):
        if meta.get(key) != sha256_bytes(path.read_bytes()):
            errors.append(f"meta {key} does not match the current file")
    if (
        meta.get("aestheticApproval") is not False
        or meta.get("human_fields") != "pending"
    ):
        errors.append("meta human/aesthetic flags")
    if meta.get("cli_commit") != "9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d":
        errors.append(
            "v1 record is pinned to pixelforge-ai 9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d"
        )
    rows = table["rows"]
    expected_ids = []
    for fixture in manifest()["fixtures"]:
        for target in protocol()["targets"]:
            expected_ids.append(
                f"{fixture['id']}-{target['width']}x{target['height']}-{method}"
            )
    if [row["row_id"] for row in rows] != expected_ids:
        errors.append(f"record rows are not fixture × 64/128 × {method}")
    if meta.get("method_id") != method or meta.get("engine_id") != engine_id:
        errors.append(f"{method} meta method/engine")
    if table.get("method_id") != method:
        errors.append(f"{method} table method")
    spec_fields = fields()
    csv_text = (record_dir / "table.csv").read_text(encoding="utf-8")
    if csv_text != rows_to_csv(rows):
        errors.append("table.csv is not the projection of table.json")
    if aggregate != aggregate_from_rows(rows):
        errors.append("aggregate.json does not match the rows")
    for row in rows:
        if list(row) != spec_fields["columns"]:
            errors.append(f"{row['row_id']} keys differ from templates/fields.json")
            break
        for name in spec_fields["must_be_null"]:
            if row[name] is not None:
                errors.append(f"{row['row_id']} {name} is filled; v1 leaves it empty")
        for name, value in spec_fields["status"].items():
            if row[name] != value:
                errors.append(f"{row['row_id']} {name} is {row[name]!r}")
        if row["method_id"] != method or row["palette_strategy"] != "limit":
            errors.append(f"{row['row_id']} method")
        if row["engine_id"] != engine_id:
            errors.append(f"{row['row_id']} engine")
        if row["exit_code"] != 0 or row["deterministic"] is not True:
            errors.append(f"{row['row_id']} did not complete a deterministic convert")
        if row["max_colors"] != 16 or row["display_scale"] != 4:
            errors.append(f"{row['row_id']} budget or scale")
        if "S4" in row["auto_severe_flags"]:
            errors.append(f"{row['row_id']} auto flag S4 is human-only")
        within = row["opaque_colors"] <= 16 and row["palette_colors"] <= 16
        if row["palette_within_budget"] is not within:
            errors.append(
                f"{row['row_id']} palette_within_budget disagrees with the counts"
            )
        lines = json.loads(row["lines_json"])
        holes = json.loads(row["holes_json"])
        flags = set(row["auto_severe_flags"])
        if ("S2" in flags) != any(item["rate"] == 0 for item in lines):
            errors.append(f"{row['row_id']} S2")
        if ("S5" in flags) != any(not item["pass"] for item in holes):
            errors.append(f"{row['row_id']} S5")
        if ("S3" in flags) != (row["bleed_cells"] > 0):
            errors.append(f"{row['row_id']} S3")
        if ("S1" in flags) != (row["solid_empty_rate"] < 0.9):
            errors.append(f"{row['row_id']} S1")
        if row["auto_severe"] is not bool(flags):
            errors.append(f"{row['row_id']} auto_severe")
        passed = (
            int(row["solid_empty_pass"])
            + sum(item["pass"] for item in holes)
            + sum(item["pass"] for item in lines)
        )
        total = 1 + len(holes) + len(lines)
        if (
            passed != row["feature_probes_passed"]
            or total != row["feature_probes_total"]
        ):
            errors.append(f"{row['row_id']} probe counts")
        if total and row["feature_retention_auto"] != round(passed / total, 6):
            errors.append(f"{row['row_id']} feature_retention_auto")
        if row["solid_empty_total"] and row["solid_empty_rate"] != round(
            row["solid_empty_matched"] / row["solid_empty_total"], 6
        ):
            errors.append(f"{row['row_id']} solid_empty_rate")
        if row["psnr_box_exact"] is not (row["psnr_box"] is None):
            errors.append(f"{row['row_id']} psnr exact flag")
        if row["ssim_box"] is None:
            errors.append(f"{row['row_id']} missing ssim")
    commands = [
        json.loads(line)
        for line in (record_dir / "commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    converts = [
        item for item in commands if item["argv"][:2] == ["pixelforge", "convert"]
    ]
    if len(converts) != len(rows) * 3:
        errors.append("commands.jsonl should have 3 converts per row")
    listed = [
        item for item in commands if item["argv"] == ["pixelforge", "engine", "list"]
    ]
    if len(listed) != 1 or listed[0]["exit_code"] != 0:
        errors.append("commands.jsonl engine list")
    allowed = {"pixelforge"}
    for item in commands:
        if item["argv"][0] not in allowed:
            errors.append("unexpected binary in commands.jsonl")
        if item["argv"][1] not in {"convert", "engine"}:
            errors.append(f"unexpected subcommand {item['argv'][1]}")
    from lib.cli import portable_argv

    fixture_by_id = {fixture["id"]: fixture for fixture in manifest()["fixtures"]}
    for row in rows:
        cell = [item for item in converts if item["row_id"] == row["row_id"]]
        expected = portable_argv(
            fixture_by_id[row["fixture_id"]]["file"],
            row["row_id"],
            row["target_width"],
            row["target_height"],
            16,
            engine_id,
        )
        if (
            len(cell) != 3
            or [item["run"] for item in cell] != [1, 2, 3]
            or any(item["argv"] != expected or item["exit_code"] != 0 for item in cell)
        ):
            errors.append(f"{row['row_id']} command drift")
    return {"rows": rows, "meta": meta}


def check_cli(
    rows: list[dict], errors: list[str], method: str = "center-sample"
) -> None:
    try:
        binary = resolve_bin()
    except CliError as exc:
        errors.append(str(exc))
        return
    engine_id = {"center-sample": "center-sample", "traditional": "dominant"}[method]
    by_id = {row["row_id"]: row for row in rows}
    spec = protocol()
    with tempfile.TemporaryDirectory(prefix="pixel-convert-v1-") as temp:
        work = Path(temp)
        for fixture in manifest()["fixtures"]:
            src_w, src_h, rgba = load_rgba(fixture)
            for target in spec["targets"]:
                row_id = (
                    f"{fixture['id']}-{target['width']}x{target['height']}-{method}"
                )
                try:
                    fresh, _commands = run_target(
                        binary,
                        fixture,
                        rgba,
                        src_w,
                        src_h,
                        target["width"],
                        target["height"],
                        work,
                        spec["timing_runs"],
                        method=method,
                        engine_id=engine_id,
                    )
                except CliError as exc:
                    errors.append(str(exc))
                    continue
                saved = by_id[row_id]
                for key in (
                    "index_sha256",
                    "palette_report_sha256",
                    "engine_id",
                    "engine_version",
                    "palette_strategy",
                    "opaque_colors",
                    "palette_colors",
                    "feature_probes_passed",
                    "feature_probes_total",
                    "feature_retention_auto",
                    "auto_severe_flags",
                    "psnr_box",
                    "psnr_box_exact",
                    "ssim_box",
                    "solid_empty_matched",
                    "bleed_cells",
                ):
                    if fresh[key] != saved[key]:
                        errors.append(
                            f"{row_id} {key} reproduced {fresh[key]!r}, record has {saved[key]!r}"
                        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the pixel-convert v1 benchmark")
    parser.add_argument(
        "--with-cli",
        action="store_true",
        help="re-run both fixed methods and compare hashes",
    )
    args = parser.parse_args()
    if not (REPO_ROOT / "README.md").is_file():
        print("repo root was not found from the benchmark path", file=sys.stderr)
        return 1
    errors: list[str] = []
    check_contract(errors)
    check_fixtures(errors)
    for method in ("center-sample", "traditional"):
        record = check_record(errors, method)
        if args.with_cli and record:
            check_cli(record["rows"], errors, method)
    if errors:
        print(f"{len(errors)} check(s) failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    mode = "offline + cli" if args.with_cli else "offline"
    print(f"pixel-convert-v1 checks passed ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
