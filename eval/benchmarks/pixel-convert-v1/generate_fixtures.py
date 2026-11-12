#!/usr/bin/env python3
"""Write the procedural PNGs and fixtures/hashes.json."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.fixtures import write_fixtures


def main() -> int:
    document = write_fixtures()
    print(f"wrote {len(document['files'])} fixture hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
