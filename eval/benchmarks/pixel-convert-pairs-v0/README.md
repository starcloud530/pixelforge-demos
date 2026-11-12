# Paired conversion seed v0 — not a model dataset release

Issue [#131](https://github.com/starcloud530/pixelforge-ai/issues/131), first slice.
Six newly authored geometric characters; each has a transparent **256×256 source
reference** and separately rasterized **64×64 and 128×128 target proxy**. Thus
12 source↔target pairs, 18 unique paired PNGs, plus 2 observed failure PNGs.
All art is CC BY 4.0 with attribution PixelForge / starcloud530; see [LICENSE.md](LICENSE.md).
No downloads, scraped art, paid image generation or external artwork.

| character_id | keep / hard case | intended future split |
| --- | --- | --- |
| pf-pair-001-antenna-bot | 1 source-pixel antenna, two eyes, foot gap | test |
| pf-pair-002-pennant-keeper | pole, pennant, arm contact | train |
| pf-pair-003-ring-diver | visor rim, transparent torso window, fins | train |
| pf-pair-004-lantern-moth | fine antennae, paired wing panels | train |
| pf-pair-005-twin-ear-scout | separated ears, narrow side tool | train |
| pf-pair-006-fork-crab | forked claws, eye stalks, leg gaps | dev |

Paths/hashes/licenses/features are in `manifest.json`. Files follow
`png/<character_id>-source.png`, `-target-64.png`, `-target-128.png`.
Failure files are `failures/pf-pair-001-antenna-bot-center-sample-{64,128}.png`.
Their manifest records a reproducible pixel observation: antenna alpha 0 in the
candidate, 255 in the proxy at [31,12] / [62,24]. These are **automatic facts**,
not invented human defect scores. Both are generated with pinned center-sample,
limit, 16 colors. The remaining designs are hard cases, not asserted failures.

## What these labels are NOT

Targets are geometry-derived proxies, not artist corrections or gold sprites.
The generator uses a fixed coordinate rule with essential details widened to at
least one target pixel; it is not the center-sample or dominant output. Sources
are flat, hard-alpha program art, not realistic concept art. No texture diversity,
AA boundary coverage, >16-color compression challenge or professional polish
labels exist in this seed. Thin-line and gap cases alone do not cover the real
reference-to-sprite task. Do not count the two sizes as independent characters.

Every record is `split: seed-unreviewed`, `training_eligible: false`.
`intended_split` uses the unchanged v1 `future_split(character_id)` rule
(4 train / 1 dev / 1 test), only to reserve identities for future review. This
seed is too small for training/validation claims; no training ran. **All six
`pf-cv-*` protocol-v1 fixtures and their derivatives are excluded from model
train/dev/test**, not reused as paired labels. The seed checker rejects their
ids and byte-identical PNGs; future curation must also reject near-duplicates.

## Replay and checks

Build the pinned CLI as described in
[TRADITIONAL.md](../pixel-convert-v1/TRADITIONAL.md), then from demos:

```bash
export PIXELFORGE_BIN=/absolute/path/to/pinned/target/release/pixelforge
python3 eval/benchmarks/pixel-convert-pairs-v0/check.py
python3 eval/benchmarks/pixel-convert-pairs-v0/check.py --with-cli
# Generate elsewhere for inspection; --with-cli already does this in a temp dir:
python3 eval/benchmarks/pixel-convert-pairs-v0/generate.py \
  --output eval/runs/pixel-convert-pairs-v0/replay
```

All authored indexed art passes through `new`, `call`, `preview`, `export png`
in the CLI; no direct project JSON writes or copied engine implementation.
The generator also creates local-only staged previews. Source/target exports
are dataset assets, not screenshots. The checker tests metadata rejection,
hashes, alpha/color budgets, intended split, frozen-set disjointness, failure
observations and (with CLI) exact regeneration of all 20 PNGs.

## Storage boundary

This seed keeps only 20 tiny PNGs in git. No CDN upload was attempted or claimed.
Before expansion, publish licensed assets through an approved upload path to
`https://resources.pixelforge.torzsi.com/` (existing pixelforge-resources R2),
with content-addressed keys, sha256/size/license manifests and a read-back hash
check. Paths proposed for that future upload are not live objects. Do not store
hundreds of images in git. Private future holdout material belongs in a private
bucket only after authorization; no bucket, resource or spend is created here.

Next work and explicit decision gates: [TRAINING_PLAN.md](TRAINING_PLAN.md).
