"""Stage the static site and its sample downloads from the canonical demo files."""

import argparse
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
KEEPER = ROOT / "demos/demo-zombie"
NEZHA = ROOT / "demos/nezha-frame-attack"

KEEPER_README = """# 港口守灯人

a/ 基础角色，b/ 披风换装，c/ 共享色板道具，d/ 局部修改。
每组包含 .pxf.json 源工程、原尺寸 PNG 和同目录的 atlas JSON。

解压后，在本目录使用 PixelForge v0.1.0-rc.6：

    pixelforge validate-atlas --atlas a/keeper-sheet.atlas.json
    pixelforge play --project a/keeper.pxf.json

安装：https://starcloud530.github.io/pixelforge-ai/install/
重放：https://github.com/starcloud530/pixelforge-demos/tree/main/demos/demo-zombie

美术采用 CC BY 4.0，署名 PixelForge / starcloud530。详见 LICENSE-ASSETS.md。
"""

NEZHA_README = """# 哪吒逐帧动作

包含 .pxf.json 源工程、原尺寸 PNG、atlas JSON 与透明 APNG。
解压后，在本目录使用 PixelForge v0.1.0-rc.6：

    pixelforge validate-atlas --atlas nezha-attack.atlas.json
    pixelforge play --project nezha-attack.pxf.json

安装：https://starcloud530.github.io/pixelforge-ai/install/
重放：https://github.com/starcloud530/pixelforge-demos/tree/main/demos/nezha-frame-attack

美术采用 CC BY 4.0，署名 PixelForge / starcloud530。详见 LICENSE-ASSETS.md。
"""


def write_bundle(destination, source, paths, readme):
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(source / path, path)
        archive.write(ROOT / "LICENSE-ASSETS.md", "LICENSE-ASSETS.md")
        archive.writestr("README.md", readme)


def build(destination):
    shutil.copytree(ROOT / "site", destination, dirs_exist_ok=True)
    assets = destination / "assets"

    media = {
        "keeper-sheet.png": KEEPER / "a/keeper-sheet.png",
        "keeper-sheet.atlas.json": KEEPER / "a/keeper-sheet.atlas.json",
        "keeper-storm-sheet.png": KEEPER / "b/keeper-storm-sheet.png",
        "keeper-storm-sheet.atlas.json": KEEPER / "b/keeper-storm-sheet.atlas.json",
        "keeper-validation.json": KEEPER / "validation.json",
        "nezha-attack.gif": NEZHA / "final/nezha-attack.gif",
        "nezha-attack-sheet.png": NEZHA / "final/nezha-attack-sheet.png",
        "nezha-attack.atlas.json": NEZHA / "final/nezha-attack.atlas.json",
        "nezha-ready.png": NEZHA / "final/poses/00-ready.png",
        "nezha-charge.png": NEZHA / "final/poses/02-charge.png",
        "nezha-thrust.png": NEZHA / "final/poses/05-thrust.png",
        "nezha-recover.png": NEZHA / "final/poses/08-recover.png",
        "nezha-validation.json": NEZHA / "reports/validate.json",
    }
    for name, source in media.items():
        shutil.copy2(source, assets / name)

    write_bundle(
        assets / "port-keeper.zip",
        KEEPER,
        [
            "a/keeper.pxf.json",
            "a/keeper-sheet.png",
            "a/keeper-sheet.atlas.json",
            "a/frame-names.csv",
            "b/keeper-storm-cape.pxf.json",
            "b/keeper-storm-sheet.png",
            "b/keeper-storm-sheet.atlas.json",
            "b/verification.json",
            "c/harbor-props.pxf.json",
            "c/harbor-props-sheet.png",
            "c/harbor-props-sheet.atlas.json",
            "d/local-iterations.pxf.json",
            "d/iteration-sheet.png",
            "d/iteration-sheet.atlas.json",
            "d/verification.json",
            "validation.json",
            "media-latest.json",
        ],
        KEEPER_README,
    )
    write_bundle(
        assets / "nezha-attack.zip",
        NEZHA / "final",
        [
            "nezha-attack.pxf.json",
            "nezha-attack-sheet.png",
            "nezha-attack.atlas.json",
            "nezha-attack.apng",
        ],
        NEZHA_README,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="separate output directory")
    destination = parser.parse_args().destination.resolve()
    if destination == ROOT or ROOT / "site" in (destination, *destination.parents):
        parser.error("choose an output directory outside the site source")
    build(destination)
