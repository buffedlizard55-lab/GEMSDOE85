#!/usr/bin/env python3
"""Compatibility entrypoint: canonical fail-closed publisher."""
from build_site import main
if __name__ == '__main__':
    raise SystemExit(main())
