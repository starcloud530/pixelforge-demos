#!/usr/bin/env python3
"""Validate redistribution metadata, content locks, disjointness and proxy status."""

from __future__ import annotations
import argparse
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from generate import HERE, PIN, generate, resolve_bin, read_rgba, future_split


def validate(root, data):
    assert data["dataset_id"] == "pixel-convert-pairs-v0"
    assert data["cli_commit"] == PIN
    frozen = json.loads((HERE.parent / "pixel-convert-v1/manifest.json").read_text())
    forbidden = {f["character_id"] for f in frozen["fixtures"]}
    frozen_hashes = json.loads(
        (HERE.parent / "pixel-convert-v1/fixtures/hashes.json").read_text()
    )
    forbidden_hashes = {f["png_sha256"] for f in frozen_hashes["files"].values()}
    seen = set()
    pairs = failures = 0
    assert len(data["characters"]) == 6
    for char in data["characters"]:
        ident = char["character_id"]
        assert (
            ident not in seen
            and ident not in forbidden
            and ident.startswith("pf-pair-")
        )
        seen.add(ident)
        assert char["license"] == "CC-BY-4.0" and char["attribution"]
        assert char["split"] == "seed-unreviewed" and char["training_eligible"] is False
        assert char["target_status"] == "procedural-proxy-not-artist-corrected"
        assert char["intended_split"] == future_split(ident)
        assert (
            char["source_kind"] == "original-program-art" and char["features_to_keep"]
        )
        assert [im["role"] for im in char["images"]] == [
            "source",
            "target-64",
            "target-128",
        ]
        assert [im["width"] for im in char["images"]] == [256, 64, 128]
        for im in char["images"] + char["failure_samples"]:
            rel = Path(im["file"])
            assert not rel.is_absolute() and ".." not in rel.parts
            path = root / rel
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == im["sha256"] and digest not in forbidden_hashes
            w, h, rgba = read_rgba(path)
            assert w == im["width"] and h == im["height"] == w
            colors = {
                tuple(rgba[i : i + 4]) for i in range(0, len(rgba), 4) if rgba[i + 3]
            }
            assert len(colors) <= 16 and all(c[3] == 255 for c in colors)
        for failure in char["failure_samples"]:
            assert (
                failure["method"] == "center-sample"
                and failure["human_severity"] is None
            )
            size = failure["width"]
            target = next(im for im in char["images"] if im["role"] == f"target-{size}")
            _, _, candidate = read_rgba(root / failure["file"])
            _, _, proxy = read_rgba(root / target["file"])
            x, y = failure["observation"]["pixel"]
            assert (
                candidate[(y * size + x) * 4 + 3]
                == failure["observation"]["candidate_alpha"]
                == 0
            )
            assert (
                proxy[(y * size + x) * 4 + 3]
                == failure["observation"]["proxy_target_alpha"]
                == 255
            )
            failures += 1
        pairs += 2
    assert (pairs, failures) == (12, 2)
    return pairs, failures


def rejection_tests(data):
    for field, value in (
        ("character_id", "pf-cv-001-mass"),
        ("training_eligible", True),
        ("license", "unknown"),
        ("intended_split", "protocol-v1"),
    ):
        bad = copy.deepcopy(data)
        bad["characters"][0][field] = value
        try:
            validate(HERE, bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"accepted bad {field}")
    bad = copy.deepcopy(data)
    bad["characters"][0]["images"][0]["sha256"] = "0" * 64
    try:
        validate(HERE, bad)
    except AssertionError:
        return
    raise AssertionError("accepted corrupted image hash")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-cli", action="store_true")
    args = parser.parse_args()
    data = json.loads((HERE / "manifest.json").read_text())
    counts = validate(HERE, data)
    rejection_tests(data)
    if args.with_cli:
        with tempfile.TemporaryDirectory(prefix="pf-pair-replay-") as temp:
            generate(Path(temp), resolve_bin())
            fresh = json.loads((Path(temp) / "manifest.json").read_text())
            assert fresh == data, "generator, data or CLI output drifted"
            validate(Path(temp), fresh)
    print(
        f"paired seed checks passed: {counts[0]} pairs, {counts[1]} observed failure samples; no training"
    )


if __name__ == "__main__":
    main()
