# pixelforge-demos

Companion to [pixelforge-ai](https://github.com/starcloud530/pixelforge-ai): marketing site, replayable demos, curated Agent runs, and eval task packs.

- **Marketing Pages:** https://starcloud530.github.io/pixelforge-demos/
- **Docs (product):** https://starcloud530.github.io/pixelforge-ai/
- **CDN media:** https://resources.pixelforge.torzsi.com/

## Layout

```
site/                 # GitHub Pages (landing + gallery)
demos/<slug>/         # replayable packs (e.g. demo-zombie)
eval/tasks/           # Agent eval briefs
eval/runs/            # scratch — gitignored
output/<task>/<ver>/<harness>/   # curated finals + trajectory
```

### Curated `output/`

`output/<task>/<version>/<harness>/` with `meta.json`, `trajectory.jsonl`, `final/`.
Harness: `grok-bot`, `codex`, `claude-code`, …

Do **not** put demo packs into `pixelforge-ai` (`examples/` is banned there).

## License

Demo art: [LICENSE-ASSETS.md](LICENSE-ASSETS.md) (CC BY 4.0).
