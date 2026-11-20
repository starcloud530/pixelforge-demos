# 潮汐温室 · Tidal Glasshouse

[下载完整工程包](https://resources.pixelforge.torzsi.com/studio/rc6/1bacf12e29c69944/tidal-glasshouse.zip?rev=355c8aa45718fe66) · [在作品集中查看](https://starcloud530.github.io/pixelforge-demos/gallery/#tidal-glasshouse)

文件清单与相对路径以解压后的工程包为准。

一张月色水道地图，采用冷色玻璃与暖铜门的配色。主入口以石板接木桥，侧阶通往停着小艇的水面。游戏素材包含岸线、浅波纹、花箱、灯、芦苇、花丛、睡莲、小艇和可拆分的温室。温室本体的三层分别保留轮廓与玻璃、植物与铁件、门灯与反光。

## 交付内容

| 文件 | 内容 |
| --- | --- |
| `tiles.pxf.json` | 51 个 32 × 32 图块。帧编号即图块编号 |
| `glasshouse-facade.pxf.json` | 128 × 96 温室原工程。修改后可重新拆成 4 × 3 图块 |
| `map.pxf-tilemap.json` | 13 × 9 地图，五层为水面、河岸、道路、温室、装饰 |
| `tiles.png`、`tileset.json`、`tile-names.json` | 原尺寸图块图集、图块矩形与名称索引 |
| `tidal-glasshouse.tmj` | Tiled 正交地图。请将 `tiles.png` 放在同目录 |
| `tidal-glasshouse.png`、`tidal-glasshouse-preview.png` | 416 × 288 实际地图导出、832 × 576 整数倍预览 |
| `glasshouse-facade-preview.png` | 独立温室透明背景预览 |
| `validation.json`、`export-checks.json` | PixelForge 地图校验与 Tiled 交付文件复核结果 |
| `build.py`、`sha256.txt` | 重建脚本与原始交付文件的校验和 |

## 重建

使用官方 PixelForge `0.1.0-rc.6`，本次在 Apple Silicon 发布二进制上运行。二进制 SHA-256 为 `6e3c01683634a33e30edb6c3ba058d8091bb9573e9f4270639dafce1711644ea`。Python 3 脚本只编排 CLI 请求，所有像素、图层、图块和地图经 PixelForge CLI 创建与导出。

```bash
python3 build.py --pixelforge /path/to/pixelforge --output rebuilt
(cd rebuilt && shasum -a 256 -c ../sha256.txt)
```

PixelForge 通过了图块尺寸、地图层和图块引用检查。重建脚本还逐格比对了 PixelForge 地图与 Tiled 文件，包括空格、图块索引和翻转标记。提供的是正交渲染素材。碰撞、寻路、地形刷规则和实际游戏引擎导入尚未测试。素材已目视检查，尚未做独立美术评审。
