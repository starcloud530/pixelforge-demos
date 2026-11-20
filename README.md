# pixelforge-demos

Pixel art and editable example projects made with the [PixelForge CLI](https://github.com/starcloud530/pixelforge-ai). This repository also hosts the evaluation tasks and selected runs.

[像素画室](https://starcloud530.github.io/pixelforge-demos/) · [作品集与工程下载](https://starcloud530.github.io/pixelforge-demos/gallery/) · [技术文档](https://starcloud530.github.io/pixelforge-ai/)

## 可重放作品

| 作品 | 内容 | 工程说明 |
| --- | --- | --- |
| [潮汐温室](https://starcloud530.github.io/pixelforge-demos/gallery/#tidal-glasshouse) | 51 个图块组成的五层地图 | [制作与重放](demos/tidal-glasshouse/README.md) |
| [雪岭邮差](https://starcloud530.github.io/pixelforge-demos/gallery/#alpine-courier) | 四个朝向、20 帧 | [制作与重放](demos/alpine-courier/README.md) |
| [星芒风候仪](https://starcloud530.github.io/pixelforge-demos/gallery/#observatory-machine) | 启动、采样与待机 | [制作与重放](demos/observatory-machine/README.md) |
| [潮汐科考道具](https://starcloud530.github.io/pixelforge-demos/gallery/#tide-survey-icons) | 八枚背包图标，两套配色 | [制作与重放](demos/tide-survey-icons/README.md) |
| [港口守灯人](https://starcloud530.github.io/pixelforge-demos/gallery/#port-keeper) | 四向行走与分层换装 | [制作与重放](demos/demo-zombie/README.md) |
| [哪吒逐帧动作](https://starcloud530.github.io/pixelforge-demos/gallery/#nezha) | 12 帧动作分解 | [制作与重放](demos/nezha-frame-attack/README.md) |

作品集提供工程包。四套画室选作的预览与工程包托管于 R2，文件地址、大小和 SHA-256 见[素材清单](demos/studio-media.json)。

仓库协作约定见 [AGENTS.md](AGENTS.md)、[CLAUDE.md](CLAUDE.md) 和 [Cursor 规则](.cursor/rules/)。

## 什么放哪 What goes where

| 路径 | 放什么 | 进 Git？ |
| --- | --- | --- |
| `site/` | 宣传落地页 + Gallery（GitHub Pages 根） | 是 |
| `demos/<slug>/` | 可重放工程包（如 `demo-zombie`：工程 + 脚本 + 小图） | 是 |
| `eval/tasks/<tier>-<slug>/` | **正式题**：`task.md` + `eval.md`（+ 可选 `start/`、`check.py`） | 是 |
| `eval/benchmarks/<id>/` | **转换质量基准**：协议、测试集、记录模板、可复核基线表 | 是 |
| `eval/runs/` | 草稿跑分：`trajectory.jsonl`、`output/`、`score.json`，以及基准重跑的工程 | **否**（gitignore） |
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
eval/benchmarks/      # conversion-quality protocols and baseline tables
eval/runs/            # scratch — gitignored
output/<task>/<ver>/<harness>/
```

## License

Demo art: [LICENSE-ASSETS.md](LICENSE-ASSETS.md) (CC BY 4.0). Scripts follow pixelforge-ai dual license when copied from there.
