# framework_bt/mempoolsource.py
"""
MempoolApiSource
────────────────
Descarga bloques completos (raw) sólo vía HTTPS desde la API pública
de mempool.space.

Flujo por bloque:
    1. GET /block-height/<height>      → devuelve el hash
    2. GET /block/<hash>/raw           → devuelve el bloque binario
Produce dicts idénticos a RpcSource / BlkFileSource:
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
        :param delay: pausa (segundos) entre peticiones para respetar el rate-limit.
                      0.2 s ≈ 5 consultas/s, tolerado por la API pública.
        """
        self.start = start_height
        self.end   = end_height
        self.delay = max(0.0, delay)

    # ──────────────────────────────────────────
    # Iterable
    # ──────────────────────────────────────────
    def __iter__(self) -> Iterator[dict]:
        total = self.end - self.start + 1
        bar   = tqdm(total=total, desc="HTTP blocks", unit="blk", dynamic_ncols=True)

        for h in range(self.start, self.end + 1):
            # 1) resolver hash
            r = requests.get(_HASH_URL.format(h), timeout=10)
            r.raise_for_status()
            blk_hash = r.text.strip()

            # 2) descargar raw
            raw = requests.get(_RAW_URL.format(blk_hash), timeout=30).content

            bar.update(1)
            yield {"height": h, "hash": blk_hash, "raw": raw}

            if self.delay:
                time.sleep(self.delay)

        bar.close()
