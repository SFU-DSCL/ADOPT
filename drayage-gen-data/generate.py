#!/usr/bin/env python3
"""Run drayage-gen-data directly from a source checkout without installation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from drayage_gen_data.cli import main


if __name__ == "__main__":
    main()
