# Curated outputs

精选对照（宣传 Gallery / harness 对比）。**不是**草稿跑分目录——草稿在 `eval/runs/`。

`task` / 路径第一段必须等于正式题目录名：`eval/tasks/<task_id>/`。

```
output/<task_id>/<version>/<harness>/
  meta.json
  trajectory.jsonl
  final/
  README.md
```

| Field | Values |
| --- | --- |
| `task_id` | 同 `eval/tasks/` 目录，如 `t5-ferrari-neon` |
| `version` | `v1`, `v2`, … |
| `harness` | `grok-bot`, `codex`, `claude-code`, … |

Only curated packs are committed. See root [AGENTS.md](../AGENTS.md).
