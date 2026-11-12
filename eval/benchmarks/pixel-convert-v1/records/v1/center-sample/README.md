# 中心采样记录 v1

正本是 [table.json](table.json)，扁表是 [table.csv](table.csv)，这 12 行的汇总是 [aggregate.json](aggregate.json)。命令见 [commands.jsonl](commands.jsonl)，版本与哈希见 [meta.json](meta.json)。

12 行都转换成功，三次索引一致，不透明色数都不超过 16。自动探针里，64×64 的 3 像素竖线命中率为 0，记了 S2；64×64 的 4 像素连接命中率低于 0.5，探针未通过，但不是 S2。史莱姆两行和盒式参照相同，所以 PSNR 为空。

人工偏好、人工特征保留、人工严重缺陷、精修时间和费用是空的。自动严重旗标不是人工严重缺陷率。PSNR 和 SSIM 是对盒式滤波预览的辅助数。

工程文件不在这个目录里。按上级 [README.md](../../README.md) 重跑后，它们出现在 `eval/runs/pixel-convert-v1/projects/`。
