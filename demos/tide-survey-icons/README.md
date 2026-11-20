# 潮汐科考道具

[下载完整工程包](https://resources.pixelforge.torzsi.com/studio/rc6/1bacf12e29c69944/tide-survey-icons.zip?rev=f0ca8f15dae3e782) · [在作品集中查看](https://starcloud530.github.io/pixelforge-demos/gallery/#tide-survey-icons)

文件清单与相对路径以解压后的工程包为准。

八枚原创 32 × 32 背包图标。按图集行序排列：黄铜罗盘、采样瓶、采样钳、潮汐图、浮标、野外放大镜、样品箱和贝壳标本。八枚共享一套 15 色调色板，另附暮潮配色。两套配色保留相同的索引格和资源标签。

使用官方 PixelForge v0.1.0-rc.6，由 AI 通过本地 CLI 的基本绘制工具完成。从源工程可继续修改每个图标、统一换色或再次导出。透明 PNG 与 atlas JSON 可一起切片，标签名与对应物件一一匹配。预览为内核放大四倍的导出。

## 重建与检查

```bash
python3 build.py --pixelforge /path/to/pixelforge --out /tmp/tide-survey-icons
pixelforge validate-atlas --size 32 --atlas /tmp/tide-survey-icons/tide-survey-icons.atlas.json
```

两版图集都通过 32 像素规格和 8 个必需标签的严格检查，0 错误、0 警告。空目录重建后，源工程、图集、调色板、预览及校验报告字节一致。已目视检查放大预览，正式 UI 内的原尺寸可读性仍需在目标背景验收。
