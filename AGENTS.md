# pixelforge-demos — agent rules

本仓是 **pixelforge-ai 的配套仓**：宣传、可重放 demo、评测题、精选跑分。  
**不**放引擎源码；**不**当 docs 站。像素编辑仍只通过本机 `pixelforge` CLI（安装自 pixelforge-ai）。

命令语义以主仓为准：  
https://starcloud530.github.io/pixelforge-ai/agent-skill/ · https://starcloud530.github.io/pixelforge-ai/tool-api/

## Hard rules

1. **目录职责（强制）**
   - 题面 → `eval/tasks/<task_id>/`（`task.md` + `eval.md`）
   - 草稿跑分 → `eval/runs/<run-id>/`（**勿 commit**）
   - 精选对照 → `output/<task_id>/<version>/<harness>/`
   - 可重放工程包 → `demos/<slug>/`
   - 宣传静态站 → `site/`
2. **`task_id`** = `eval/tasks/` 目录名 = `<tier>-<slug>`（例 `t5-ferrari-neon`）。`output/.../meta.json` 的 `task` 字段必须一致。
3. **新正式题**：复制 `eval/tasks/_template/`，改名，填 `task.md` / `eval.md`。`_template` 本身不可当题跑。
4. **Agent 只读 `task.md`**；不要把 `eval.md`（评分 / 边界剧透）塞进 Agent 上下文。
5. **默认 `aestheticApproval: false`**，除非人类盲评改写。
6. **禁止**往 pixelforge-ai 写或恢复 `examples/`。
7. **大媒体** → `https://resources.pixelforge.torzsi.com/`，不要塞爆本仓。
8. **不要编造** `pixelforge` 子命令；以主仓 agent-skill 为准。
9. 主仓 skill 在 pixelforge-ai 的 `.cursor/skills/`；本仓**不**复制一份 skill 树，需要时打开主仓或已安装的 CLI + 主仓文档。
10. **UI / layout**：Avoid unnecessary secondary labels and descriptions. Let the layout do the explaining.

## 放哪里（速查）

| 要存的东西 | 路径 |
| --- | --- |
| 新评测题 | `eval/tasks/<tier>-<slug>/` |
| 某次草稿轨迹 / 机判 | `eval/runs/<run-id>/` |
| 对外可看的好结果（分 harness） | `output/<task_id>/vN/<harness>/` |
| 官方可重放 demo 包 | `demos/<slug>/` |
| 落地页改版 | `site/` |

详情：根 [README.md](README.md) · [eval/README.md](eval/README.md) · [output/README.md](output/README.md)
