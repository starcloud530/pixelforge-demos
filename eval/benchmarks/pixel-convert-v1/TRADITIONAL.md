# Traditional baseline supplement (issue #131, first slice)

This adds one method under the existing v1 comparison rules, not a protocol v2.
`protocol.json`, `manifest.json`, `fixtures/hashes.json`, `templates/fields.json`
and every byte under `records/v1/center-sample/` remain frozen. The old
`traditional: not-run` in protocol.json records the initial v1 snapshot; the
actual new method availability is documented here and in its separate records.
No constants, probes, thresholds, human fields or source fixtures changed.

## Fixed method

`traditional` is **dominant-cell majority + the existing limit palette strategy**,
not a claim to be the best possible classical method. Engine code already exists
in pixelforge-ai at `9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d`.
For every cell the engine counts source pixels with alpha >=128, outputs
transparent unless more than half the block is opaque, then chooses the most
frequent opaque RGB (ties: lower RGB). No dithering or per-fixture tuning.
The CLI then applies its existing `limit` strategy, max 16 opaque colors.

```bash
pixelforge convert --file <same-source.png> --output <new-project.json> \
  --width <64-or-128> --height <same> --engine dominant \
  --palette-strategy limit --max-colors 16
```

Exactly three processes per fixture/size; all parameters fixed across fixtures.
Only output paths differ for separate runs. Commands are stored as portable
argv (the common output filename is canonicalized, as in the original record).
Use the same v1 4x nearest-neighbor #808080 review renderer for both methods:

```bash
python3 eval/benchmarks/pixel-convert-v1/review_sheet.py \
  --project eval/runs/pixel-convert-v1/projects/pf-cv-002-line-64x64-traditional-run1.json \
  --output eval/runs/pixel-convert-v1/traditional-line-64-review.png
```

Review images and editable projects stay local/ignored. Human scores remain
null. Automatically measured structural flags are not human defect judgments.

## Reproduce

Build a separate checkout/worktree of pixelforge-ai at the exact pin (released
v0.1.0-rc.2 alone is insufficient):

```bash
# From a pixelforge-ai checkout:
git worktree add --detach ../pixelforge-cli-v1 9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d
cd ../pixelforge-cli-v1
cargo build --release --locked -p pixelforge-cli
# From pixelforge-demos:
export PIXELFORGE_BIN=/absolute/path/pixelforge-cli-v1/target/release/pixelforge
python3 eval/benchmarks/pixel-convert-v1/check.py --with-cli
# Optional fresh timed recording; do NOT overwrite the frozen center record:
python3 eval/benchmarks/pixel-convert-v1/run_baseline.py --method traditional \
  --cli-commit 9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d \
  --record-dir eval/runs/pixel-convert-v1/fresh-traditional-record
```

The commit flag is an assertion by the operator; build from a clean pinned
worktree. The traditional meta also captures the local binary SHA-256. Binary
hashes can differ across toolchains, while output index/palette hashes and
derived metrics must reproduce. Timings are observations, not quality scores.

## Recorded facts (12 rows per method)

| Published table field | center-sample (frozen) | traditional/dominant |
| --- | ---: | ---: |
| feature_probes_passed / total | 22 / 24 | 22 / 24 |
| feature_retention_auto | 0.916667 | 0.916667 |
| auto_severe_rows | 1 / 12 | 1 / 12 |
| palette_within_budget_rows | 12 / 12 | 12 / 12 |
| deterministic_rows | 12 / 12 | 12 / 12 |
| psnr_box_mean (exact rows excluded) | 36.723267 | 36.920606 |
| ssim_box_mean | 0.973172 | 0.973112 |
| duration_ms_median_of_row_medians | 3 | 5 |

Both have S2 on `pf-cv-002-line` at 64; the `pf-cv-005-gap` 64 row
passes only 2/3 probes in both. Both have two exact PSNR rows (slime).
Timings were collected on different runs/machines, so the 3 vs 5 ms values
are **not a calibrated speed comparison**. Neither auxiliary fidelity metric
establishes a winner, feature-preserving learning, aesthetic approval or a
model go/no-go. There is no trained model in this slice.

Paired data and the later training/evaluation plan are separate:
[paired-seed README](../pixel-convert-pairs-v0/README.md) ·
[training plan](../pixel-convert-pairs-v0/TRAINING_PLAN.md).
