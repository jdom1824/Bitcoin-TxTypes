# framework_bt/mempoolsource.py
"""
MempoolApiSource
────────────────
Downloads full blocks (raw) via HTTPS using the public mempool.space API.

Per-block flow:
    1. GET /block-height/<height>      → returns the block hash
    2. GET /block/<hash>/raw           → returns the raw block bytes
Produces dicts identical to RpcSource / BlkFileSource:
    {"height": int, "hash": str, "raw": bytes}
"""

from __future__ import annotations
import time
from typing import Iterator

import requests
from tqdm import tqdm

_HASH_URL = "https://mempool.space/api/block-height/{}"
_RAW_URL  = "https://mempool.space/api/block/{}/raw"


class MempoolApiSource:
    def __init__(self, start_height: int, end_height: int, *, delay: float = 0.2):
        """
        :param delay: Delay (in seconds) between requests to respect API rate limits.
                      0.2 s ≈ 5 requests/sec, which is tolerated by the public API.
        """
        self.start = start_height
        self.end   = end_height
        self.delay = max(0.0, delay)

    # ──────────────────────────────────────────
    # Iterable interface
    # ──────────────────────────────────────────
    def __iter__(self) -> Iterator[dict]:
        total = self.end - self.start + 1
        bar   = tqdm(total=total, desc="HTTP blocks", unit="blk", dynamic_ncols=True)

        for h in range(self.start, self.end + 1):
            # Step 1: resolve hash by height
            r = requests.get(_HASH_URL.format(h), timeout=10)
            r.raise_for_status()
            blk_hash = r.text.strip()

            # Step 2: download raw block
            raw = requests.get(_RAW_URL.format(blk_hash), timeout=30).content

            bar.update(1)
            yield {"height": h, "hash": blk_hash, "raw": raw}

            if self.delay:
                time.sleep(self.delay)

        bar.close()
