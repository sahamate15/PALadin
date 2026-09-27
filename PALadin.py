"""Compatibility launcher for running PALadin directly from a checkout."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from paladin.cli import main

raise SystemExit(main())
