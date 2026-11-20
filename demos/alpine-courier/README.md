# 雪岭邮差 · Alpine Post Courier

[下载完整工程包](https://resources.pixelforge.torzsi.com/studio/rc6/1bacf12e29c69944/alpine-courier.zip?rev=36818f595463fd65) · [在作品集中查看](https://starcloud530.github.io/pixelforge-demos/gallery/#alpine-courier)

文件清单与相对路径以解压后的工程包为准。

俯视冒险游戏的原创非战斗 NPC。酒红毛帽、蜜色羽绒服、带扣帆布邮包和防滑靴组成角色识别点。侧面用邮包和围巾加深轮廓，背面保留包盖上的高山标记，避免从各方向看起来像不同角色。

![四向待机与行走精灵表](https://resources.pixelforge.torzsi.com/studio/rc6/1bacf12e29c69944/alpine-courier.png?rev=4741436ca9e0d5f2)

## 工程与导出

- `alpine-courier.pxf.json` 是带 20 色调色板和五个编辑图层的 `64 × 64` 工程。裤腿与靴子、脸与外套、邮包与围巾、袖子、围巾尾可单独修改。
- `alpine-courier.png` 与 `alpine-courier.atlas.json` 是原尺寸游戏图集。行向下、左、右、上排列。每行第一格是 400 ms 的待机，后四格是接触、经过、反脚接触、反脚经过组成的原地循环，总长 520 ms。
- `walk-down.apng`、`walk-left.apng`、`walk-right.apng`、`walk-up.apng` 是透明的逐向播放文件。`courier-preview.png`、`courier-front.png` 供放大审阅。
- `validation.json` 保存严格图集校验、四向标签检查、行走相邻帧差分及核心文件哈希。`trajectory.jsonl` 保存 CLI 调用顺序和退出状态，`build.py` 保留所有绘制请求。

## 重放

Python 3 与官方 [PixelForge v0.1.0-rc.6](https://github.com/starcloud530/pixelforge-ai/releases/tag/v0.1.0-rc.6) 即可重建。这里使用发布包中通过 SHA-256 校对的 macOS Apple silicon 二进制。

```bash
python3 build.py --pixelforge /path/to/pixelforge --out ./courier-replay
pixelforge play --project ./courier-replay/alpine-courier.pxf.json
pixelforge validate-atlas --atlas ./courier-replay/alpine-courier.atlas.json --strict --four-direction on
```

AI 设计并编排原生绘图请求，像素落笔、配色、图层、帧和导出全部经过 PixelForge CLI。步态由复制同朝向的待机帧再替换腿、袖和围巾尾得到，经过姿势额外把身体和邮包抬高一格。

## 审阅结果

严格图集校验与四向布局检查通过，16 个循环相邻帧组均有像素变化。从空目录重放得到字节一致的原尺寸图集、atlas 和可编辑工程。对照静态表检查了朝向、配色与轮廓，在近侧袖和两只靴子的形状上保留独立变化。

正式使用前，在目标游戏相机与角色移动速度下核对脚跟支撑、后退步态和前后朝向走路时的重心变化。
