# Later model PoC: data, training and decision plan

Status: **plan only; no weights, optimizer run, human evaluation or go/no-go**.
The first slice supplies a redistributable seed and a second classical record.
It does not meet the full acceptance of pixelforge-ai #131 or replace #17.

## 1. Data gates before training

- Expand toward 100–200 distinct character identities from original commissioned
  art with explicit redistribution rights, CC0, CC BY, or documented in-repo
  grants. Store source URL/creator/license text/retrieval date/change history,
  source and target hashes, palette, requested keep-features and artist consent.
  Reject unclear provenance, game rips and arbitrary web image collections.
- Source reference → artist-authored/corrected 64 and 128 target, ≤16 opaque
  colors plus transparent index 0. Save editable target, conversion-before,
  correction-after, feature checklist, defect reasons and correction history.
  Record the artist and correction tool, not fabricated duration labels. Time
  logs are valid only if collected prospectively using the benchmark rules.
- Collect successes AND failures: thin weapons/antennae, gaps, similar color
  identities, AA fringes, low-contrast edges and color-budget pressure. Record
  failures independently of baseline selection; do not discard hard outputs.
  Keep artist corrections distinct from automatic proxy/negative samples.
- Current 6-character seed remains unreviewed and ineligible. It has zero artist
  corrections, only flat geometry, two transparent-background failure examples,
  and correlated sizes. It is useful for pipeline tests, not evidence a model
  can generalize. Proxy images cannot silently be relabeled artist ground truth.

## 2. Freeze identity splits and protect the benchmark

Use the already published `lib/splits.py:future_split` rule without changing it:
SHA-256(character_id), first byte mod 10: 0–1 dev, 2–3 test, 4–9 train. Publish
split version/hash and immutable manifest before any optimization. Group all
poses, outfits, recolors, crops, resolutions and near-duplicates by original
identity; no random image/patch split. Also audit source-family/artist overlap
and report style-stratified counts; source-style leakage can survive id splits.
The seed's reserved allocation is 4/1/1; nothing is trained on those slots now.

**The six `pf-cv-001..006` protocol-v1 objects, all their variants and outputs,
checklists and generated proxy labels must not enter ANY model train/dev/test
set.** Exclude by id, provenance lineage, exact hashes and perceptual/manual
near-duplicate review. Data augmentation must inherit its parent's split.
Do not generate "new" training characters by perturbing v1 fixture geometries.

The #127 benchmark remains a separate, public post-selection audit, not a model
validation set or a private holdout. No checkpoint, architecture, loss weight or
feature threshold may be chosen from its scores. Choose all those on dev;
lock the checkpoint and inference parameters first, run test once, then run the
frozen protocol audit. Public fixtures are already visible, so even the audit
cannot support a claim of unseen-data generalization. A genuinely private
holdout later needs separate identities and authorized private-bucket storage;
create no bucket or expense now. Keep a data access/contamination log.

## 3. Minimal training experiment (not implemented)

Start with a small supervised palette-conditioned encoder/decoder, not training
an image foundation model from scratch. Inputs: normalized RGBA reference,
target grid size, an explicitly provided palette of ≤16 opaque colors, and
artist-annotated keep-feature masks/tokens. Output: per-cell categorical logits
for transparent plus palette indices. Export predictions through the existing
engine/CLI into editable indexed projects; engine/model code and weights metadata
belong in pixelforge-ai, never vendored into demos.

First implement a mask-only/alpha ablation, then full palette classification.
Train with transparent/opaque class-balanced cross entropy and a boundary loss;
add keep-feature-region weighting only from training annotations. Tune weights
on dev and record unweighted metrics as a check against gaming. Compare against
an otherwise identical model without feature conditioning. Keep palette
construction independent of test target colors: supply the same input palette
policy to every paired comparison; target-only palettes would leak labels.

Predeclare seed, architecture, data manifest, dependency lock, epochs/early-stop,
hardware/time/memory budget and maximum experiment count before compute starts.
Checkpoint selection uses dev only. Log failures, random seeds, latency and
training cost; stop on a fixed budget. No paid GPU run or model download is
initiated by this document. More synthetic data alone is not an expansion gate.

## 4. Evaluation protocol and genuine human evidence

1. Replay pinned center-sample and the fixed `traditional`/dominant pipeline.
   Before model selection, use dev to select any stronger classical candidate
   (e.g. the already available kmeans/contrast-outline engines); do not tune
   per v1 fixture or only compare against a deliberately weak reference.
2. Freeze a model and inference command. On the separate #127 audit, use the
   exact six sources, 64×64 and 128×128, limit 16 opaque colors, three identical
   inference runs for determinism/latency and nearest-neighbor 4x #808080.
   New method rows go in `records/v1/model/` using unchanged fields. Any protocol
   constant change requires a new protocol version, not rewritten v1 hashes.
3. Report automatic probes, flags, palette budget, exact index hashes and timing
   as automation. PSNR/SSIM are auxiliary only; do not optimize the model for
   the box-filter reference. All human fields stay null until real observations.
4. On a larger held-out, artist-corrected character test set, obtain randomized,
   method-blinded A/B/tie ballots using v1 sheets, with at least 3 independent
   raters per character/size/method pair; hide the method seal. Collect checklist
   feature decisions and S1–S5 from those raters, separately from auto probes.
5. Have at least 2 editors prospectively retouch randomized matched inputs to
   the deliverability checklist, counterbalancing method order. Use the same
   editor/tool policy per block; record interruptions, unfinished/censored tasks,
   missingness and editable projects. Do not time the generation process and
   call it polish time. Report agreements and disagreements, not only averages.
6. Pre-register statistics before ballots: pairwise score=(wins+0.5*ties)/N;
   characterize uncertainty by character-cluster bootstrap (both sizes and
   raters stay within identity clusters), with editor blocking for time. The
   existing probe-count Wilson interval is descriptive for six fixtures, not
   an independent-character confidence interval for the later study.

## 5. Proposed continue/stop gates (must be agreed before the study)

A useful next milestone needs at least 30 distinct reviewed held-out characters
with real corrections (in addition to the public protocol audit). Against the
best dev-selected classical method on that set, propose ALL of:

- Blind preference score lower 95% character-cluster CI >0.5.
- Human feature retention improves by ≥10 percentage points, with the CI of
  the difference above 0; human severe-defect rate does not regress (report its
  difference CI rather than converting automatic flags into human labels).
- Median matched editor polish time falls ≥20%, with a positive CI for time
  saved, without hiding incomplete edits. Predefine timeout handling.
- All outputs satisfy canvas, transparency and ≤16-color constraints and can
  be opened/edited; runtime, compute cost and correction burden fit the
  pre-agreed budget on the recorded hardware.

If uncertainty overlaps no benefit, collect more independent identities or
report inconclusive. If the model only improves PSNR, wins on synthetic seed
art or loses once editors finish the sprites, stop/revise rather than declare
success. The current 22/24 vs 22/24 automatic probe counts, no ballots and no
polish logs justify **no model continuation conclusion**. The full issue stays
open until a real PoC and those comparisons exist.
