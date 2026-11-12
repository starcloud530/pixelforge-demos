# 像素转换质量基准 v1

固定输入、固定尺寸、固定色数，用来比较「任意尺寸 PNG → 索引帧」的方法。v1 只跑通中心采样。盲评、人工特征保留、严重缺陷和精修时间留在表里，值为空。

这个目录不是 Agent 题。Agent 题在 [`../../tasks/`](../../tasks/)。这里的 `check.py` 只校验本基准，不会拉起外部 Agent。

## 协议里写死的条件

| 项 | 值 |
| --- | --- |
| 目标 | 64×64 与 128×128，每种固件各一行 |
| 不透明色上限 | 16（`--palette-strategy limit --max-colors 16`） |
| 基线引擎 | `center-sample` |
| 展示 | 最近邻 4 倍，透明区铺在 `#808080` 上再给人看 |
| 对照栏 | `traditional`、`service`、`model` 只占位，本轮不跑 |

同一固件、同一尺寸、同一方法用同一条命令。不按某张图改色数、阈值或采样参数。

## 目录

| 路径 | 作用 |
| --- | --- |
| [protocol.json](protocol.json) | 机器可读的常数 |
| [PROTOCOL.md](PROTOCOL.md) | 怎么比、怎么盲评、怎么记精修 |
| [METRICS.md](METRICS.md) | 指标定义 |
| [DATASET.md](DATASET.md) | 测试集与以后扩到 100–200 个角色的规则 |
| [manifest.json](manifest.json) | v1 固件清单 |
| [fixtures/png/](fixtures/png/) | 程序生成的源图 |
| [templates/](templates/) | 记录行、盲评票、精修日志的空模板 |
| [records/v1/center-sample/](records/v1/center-sample/) | 已跑通的基线记录表 |
| `check.py` | 校验 |
| `generate_fixtures.py` | 重写程序固件 |
| `run_baseline.py` | 重跑中心采样并覆写记录表 |
| `review_sheet.py` | 做给人看的 4 倍图 |

草稿工程写到 `eval/runs/pixel-convert-v1/`，该目录已被 Git 忽略。

## 复现

已发布的 `v0.1.0-rc.2` 安装包还没有 `convert`。记录表钉在 pixelforge-ai 提交 `9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d`（含已合入的 PNG 转换与三种调色板策略）。本仓不携带引擎源码。

```bash
git clone https://github.com/starcloud530/pixelforge-ai.git
git -C pixelforge-ai checkout 9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d
cargo build -p pixelforge-cli --release --manifest-path pixelforge-ai/Cargo.toml
export PIXELFORGE_BIN="$PWD/pixelforge-ai/target/release/pixelforge"

python3 eval/benchmarks/pixel-convert-v1/check.py
python3 eval/benchmarks/pixel-convert-v1/check.py --with-cli
```

`--with-cli` 会再转一遍，并核对索引哈希、调色板报告哈希和由它们算出的指标。耗时不会与记录表逐毫秒相同。

只想重写记录表时：

```bash
python3 eval/benchmarks/pixel-convert-v1/generate_fixtures.py
python3 eval/benchmarks/pixel-convert-v1/run_baseline.py \
  --cli-commit 9fc35888aad9a5b8c4edfeeeab4bfc8e49ab9b1d
```

给人看的图（不进 Git）：

```bash
python3 eval/benchmarks/pixel-convert-v1/review_sheet.py \
  --project eval/runs/pixel-convert-v1/projects/pf-cv-001-mass-64x64-center-sample-run1.json \
  --output eval/runs/pixel-convert-v1/sheets/pf-cv-001-mass-64.png
```

`pixelforge preview --project … --scale 4 --output …` 也能看彩色结果。盲评用的是铺在 `#808080` 上的那张，不要直接拿未铺底的预览互比。

## 怎么读记录表

[records/v1/center-sample/table.json](records/v1/center-sample/table.json) 是正本，`table.csv` 是同一张表的扁平行。[aggregate.json](records/v1/center-sample/aggregate.json) 是这 12 行的汇总。

自动列有延迟、确定性、色数、结构探针、PSNR、SSIM。下列字段在 v1 必须是空的，不能填估算值：

- `blind_preference`
- `feature_retention_human`
- `severe_defect_human` 与 `severe_defect_codes_human`
- `retouch_minutes`
- `cost_usd`
- `lpips`

人工填写用 [templates/](templates/) 里的票和精修日志，再按 [METRICS.md](METRICS.md) 汇总。汇总前胜率、人工特征保留率、人工严重缺陷率和精修时间保持 `null`。

## #131 first-slice supplement

The original v1 snapshot remains frozen. An additional `traditional` record now
lives beside center-sample; see [TRADITIONAL.md](TRADITIONAL.md). The checker
validates/replays both methods. The paired seed is separate from these fixtures:
[paired-seed](../pixel-convert-pairs-v0/README.md). No model is trained here.
