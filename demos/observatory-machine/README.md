# 星芒风候仪 · Aster Wind Observatory

[下载完整工程包](https://resources.pixelforge.torzsi.com/studio/rc6/1bacf12e29c69944/observatory-machine.zip?rev=fa0b682eec2099fc) · [在作品集中查看](https://starcloud530.github.io/pixelforge-demos/gallery/#observatory-machine)

文件清单与相对路径以解压后的工程包为准。

用于经营或探索游戏的原创互动机关。青铜机身、嵌入式仪表、储液玻璃筒和石台放在同一透视下。启动时风杯逐步加速，指针扫过刻度，状态灯与储液筒从暗色转为青绿。采样阶段保持稳定转速，玻璃筒内的气泡持续上升。

## 交付文件

| 文件 | 用途 |
| --- | --- |
| `exports/aster-wind-observatory.pxf.json` | 可编辑源工程，96 × 96，24 个不透明色，12 帧，五层 |
| `exports/aster-wind-observatory-sheet.png` 和 `exports/aster-wind-observatory.atlas.json` | 384 × 288 原尺寸精灵表与帧坐标、时长、动画标签 |
| `exports/aster-wind-observatory-power-on.png` | 启动 APNG，播放一次 |
| `exports/aster-wind-observatory-sampling.png` | 采样 APNG，循环播放 |
| `exports/aster-wind-observatory-poster.png` | 480 × 480 透明静帧预览 |
| `exports/aster-wind-observatory-native.png` | 96 × 96 静帧，便于直接检查原尺寸可读性 |
| `exports/validation.json` | 图集校验、图层一致性、动画范围与哈希 |

## 动画标签

| 标签 | 帧索引 | 时长 | 播放 |
| --- | --- | --- | --- |
| `dormant` | 0 | 320 ms | 开机前静帧 |
| `power_on` | 0–4 | 767 ms | 单次启动 |
| `sampling` | 4–11 | 736 ms | 持续采样循环 |

在游戏中可以用 `dormant` 静帧，交互触发后播放 `power_on`，再进入 `sampling`。推荐在引擎中手动设置过滤为 Nearest，轴心从石台地面落点约 `(48, 88)` 开始调。实际接入项目时按场景网格和美术方向调整。

## 重放

所有像素由官方发行版 [PixelForge v0.1.0-rc.6](https://github.com/starcloud530/pixelforge-ai/releases/tag/v0.1.0-rc.6) 的 CLI / Tool API 绘制。Python 只编排调色板、几何笔画、帧复制、导出与校验。每个新帧复制上一帧，只重绘风杯转子和信号层的局部区域。

```sh
python3 build.py --pixelforge "$(command -v pixelforge)" --out ./rebuild
```

用空输出目录重建。可加 `--stages` 输出剪影、机身和细节三个检查阶段。原生图集的 SHA-256 为 `e0546ec1e011b5d24307d73a3d3958c335303b19cd1fc26825c6e14f5d405f2b`。

## 验收

`validate-atlas --strict` 返回 0 错误、0 警告，且三段标签齐全。静态的石台、青铜机身和仪表层在 12 帧中逐格一致。八个采样转子姿势互异。缩放预览与原尺寸图集已目检。引擎场景内的层级、轴心和美术验收待项目团队复核。
