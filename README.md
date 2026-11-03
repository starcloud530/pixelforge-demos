# pixelforge-demos

Companion to [pixelforge-ai](https://github.com/starcloud530/pixelforge-ai): marketing site, replayable demos, curated Agent runs, and eval task packs.

| Surface | URL |
| --- | --- |
| Marketing Pages | https://starcloud530.github.io/pixelforge-demos/ |
| Product docs | https://starcloud530.github.io/pixelforge-ai/ |
| CDN media | https://resources.pixelforge.torzsi.com/ |

Agent / tool layout rules: **[AGENTS.md](AGENTS.md)** (also mirrored for Claude as [CLAUDE.md](CLAUDE.md) and Cursor as [`.cursor/rules/`](.cursor/rules/)).

## 什么放哪 What goes where

| 路径 | 放什么 | 进 Git？ |
| --- | --- | --- |
| `site/` | 宣传落地页 + Gallery（GitHub Pages 根） | 是 |
| `demos/<slug>/` | 可重放工程包（如 `demo-zombie`：工程 + 脚本 + 小图） | 是 |
| `eval/tasks/<tier>-<slug>/` | **正式题**：`task.md` + `eval.md`（+ 可选 `start/`、`check.py`） | 是 |
| `eval/runs/` | 草稿跑分：`trajectory.jsonl`、`output/`、`score.json` | **否**（gitignore） |
| `output/<task>/<version>/<harness>/` | **精选对照**：`final/` + `trajectory.jsonl` + `meta.json` | 是（仅 curated） |

**`task_id`** = `eval/tasks/` 下的目录名，形如 `t5-ferrari-neon`（`<tier>-<slug>`）。精选包里的 `meta.json.task` 必须等于该 id。

### 禁止 / 不要

- 不要在 [pixelforge-ai](https://github.com/starcloud530/pixelforge-ai) 写 `examples/`（已 ban）。
- 不要把草稿 `eval/runs/` 提交进仓。
- 不要把大体积宣传视频塞进本仓；走 CDN。
- 不要把未人工过目的跑分直接当 `output/` 发布；默认 `aestheticApproval: false`。
- 不要把产品文档 MkDocs 放进本仓 Pages（docs 只在 pixelforge-ai）。

### Curated `output/` 形状

```
output/<task_id>/<version>/<harness>/
  meta.json           # task, version, harness, cliVersion, aestheticApproval
  trajectory.jsonl    # 每行一次 pixelforge 进程调用
  final/              # 访客应看到的 PNG / GIF / sheet / 工程
  README.md
```

`version`: `v1`, `v2`, … · `harness`: `grok-bot` | `codex` | `claude-code` | …

模板：[`output/_template/v1/grok-bot/`](output/_template/v1/grok-bot/) · 题面模板：[`eval/tasks/_template/`](eval/tasks/_template/) · 详解：[`eval/README.md`](eval/README.md)

## Layout (tree)

```
site/                 # GitHub Pages
demos/<slug>/         # replayable packs
eval/tasks/           # formal task briefs
eval/runs/            # scratch — gitignored
output/<task>/<ver>/<harness>/
```

## License

Demo art: [LICENSE-ASSETS.md](LICENSE-ASSETS.md) (CC BY 4.0). Scripts follow pixelforge-ai dual license when copied from there.
