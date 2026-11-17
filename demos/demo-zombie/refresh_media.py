#!/usr/bin/env python3
"""Rebuild the Port Keeper README media with an explicitly selected CLI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ASSETS = (
    'a/walk-four-directions.gif',
    'storyboard/hero-before-after.png',
    'storyboard/timeline.png',
    'videos/01-sheet-assembly.mp4',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pixelforge', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='New or empty output directory')
    parser.add_argument('--cdn-prefix', default='port-keeper/v2')
    args = parser.parse_args()
    binary, output = args.pixelforge.resolve(), args.out.resolve()
    version = subprocess.check_output([str(binary), '--version'], text=True).strip()
    env = dict(os.environ, PIXELFORGE_BIN=str(binary), PIXELFORGE_DEMO_OUT=str(output))
    subprocess.run([sys.executable, str(ROOT / 'replay.py'), '--out', str(output)], env=env, check=True)
    subprocess.run([sys.executable, str(ROOT / 'media.py')], env=env, check=True)
    subprocess.run([sys.executable, str(ROOT / 'media.py'), 'sheet-video'], env=env, check=True)
    replay = json.loads((output / 'replay-report.json').read_text())
    records = []
    for name in ASSETS:
        file = output / name
        records.append(dict(file=name, bytes=file.stat().st_size, sha256=digest(file),
                            url=f'https://resources.pixelforge.torzsi.com/{args.cdn_prefix}/{name}'))
    record = dict(character='Port Keeper / 港口守灯人', cliVersion=version,
                  cliBinarySha256=digest(binary), cleanReplay=replay['cleanReplay'],
                  nativeSheetHashes=replay['sheetHashes'],
                  recipeSha256={name: digest(ROOT / name) for name in
                                ('build.py', 'replay.py', 'validate.py', 'media.py', 'refresh_media.py')},
                  aestheticApproval=False, assets=records)
    (output / 'media-rebuild.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('PASS: rebuilt four README media assets; provenance: ' + str(output / 'media-rebuild.json'))


if __name__ == '__main__':
    main()
