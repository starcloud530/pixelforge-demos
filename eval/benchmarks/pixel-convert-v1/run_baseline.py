#!/usr/bin/env python3
"""Run a fixed v1 method and write its separate record table.

Projects land in eval/runs/pixel-convert-v1/ (gitignored). The record table
is written under records/v1/<method>/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.baseline import run_target
from lib.cli import CliError, parse_result, resolve_bin, run_cli
from lib.fixtures import load_rgba
from lib.paths import (
    BENCH_DIR,
    FIELDS_PATH,
    HASHES_PATH,
    MANIFEST_PATH,
    PROTOCOL_PATH,
    RECORD_DIR,
    REPO_ROOT,
    manifest,
    protocol,
)
from lib.record import aggregate_from_rows, dumps, rows_to_csv, sha256_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a fixed v1 baseline method")
    parser.add_argument(
        "--method", choices=["center-sample", "traditional"], default="center-sample"
    )
    parser.add_argument(
        "--cli-commit",
        required=True,
        help="pixelforge-ai commit the binary was built from",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=REPO_ROOT / "eval" / "runs" / "pixel-convert-v1",
    )
    parser.add_argument("--record-dir", type=Path, default=None)
    args = parser.parse_args()
    engine_id = {"center-sample": "center-sample", "traditional": "dominant"}[
        args.method
    ]
    if args.cli_commit != "9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d":
        raise SystemExit("this record runner requires the v1 CLI pin")
    args.record_dir = args.record_dir or RECORD_DIR.parent / args.method
    spec = protocol()
    if int(spec["timing_runs"]) != 3:
        raise SystemExit("v1 timing_runs must stay 3")
    binary = resolve_bin()
    code, version_out, version_err, _ = run_cli(binary, ["--version"])
    if code != 0:
        raise SystemExit(version_err.strip() or "pixelforge --version failed")
    cli_version = version_out.strip() or version_err.strip()
    code, engines_out, engines_err, engines_ms = run_cli(binary, ["engine", "list"])
    if code != 0:
        raise SystemExit(engines_err.strip() or "pixelforge engine list failed")
    engines = parse_result(engines_out)
    ids = [item.get("id") for item in engines.get("engines", [])]
    if engine_id not in ids:
        raise SystemExit(f"{engine_id} is not in engine list: {ids}")
    rows = []
    commands = [
        {
            "row_id": "",
            "run": 0,
            "argv": ["pixelforge", "engine", "list"],
            "exit_code": code,
            "duration_ms": engines_ms,
        }
    ]
    for fixture in manifest()["fixtures"]:
        src_w, src_h, rgba = load_rgba(fixture)
        for target in spec["targets"]:
            print(
                f"convert {fixture['id']} {target['width']}x{target['height']}",
                file=sys.stderr,
            )
            row, cell_commands = run_target(
                binary,
                fixture,
                rgba,
                src_w,
                src_h,
                target["width"],
                target["height"],
                args.work_dir,
                spec["timing_runs"],
                method=args.method,
                engine_id=engine_id,
            )
            row["cli_version"] = cli_version
            rows.append(row)
            commands.extend(cell_commands)
    table = {
        "benchmark_id": spec["benchmark_id"],
        "method_id": args.method,
        "canonical": "this JSON table; table.csv is a projection",
        "rows": rows,
    }
    aggregate = aggregate_from_rows(rows)
    meta = {
        "benchmark_id": spec["benchmark_id"],
        "record_version": "v1",
        "method_id": args.method,
        "cli_version": cli_version,
        "cli_commit": args.cli_commit,
        "cli_repo": "https://github.com/starcloud530/pixelforge-ai",
        "engine_id": engine_id,
        "engine_version": rows[0]["engine_version"],
        "engines": ids,
        "palette_strategy": "limit",
        "max_opaque_colors": spec["max_opaque_colors"],
        "display_scale": spec["display_scale"],
        "review_backdrop_rgb": spec["review_backdrop_rgb"],
        "timing_runs": spec["timing_runs"],
        "aestheticApproval": False,
        "human_fields": "pending",
        "projects": "eval/runs/pixel-convert-v1/projects/ (not committed)",
        "protocol_sha256": sha256_bytes(PROTOCOL_PATH.read_bytes()),
        "manifest_sha256": sha256_bytes(MANIFEST_PATH.read_bytes()),
        "fields_sha256": sha256_bytes(FIELDS_PATH.read_bytes()),
        "hashes_sha256": sha256_bytes(HASHES_PATH.read_bytes()),
    }
    if args.method == "traditional":
        meta["cli_binary_sha256"] = sha256_bytes(Path(binary).read_bytes())
        meta["method_spec"] = (
            "TRADITIONAL.md (supplement; frozen protocol.json unchanged)"
        )
    args.record_dir.mkdir(parents=True, exist_ok=True)
    (args.record_dir / "meta.json").write_text(dumps(meta), encoding="utf-8")
    (args.record_dir / "table.json").write_text(dumps(table), encoding="utf-8")
    (args.record_dir / "table.csv").write_text(rows_to_csv(rows), encoding="utf-8")
    (args.record_dir / "aggregate.json").write_text(dumps(aggregate), encoding="utf-8")
    (args.record_dir / "commands.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in commands),
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} rows to {args.record_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CliError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
