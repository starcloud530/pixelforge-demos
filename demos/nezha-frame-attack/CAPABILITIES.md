# 能力归因

本文只记录 `demos/nezha-frame-attack/` 当前树里能核对到的事实，供判断这个示例实际用过、证明过哪些能力。它补充 [README.md](README.md)，不改变重跑或校验行为。

核对基准是 main 提交 `92a0fe74`（与 PR [#5](https://github.com/starcloud530/pixelforge-demos/pull/5) 头提交 `9710c60` 的本目录 `git diff` 为空）。写这份说明时，环境里没有 `pixelforge` 可执行文件，没有重跑 CLI；运行时结论来自脚本、已提交工程，以及 `reports/` 里记录的 `pixelforge 0.1.0-rc.5` 结果。

本示例没有验证 IK、约束、曲线或物理解算。它只有朝右攻击，不能直接充当完整八向测试素材。

## PixelForge CLI 操作

工程起点不是 CLI 新建。`build.py` 第 204–205 行把 `source/body.pxf.json` 复制成 `work/nezha-attack.pxf.json`，之后的像素写入都走 CLI。Python 只组请求；`ffmpeg` 只把已导出的 APNG 包成深色背景 GIF（第 362–380 行），不是 PixelForge 子命令。

`build.py` 实际拉起的 CLI 参数：

| 调用 | 位置 | 作用 |
| --- | --- | --- |
| `call --project <工程> --request-file <JSON 数组>` | 第 38 行；每帧 `attack-NN`，最后 `tags` | 批量执行下表工具 |
| `export png --project <工程> --out-dir final/frames` | 第 330 行 | 1× 帧 PNG，`pixelforge-000.png` … `pixelforge-011.png` |
| `export png --project <工程> --out-dir work/preview-frames --scale 4` | 第 331 行 | 4× 预览；第 356–360 行从中复制 0、2、5、8 帧到 `final/poses/` |
| `export sheet --project <工程> --output final/nezha-attack-sheet.png --cols 6 --atlas final/nezha-attack.atlas.json` | 第 332–343 行 | 图集。脚本只传 `--cols 6`；已提交 atlas 为 6×2、每格 128×128、`scale` 1 |
| `export apng --project <工程> --output final/nezha-attack.apng --tag attack_right --scale 4` | 第 344–355 行 | 按 `attack_right` 导出透明 APNG |
| `--version` | 第 383 行 | 写入 `reports/stamp.json` 的 `cliVersion` |

`call` 请求里的 `tool` 名称（`build.py`）：

| 工具 | 位置 | 本示例里的用法 |
| --- | --- | --- |
| `polygon` | 第 41–47 行 | 填充多边形：红绫、风火轮焰、短裤、枪头、枪缨 |
| `fillRect` | 第 49–57 行 | 近手护腕矩形 |
| `ellipse` | 第 59–68 行 | 风火轮椭圆、指节 |
| `line` | 第 70–71 行 | 轮辐、枪身高光、速度线、后脚火花 |
| `duplicateFrame` | 第 209 行 | 帧 1–11 复制上一帧 |
| `setActiveFrame` | 第 210、325 行 | 切到新帧；全部画完后回到帧 0 |
| `copyRect` | 第 211–222 行 | 帧 1–11 把帧 0 的第 2 层整幅 128×128 拷回 |
| `moveRect` | 第 224–246 行 | 有身体位移时挪 `(34,16)` 起 45×64；有 `headLean` 时再挪头部 35×39 |
| `setActiveLayer` | 第 248、253、280 行 | 切到层 0、1、3 |
| `eraseRect` | 第 249、254、281 行 | 每帧清空层 0、1、3 后重画 |
| `setFrameDelay` | 第 323 行 | 写入该帧 `delayMs` |
| `addTag` | 第 326–328 行 | 见下一节标签 |

`validate.py` 另有这些调用，不改工程：

| 调用 | 位置 |
| --- | --- |
| `call --project <工程> --request-file <JSONL>`，工具 `scene` | 第 21–45、122、171 行 |
| 同上，工具 `previewFrame`，参数 `frame`、`layer` | 第 139–146 行。12 帧 × 4 层 |
| `validate-atlas --atlas final/nezha-attack.atlas.json --sheet final/nezha-attack-sheet.png --four-direction off` | 第 176–186 行 |

当前两个脚本都没有 `constraint`、`bake`、`solveConstraints`，也没有曲线、IK、方向或物理相关子命令。`reports/stamp.json` 的 `method` 与 `source/poses.json` 第 2 行写的是显式逐帧姿势。

已提交 `final/nezha-attack.pxf.json` 与 `source/body.pxf.json` 的顶层键只有 `format`、`version`、`width`、`height`、`activeFrame`、`activeLayer`、`layers`、`palette`、`paletteLocked`、`frames`；成片工程多一个 `tags`。文件里没有 `parts`、`curves`、`constraints`、IK 或 bake 字段。`validate.py` 第 127–128 行还要求 CLI `scene` 结果里的 `parts`、`curves`、`constraints` 为假值。`reports/validate.json` 记录当时 `rigMetadata` 为 `absent`、`status` 为 `passed`。这是对空元数据的检查，不是一次求解演示。

`build.py` 第 252 行注释写 “Kinetic chain”。紧接着的第 257–265 行用身体位移和脚点的闭式算术放膝点，再调用 `segment()` 画粗多边形。没有骨骼、没有迭代求解、没有 IK 工具。轮子相位是帧号（第 104–139、256、262 行），红绫偏移是 `poses.json` 里的整数 `ribbonLag`（第 142–176、250–251 行）。这些是逐帧绘图参数，不是物理解算。

## 逐帧编排

画布 128×128。层从后到前：`silk`、`legs-and-wheels`、`body`、`arms-and-spear`（`brief.json` 第 25–29 行，工程 `layers` 同名）。色板 33 色，索引 0 为透明；`paletteLocked` 在底稿和成片里都是 false。底稿只有 1 帧：层 2 有 1069 个非透明像素，包围盒 x 42–71、y 22–79；层 0、1、3 为空。成片 12 帧的身体层仍各为 1069 个非透明像素。帧 0 和帧 11 的身体层与底稿逐像素相同；帧 1–10 的身体层因 `moveRect` 与底稿不同。

姿势全部来自 `source/poses.json` 的 `frames[]`。`build.py` 第 197–203 行读出 `body.offset`、`weapon.grip`、`weapon.angleDegrees`、`delayMs`、`feet`、`ribbonLag`；`headLean` 在第 235 行按帧读取。没有插值步骤。屏幕 x 向右增大。出枪时握点 x 从 66 增到 80，角度 −5° 的单位向量 x 分量为正，枪尖在握点右侧；速度线画在 x=92、112、104–118（第 312–317 行）。标签名是 `attack_right`。已查看 GIF、6×2 图集、帧 0 与帧 5，以及 `poses/` 的准备、蓄力、出枪、收势四张图，画面是这一条朝右攻击。

时长单位是毫秒。阶段和来自 `brief.json` 与 `addTag`：

| 标签 | 帧 | 循环 | 时长 |
| --- | --- | --- | --- |
| `attack_right` | 0–11 | `forward` | 1070 |
| `ready` | 0–0 | `once` | 180 |
| `charge` | 1–3 | `once` | 220 |
| `thrust` | 4–6 | `once` | 160 |
| `recover` | 7–11 | `once` | 510 |

`attack_right` 覆盖全部帧，与阶段标签重叠。同一组范围写在成片工程 `tags` 和 `final/nezha-attack.atlas.json` 的 `tags`。

| 帧 | 阶段 | 身体 dx, dy | 头倾 | 握点 | 枪角度° | 前脚 | 后脚 | 红绫滞后 | 时长 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | ready | 0, 0 | 0 | 66, 67 | −65 | 60, 100 | 48, 99 | 0 | 180 |
| 1 | charge | −2, 2 | −1 | 64, 69 | −77 | 59, 98 | 48, 99 | −1 | 80 |
| 2 | charge | −4, 4 | −2 | 61, 71 | −88 | 56, 94 | 48, 99 | −3 | 80 |
| 3 | charge | −4, 4 | −2 | 60, 71 | −83 | 58, 91 | 48, 99 | −5 | 60 |
| 4 | thrust | 1, 0 | 1 | 70, 66 | −29 | 68, 92 | 47, 98 | −7 | 40 |
| 5 | thrust | 7, −1 | 3 | 80, 65 | −5 | 77, 100 | 46, 97 | −10 | 50 |
| 6 | thrust | 8, 1 | 2 | 80, 67 | −5 | 77, 100 | 46, 99 | −8 | 70 |
| 7 | recover | 6, 3 | 1 | 77, 69 | −8 | 75, 100 | 47, 99 | −2 | 70 |
| 8 | recover | 4, 2 | 0 | 73, 69 | −25 | 70, 96 | 48, 99 | 5 | 80 |
| 9 | recover | 2, −1 | −1 | 70, 67 | −43 | 64, 94 | 48, 99 | 7 | 90 |
| 10 | recover | 0, −1 | 0 | 67, 66 | −59 | 61, 97 | 48, 99 | 4 | 100 |
| 11 | recover | 0, 0 | 0 | 66, 67 | −65 | 60, 100 | 48, 99 | 1 | 170 |

帧 0 不复制帧，身体层保持底稿。帧 1–11 先 `duplicateFrame`，再用 `copyRect` 把身体层恢复成帧 0，然后按上表位移。层 0、1、3 每一帧都清空重画。枪杆每帧是握点出发、角度为上表角度、参数 t 从 −24 到 35、宽度 3 的直轴（第 287–297 行）。枪缨另乘 `ribbonLag * 0.6`（第 303–304 行）。帧 4–7 加右侧速度线，帧 5–6 再加一条；帧 4–8 在后脚附近画三段短火花（第 312–322 行）。

帧 11 与帧 0 的身体、握点、角度和双脚数字相同，但 `ribbonLag` 是 1 而不是 0，时长是 170 而不是 180。轮辐相位还依赖帧号，所以首尾帧不是逐像素相同的循环。成片非透明像素数：帧 0 为层 638 / 657 / 1069 / 454，帧 11 为层 635 / 662 / 1069 / 448。

图集没有朝向字段。除 `attack_right` 外，没有左、上、下或斜向标签。

## 造型与修复：提交能确认的部分

当前目录是一次整目录替换的结果，不是在绑定冲刺上继续改像素。

- PR [#5](https://github.com/starcloud530/pixelforge-demos/pull/5) 在 `9710c60`（说明只有标题 `feat(demo): replace rigged lunge with frame-authored Nezha attack`，git 作者名记录为 `a`，邮箱 `a@adeMac-Mini.local`，2026-11-15）删除整个 `demos/spear-lunge/`，并新增现在的 `demos/nezha-frame-attack/`。该提交没有正文，没有列出改过的像素。main 上可见的是 squash `92a0fe74`；`9710c60` 不是 main 的祖先，但两棵树的本目录内容一致。
- 更早的 `7126056`、`29a3893`、`fd50f41`、`881a586`、`86be705` 都作用在已删除的 `demos/spear-lunge/`。其中 `86be705` 的 `build.py` 有 `solveConstraints`（约第 917 行）、`constraint` 且类型为 `ik`（约第 1001–1031、1205–1213 行）和 `bake --from 0 --to <末帧> --fps <FPS>`（约第 1472 行）。`881a586` 的说明是收剪影、落脚、布料和时机；`86be705` 的说明是 bake 之后保住枪杆剪影。这些说明对应的文件已经不在交付目录里，不能当成当前哪吒像素的修复记录。PR 正文也写了曲线/IK 原型已移出交付目录。
- 谁手调了 `poses.json` 里的数字，提交说明没有写。未知。
- 身体层 1069 个像素只存在于 `source/body.pxf.json`。`build.py` 不重画这层轮廓，只做复制和平移。这些像素第一次如何画入底稿，git 里没有更早的本目录提交。未知。
- `reports/reference-check.json` 写明对照物是 “selected twelve-frame Nezha preview from this conversation”，并给出 12 个 RGBA SHA-256，`status` 为 `passed`。参考图和生成这段 JSON 的脚本都不在仓库里，无法独立复核，也不能从中确定挑选者。未知。
- 仓库级 [LICENSE-ASSETS.md](../../LICENSE-ASSETS.md) 写 `demos/` 美术为 AI 辅助生成、再经维护者整理。本目录 README 要求署名时注明 CLI 绘制、AI 辅助编排。两处都是总说明，不是一笔一笔的造型记录。

当前脚本里能够直接看到、且属于这次哪吒文件的造型规则，是上一节的直枪轴、独立枪缨、红绫滞后、速度线和后脚火花，以及闭式膝点。它们是 `build.py` 常量，没有单独的「人工修复」提交。

## 已有自动检查

`validate.py` 的文档字符串写明它检查的是编排内容和导出，不是审美。通过时把 `reports/validate.json` 写成 `aestheticApproval: false`，`limits` 写明覆盖像素连续性、结构、时长和文件身份，不覆盖自然度或美术认可。`stamp.json` 同样是 `aestheticApproval: false`。

| 检查 | 位置 | 通过时能说明的事 | 通过时不能说明的事 |
| --- | --- | --- | --- |
| `scene` 的宽、高、帧数是 128、128、12 | `validate.py` 第 123–124 行 | 成片工程的画布和帧数 | 画面内容正确 |
| 层名等于 `brief.json` 的四层 | 第 125–126 行 | 层顺序和层名未变 | 层内像素的对错 |
| `scene` 的 `parts`、`curves`、`constraints` 为假 | 第 127–128 行 | 这次打开的工程没有这三项绑定元数据 | CLI 不具备这些能力；也不是求解结果 |
| 帧延迟等于 `poses.json` | 第 129–130 行 | 工程延迟与姿势表一致 | 动作节奏好看 |
| `activeFrame == 0` | 第 131–132 行 | 工程重新打开时停在第 0 帧 | 第 0 帧是合格的准备姿势 |
| 存在 `attack_right`，且 `from`/`to` 为 0 和 11 | 第 133–138 行 | 这条全长标签的帧范围还在 | 不读 `loop`。不检查 `ready`、`charge`、`thrust`、`recover` 是否存在 |
| 每帧每层 `previewFrame` 有非零像素 | 第 150–153 行 | 四层都不是空层 | 造型、朝向、遮挡关系 |
| 腿层在 `(脚 x, 脚 y−7)` 非透明 | 第 155–157 行 | 姿势表给出的两只脚上方 7 像素处，腿层有像素 | 接触约束、地面、脚底承重。README 也写了风火轮最低焰不能当脚底接触点 |
| 帧 1–11 的腿层与帧 0 腿层有差异 | 第 158–160 行 | 下肢相对准备帧有像素变化。`validate.json` 记录的差异像素数为 403、547、539、606、968、884、792、619、498、351、43 | 步态正确，或变化来自求解器 |
| 枪中心线 t=−21…28 的取整像素在手臂层非透明 | 第 166–169 行 | 这段采样中心线没有洞 | 整支武器无洞。绘制范围是 t=−24…35，枪头多边形还伸到约 t=43。也不是刚体或物理刚性 |
| 底稿 `frameCount == 1`，且 `paletteHash` 与成片相同 | 第 171–173 行 | 底稿仍是单帧，两边色板哈希相同 | `paletteLocked` 的值；当前两边都是 false，脚本不检查该字段 |
| `validate-atlas … --four-direction off` 退出码 0 | 第 176–191 行 | 在四向检查关闭时，atlas 与 sheet 通过该子命令 | 四向或八向布局。脚本显式关掉四向，也没有任何八向参数 |
| APNG `fcTL` 延迟与姿势表精确相等 | 第 48–63 行 | 已提交 APNG 的 12 段延迟就是 180、80、80、60、40、50、70、70、80、90、100、170 | 平均帧率一类的近似 |
| GIF 每帧延迟与总和都在 10 ms 以内 | 第 98–105 行 | 已提交 GIF 的延迟落在百分秒容差内。`validate.json` 里这次刚好逐帧相等，总和 1070 | 容差本身允许每帧差 10 ms。相等是这次文件的结果，不是检查器要求逐毫秒相等 |
| `stamp.json` 里七个路径的 SHA-256 与文件一致 | 第 193–196 行 | 底稿、姿势表、工程、sheet、atlas、APNG、GIF 与那次盖章时相同 | 审美通过，或与仓库外参考图一致 |

`reports/replay-check.json` 写 `scope` 为 “fresh build”，七个哈希与 `stamp.json` 相同，`status` 为 `passed`。`build.py` 和 `validate.py` 都不写这个文件，生成命令不在本目录。它是一份已提交的外部重跑记录，这次说明没有重做那次重跑。

`reports/reference-check.json` 同样没有对应脚本。它只保存哈希和一句对照说明，仓库里没有被对照的预览图。

因此，现有自动检查能一起说明的是：这是一套 128×128、12 帧、1070 ms、四层、带 `attack_right` 全长标签的逐帧工程；绑定元数据为空；下肢相对准备帧有变化；脚点上方 7 像素和枪中心线的一段采样非空；图集在关闭四向检查时通过；盖章文件未被改写。它们不证明 IK、约束、曲线或物理，不证明八向，也不证明 `aestheticApproval`。
