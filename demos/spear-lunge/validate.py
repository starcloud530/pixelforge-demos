#!/usr/bin/env python3
"""Re-check the baked lunge with the PixelForge CLI.

Static checks only: solves, samples, layer pixels, atlas, and hashes.
Playback timing is not decided here. Thresholds are pixel or degree gaps,
not a naturalness score.

    PIXELFORGE=/path/to/pixelforge python3 demos/spear-lunge/validate.py
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE_SHA = "b647dc1631e639b34279e6027825430b0a3ce1b2"
FRAMES = 16
WIDTH = 128

LAYERS = [
    "ground",
    "ribbon-tip",
    "ribbon-mid",
    "ribbon-root",
    "thigh-far",
    "shin-far",
    "upper-far",
    "fore-far",
    "hand-far",
    "pelvis",
    "torso",
    "thigh-near",
    "shin-near",
    "spear",
    "tassel-root",
    "tassel-tip",
    "flame",
    "upper-near",
    "fore-near",
    "hand-near",
    "head",
]


def fail(message: str) -> None:
    raise SystemExit(message)


def run_batch(binary: str, project: Path, requests: list[dict]) -> list[dict]:
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    try:
        for request in requests:
            handle.write(json.dumps(request) + "\n")
        handle.close()
        proc = subprocess.run(
            [binary, "call", "--project", str(project), "--request-file", handle.name],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        os.unlink(handle.name)
    results = []
    for line in proc.stdout.splitlines():
        if not line.startswith("{"):
            continue
        body = json.loads(line)
        if body.get("ok") is not True:
            fail(json.dumps(body, ensure_ascii=False))
        results.append(body["result"])
    if proc.returncode != 0 or len(results) != len(requests):
        fail(f"batch exit {proc.returncode} {len(results)}/{len(requests)}\n{proc.stderr[-1000:]}")
    return results


def anchor(part: dict, name: str) -> dict:
    for item in part["anchors"]:
        if item["name"] == name:
            return item
    fail(f"missing {part['name']}.{name}")
    raise AssertionError


def main() -> None:
    binary = os.environ.get("PIXELFORGE") or ""
    if not binary:
        fail("set PIXELFORGE")
    root = Path(__file__).resolve().parent
    project = root / "final" / "spear-lunge.pxf.json"
    if not project.exists():
        fail("missing baked project; run build.py")
    skill = subprocess.run(
        [binary, "skills", "read", "pixel-art-craft", "references/action-motion.md"],
        check=False,
        capture_output=True,
        text=True,
    )
    if skill.returncode != 0 or "跨步刺击" not in skill.stdout:
        fail("PIXELFORGE is not the pinned action-motion CLI")
    version = subprocess.run([binary, "--version"], check=False, capture_output=True, text=True).stdout.strip()

    solves = run_batch(
        binary,
        project,
        [{"tool": "solveConstraints", "params": {"frame": frame}} for frame in range(FRAMES)],
    )
    samples = run_batch(
        binary,
        project,
        [
            {"tool": "sampleCurve", "params": {"part": part, "channel": channel, "frame": frame}}
            for part, channel in (
                ("pelvis", "translateX"),
                ("pelvis", "translateY"),
                ("torso", "rotation"),
                ("spear", "rotation"),
                ("tassel-tip", "rotation"),
                ("tassel-root", "rotation"),
                ("ribbon-tip", "rotation"),
                ("ribbon-root", "rotation"),
            )
            for frame in range(FRAMES)
        ],
    )
    grouped = {}
    index = 0
    for part, channel in (
        ("pelvis", "translateX"),
        ("pelvis", "translateY"),
        ("torso", "rotation"),
        ("spear", "rotation"),
        ("tassel-tip", "rotation"),
        ("tassel-root", "rotation"),
        ("ribbon-tip", "rotation"),
        ("ribbon-root", "rotation"),
    ):
        grouped[f"{part}.{channel}"] = [float(item["value"]) for item in samples[index : index + FRAMES]]
        index += FRAMES

    rows = []
    grip_errors = []
    cloth_errors = []
    for frame, report in enumerate(solves):
        parts = {part["name"]: part for part in report["parts"]}
        front = anchor(parts["shin-near"], "sole")
        rear = anchor(parts["shin-far"], "sole")
        hand_near = anchor(parts["hand-near"], "palm")
        hand_far = anchor(parts["hand-far"], "palm")
        grip_fore = anchor(parts["spear"], "grip-fore")
        grip_rear = anchor(parts["spear"], "grip-rear")
        ribbon = anchor(parts["ribbon-root"], "root")
        hip_ribbon = anchor(parts["pelvis"], "ribbon")
        tassel = anchor(parts["tassel-root"], "root")
        spear_tassel = anchor(parts["spear"], "tassel")
        constraints = {item["name"]: item for item in report["constraints"]}
        near_grip = (hand_near["canvasX"], hand_near["canvasY"]) == (grip_fore["canvasX"], grip_fore["canvasY"])
        far_grip = (hand_far["canvasX"], hand_far["canvasY"]) == (grip_rear["canvasX"], grip_rear["canvasY"])
        ribbon_held = (ribbon["canvasX"], ribbon["canvasY"]) == (hip_ribbon["canvasX"], hip_ribbon["canvasY"])
        tassel_held = (tassel["canvasX"], tassel["canvasY"]) == (spear_tassel["canvasX"], spear_tassel["canvasY"])
        if not near_grip or not far_grip:
            grip_errors.append(frame)
        if not ribbon_held or not tassel_held:
            cloth_errors.append(frame)
        rows.append(
            {
                "frame": frame,
                "frontSole": [front["canvasX"], front["canvasY"]],
                "rearSole": [rear["canvasX"], rear["canvasY"]],
                "frontLocal": [front["x"], front["y"]],
                "gripForeCanvas": [grip_fore["canvasX"], grip_fore["canvasY"]],
                "gripForeLocal": [grip_fore["x"], grip_fore["y"]],
                "restGripForeLocal": [14, -7],
                "legNearPlantedFlag": constraints["leg-near"]["planted"],
                "legFarPlantedFlag": constraints["leg-far"]["planted"],
                "nearGrip": near_grip,
                "farGrip": far_grip,
                "ribbonHeld": ribbon_held,
                "tasselHeld": tassel_held,
            }
        )

    if grip_errors:
        fail(f"grip detached on frames {grip_errors}")
    if cloth_errors:
        fail(f"cloth root detached on frames {cloth_errors}")

    for row in rows:
        if row["rearSole"] != [30, 116]:
            fail(f"rear sole moved on frame {row['frame']}: {row['rearSole']}")
    for frame in (0, 1, 2, 3):
        if rows[frame]["frontSole"] != [56, 116]:
            fail(f"front sole slid during charge frame {frame}")
    for frame in range(7, 16):
        if rows[frame]["frontSole"] != [74, 116]:
            fail(f"front sole slid after the landing on frame {frame}: {rows[frame]['frontSole']}")
    swing = [rows[frame]["frontSole"] for frame in (4, 5, 6)]
    if [61, 109] not in swing or [67, 107] not in swing or [71, 111] not in swing:
        fail(f"front swing is not the lifted step path: {swing}")
    if any(point[1] > 113 for point in swing):
        fail("a swing frame is not at least 3px above the ground line")

    def span(values: list[float]) -> float:
        return max(values) - min(values)

    pelvis_x = grouped["pelvis.translateX"]
    pelvis_y = grouped["pelvis.translateY"]
    torso = grouped["torso.rotation"]
    spear = grouped["spear.rotation"]
    if span(pelvis_x) < 6:
        fail(f"pelvis x travel {span(pelvis_x)} px is under 6")
    if span(pelvis_y) < 3:
        fail(f"pelvis sink {span(pelvis_y)} px is under 3")
    if span(torso) < 15:
        fail(f"torso rotation span {span(torso)} is under 15 degrees")
    if span(spear) < 20:
        fail(f"spear rotation span {span(spear)} is under 20 degrees")

    tip = grouped["tassel-tip.rotation"]
    thrust_lag = abs(tip[7] - spear[7])
    settle_lag = abs(tip[15] - spear[15])
    if thrust_lag < 4:
        fail(f"tassel tip does not lag the thrust: {thrust_lag} degrees")
    if settle_lag >= thrust_lag:
        fail(f"tassel tip does not settle: thrust lag {thrust_lag}, end lag {settle_lag}")
    ribbon_gap = abs(grouped["ribbon-tip.rotation"][7] - grouped["ribbon-root.rotation"][7])
    if ribbon_gap < 8:
        fail(f"ribbon free end stays too close to the root on the thrust: {ribbon_gap}")

    local_diff = rows[7]["gripForeLocal"] != rows[0]["gripForeLocal"]
    if not local_diff:
        fail("spear grip local anchor did not change after rotation; rest and posed would be the same")

    pixel_requests = []
    watched = ("ribbon-tip", "ribbon-mid", "ribbon-root", "tassel-tip", "tassel-root")
    for frame in range(FRAMES):
        for name in watched:
            pixel_requests.append(
                {"tool": "previewFrame", "params": {"frame": frame, "layer": LAYERS.index(name)}}
            )
    previews = run_batch(binary, project, pixel_requests)
    cloth_bottom = []
    cursor = 0
    for frame in range(FRAMES):
        bottoms = {}
        for name in watched:
            pixels = previews[cursor]["pixels"]
            cursor += 1
            lowest = None
            for offset, value in enumerate(pixels):
                if value:
                    y = offset // WIDTH
                    if lowest is None or y > lowest:
                        lowest = y
            bottoms[name] = lowest
            if lowest is None:
                fail(f"{name} is empty on frame {frame}")
            if lowest > 112:
                fail(f"{name} reaches y={lowest} on frame {frame}; that is too close to the sole at y=116")
        cloth_bottom.append({"frame": frame, **bottoms})

    sheet = root / "final" / "spear-lunge-sheet.png"
    atlas = root / "final" / "spear-lunge-sheet.atlas.json"
    atlas_proc = subprocess.run(
        [binary, "validate-atlas", "--atlas", str(atlas), "--sheet", str(sheet), "--size", "128"],
        check=False,
        capture_output=True,
        text=True,
    )
    if atlas_proc.returncode != 0:
        fail(f"atlas check exit {atlas_proc.returncode}\n{atlas_proc.stdout}\n{atlas_proc.stderr}")

    digest = hashlib.sha256(sheet.read_bytes()).hexdigest()
    stamp = json.loads((root / "reports" / "stamp.json").read_text(encoding="utf-8"))
    if stamp.get("sheetSha256") != digest:
        fail("sheet hash does not match reports/stamp.json")
    if stamp.get("engineSha") != ENGINE_SHA:
        fail("stamp SHA is not the pinned engine")

    report = {
        "engineSha": ENGINE_SHA,
        "versionString": version,
        "staticCheck": "passed",
        "playbackCheck": "not this script",
        "pelvisX": pelvis_x,
        "pelvisY": pelvis_y,
        "torsoRotation": torso,
        "spearRotation": spear,
        "tasselTipRotation": tip,
        "thrustTasselLagDegrees": round(thrust_lag, 2),
        "settleTasselLagDegrees": round(settle_lag, 2),
        "thrustRibbonTipMinusRootDegrees": round(ribbon_gap, 2),
        "frontStepPx": 74 - 56,
        "rows": rows,
        "clothBottomY": cloth_bottom,
        "observation": "Sole, grip, and cloth-root cells are constraint-solve canvas positions. restGripForeLocal is the authored rest offset. gripForeLocal on later frames is the anchor after rotation, and it is not used as the contact cell.",
        "bake": {
            "dropped": stamp.get("dropped"),
            "sealed": stamp.get("sealed"),
            "breaks": stamp.get("breaks"),
            "note": "sealed counts coverage fill. breaks are diagonal joins left after that fill. No polish layer was painted.",
        },
    }
    out = root / "reports" / "validate.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"static checks passed; pelvis x {min(pelvis_x):.2f}..{max(pelvis_x):.2f}, y {min(pelvis_y):.2f}..{max(pelvis_y):.2f}")
    print(f"torso {min(torso):.2f}..{max(torso):.2f} deg, spear {min(spear):.2f}..{max(spear):.2f} deg")
    print(f"tassel lag thrust {thrust_lag:.2f} deg, settle {settle_lag:.2f} deg; ribbon gap {ribbon_gap:.2f} deg")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
