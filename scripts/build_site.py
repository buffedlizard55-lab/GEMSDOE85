#!/usr/bin/env python3
from gems85_site import build

if __name__ == "__main__":
    c = build()
    print(f"Built site & canonical run_card cleanly: {c['submission']['file']} (HOLDOUT-DTI={c['holdout']['dti']:.6f})")
