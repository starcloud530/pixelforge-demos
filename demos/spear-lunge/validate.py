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
import struct
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
    "ribbon-finish",
    "thigh-far",
    "shin-far",
    "foot-far",
    "upper-far",
    "fore-far",
    "hand-far",
    "pelvis",
    "torso",
    "thigh-near",
    "shin-near",
    "foot-near",
    "spear",
    "tassel-root",
    "tassel-tip",
    "tassel-finish",
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


def media_timing(root: Path, expected: list[int]) -> dict:
    """Read animation control blocks; do not infer timing from average FPS."""
    final = root / "final"
    png = (final / "spear-lunge.apng").read_bytes()
    position = 8
    apng = []
    while position < len(png):
        length = struct.unpack_from(">I", png, position)[0]
        kind = png[position + 4 : position + 8]
        data = png[position + 8 : position + 8 + length]
        if kind == b"fcTL":
            numerator, denominator = struct.unpack_from(">HH", data, 20)
            apng.append(numerator * 1000 / (denominator or 100))
        position += length + 12
    if apng != expected:
        fail(f"APNG frame timing differs from project: {apng}")
    gif = (final / "spear-lunge.gif").read_bytes()
    position = 13 + (3 * (2 ** ((gif[10] & 7) + 1)) if gif[10] & 128 else 0)
    delays = []
    pending = 0

    def skip_blocks(pos):
        while gif[pos]:
            pos += gif[pos] + 1
        return pos + 1

    while position < len(gif):
        marker = gif[position]
        position += 1
        if marker == 0x3B:
            break
        if marker == 0x21:
            label = gif[position]
            position += 1
            if label == 0xF9:
                if gif[position] != 4:
                    fail("bad GIF graphic-control block")
                pending = int.from_bytes(gif[position + 2 : position + 4], "little") * 10
            position = skip_blocks(position)
        elif marker == 0x2C:
            packed = gif[position + 8]
            position += 9
            if packed & 128:
                position += 3 * (2 ** ((packed & 7) + 1))
            position += 1
            position = skip_blocks(position)
            delays.append(pending)
            pending = 0
        else:
            fail(f"unexpected GIF block {marker:#x}")
    if (
        len(delays) != len(expected)
        or any(abs(a - b) > 10 for a, b in zip(delays, expected))
        or abs(sum(delays) - sum(expected)) > 10
    ):
        fail(
            f"GIF frame timing does not preserve authored cadence within centisecond precision: {delays}"
        )
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "frame=best_effort_timestamp_time:format=duration",
                "-of",
                "json",
                str(final / "spear-lunge-review.mp4"),
            ],
            text=True,
        )
    )
    timestamps = [float(f["best_effort_timestamp_time"]) for f in probe["frames"]]
    cumulative = [sum(expected[:i]) / 1000 for i in range(len(expected))]
    target = [repeat * sum(expected) / 1000 + t for repeat in range(3) for t in cumulative]
    target.append(sum(expected) * 3 / 1000)  # terminal frame preserves the final hold
    if len(timestamps) != len(target) or any(
        abs(a - b) > 0.002 for a, b in zip(timestamps, target)
    ):
        fail("review MP4 presentation times differ from the three authored action repetitions")
    if abs(float(probe["format"]["duration"]) - sum(expected) * 3 / 1000) > 0.002:
        fail("review MP4 truncates the final pose hold")
    return {
        "apngDelaysMs": apng,
        "gifDelaysMs": delays,
        "mp4Frames": len(timestamps),
        "mp4DurationSeconds": float(probe["format"]["duration"]),
        "visualPlayback": "not established by metadata checks",
    }


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
    version = subprocess.run(
        [binary, "--version"], check=False, capture_output=True, text=True
    ).stdout.strip()

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
        grouped[f"{part}.{channel}"] = [
            float(item["value"]) for item in samples[index : index + FRAMES]
        ]
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
        for side, solved_sole in [("near", front), ("far", rear)]:
            foot = anchor(parts["foot-" + side], "sole")
            if (foot["canvasX"], foot["canvasY"]) != (
                solved_sole["canvasX"],
                solved_sole["canvasY"],
            ):
                fail(f"foot-{side} detached from shin IK on frame {frame}")
        constraints = {item["name"]: item for item in report["constraints"]}
        near_grip = (hand_near["canvasX"], hand_near["canvasY"]) == (
            grip_fore["canvasX"],
            grip_fore["canvasY"],
        )
        far_grip = (hand_far["canvasX"], hand_far["canvasY"]) == (
            grip_rear["canvasX"],
            grip_rear["canvasY"],
        )
        ribbon_held = (ribbon["canvasX"], ribbon["canvasY"]) == (
            hip_ribbon["canvasX"],
            hip_ribbon["canvasY"],
        )
        tassel_held = (tassel["canvasX"], tassel["canvasY"]) == (
            spear_tassel["canvasX"],
            spear_tassel["canvasY"],
        )
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
        fail(
            "spear grip local anchor did not change after rotation; rest and posed would be the same"
        )

    # Read kernel state to verify the published timing and presentation layers.
    scene = run_batch(binary, project, [{"tool": "scene"}])[0]
    if scene["activeFrame"] != 0:
        fail("review project must reopen on source frame 0 before constraint resampling")
    expected_delays = [150, 80, 70, 100, 45, 40, 40, 55, 85, 60, 65, 70, 80, 90, 100, 160]
    if [frame["delayMs"] for frame in scene["frames"]] != expected_delays:
        fail("published timing differs from the authored anticipation/thrust/recovery timing")
    for name in ("ribbon-finish", "tassel-finish"):
        layer = scene["layers"][LAYERS.index(name)]
        if layer["role"] != "polish" or layer["visible"] is not True:
            fail(f"{name} should be a visible, unbound per-frame polish layer")
    for name in ("ribbon-root", "ribbon-mid", "ribbon-tip", "tassel-root", "tassel-tip"):
        if scene["layers"][LAYERS.index(name)]["visible"] is not False:
            fail(f"rigid guide {name} should not be rendered over the curved finish")

    pixel_requests = []
    watched = ("ribbon-finish", "tassel-finish")
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
                fail(
                    f"{name} reaches y={lowest} on frame {frame}; that is too close to the sole at y=116"
                )
        cloth_bottom.append({"frame": frame, **bottoms})

    # Verify the rendered boot, not only an abstract IK point, meets the floor.
    feet = run_batch(
        binary,
        project,
        [
            {
                "tool": "previewFrame",
                "params": {"frame": frame, "layer": LAYERS.index("foot-" + side)},
            }
            for frame in range(FRAMES)
            for side in ("near", "far")
        ],
    )
    for frame in range(FRAMES):
        for offset, side in enumerate(("near", "far")):
            pixels = feet[frame * 2 + offset]["pixels"]
            x, y = rows[frame]["frontSole" if side == "near" else "rearSole"]
            if pixels[y * WIDTH + x] == 0:
                fail(f"rendered {side} sole is empty on frame {frame}")
            if side == "far" or frame not in (4, 5, 6):
                lowest = max(n // WIDTH for n, v in enumerate(pixels) if v)
                if lowest != 116:
                    fail(
                        f"rendered support boot {side} floats or penetrates the floor on frame {frame}: y={lowest}"
                    )

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

    media = media_timing(root, expected_delays)
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
        "frameDelaysMs": expected_delays,
        "mediaTiming": media,
        "totalDurationMs": sum(expected_delays),
        "independentFeet": "sole attachments match solved shin IK endpoints on every frame",
        "rows": rows,
        "clothBottomY": cloth_bottom,
        "observation": "Sole, grip, and cloth-root cells are constraint-solve canvas positions. restGripForeLocal is the authored rest offset. gripForeLocal on later frames is the anchor after rotation, and it is not used as the contact cell.",
        "bake": {
            "dropped": stamp.get("dropped"),
            "sealed": stamp.get("sealed"),
            "breaks": stamp.get("breaks"),
            "note": "sealed counts coverage fill. breaks are diagonal joins left after that fill. Curved cloth is authored from evaluated guide anchors into per-frame polish layers after bake.",
        },
    }
    out = root / "reports" / "validate.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"static checks passed; pelvis x {min(pelvis_x):.2f}..{max(pelvis_x):.2f}, y {min(pelvis_y):.2f}..{max(pelvis_y):.2f}"
    )
    print(
        f"torso {min(torso):.2f}..{max(torso):.2f} deg, spear {min(spear):.2f}..{max(spear):.2f} deg"
    )
    print(
        f"tassel lag thrust {thrust_lag:.2f} deg, settle {settle_lag:.2f} deg; ribbon gap {ribbon_gap:.2f} deg"
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
