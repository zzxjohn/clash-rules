#!/usr/bin/env python3
"""Compatibility entry point: use sync_rulesets.py for registry-driven sync."""
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name("sync_rulesets.py")
_spec = importlib.util.spec_from_file_location("sync_rulesets", _path)
_sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sync)
FIELDS = _sync.FIELDS
parse_source = _sync.parse_source


def convert(data):
    return _sync.convert(data)


if __name__ == "__main__":
    try:
        _sync.main()
    except (ValueError, OSError) as error:
        print(f"Sync failed: {error}", file=sys.stderr)
        sys.exit(1)
