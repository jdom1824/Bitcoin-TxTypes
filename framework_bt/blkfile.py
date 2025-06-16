"""
blkfile.py
==========
Fuente de bloques desde archivos blk*.dat, contando bloques por orden secuencial.
No requiere obtener altura desde coinbase. Se permite uso de start/end/hash.
"""

import os
import struct
from typing import Iterator, Optional

from bitcoin.core import CBlock

MAGIC_BYTES = b"\xf9\xbe\xb4\xd9"  # Mainnet
MAGIC_LEN = 4
LENGTH_LEN = 4


class BlkFileSource:
    def __init__(
        self,
        blk_dir: str,
        start_height: Optional[int] = 0,
        end_height: Optional[int] = None,
        hashes: Optional[list[str]] = None,  # ← aceptado aunque no usado aún
    ):
        self.blk_dir = blk_dir
        self.start_height = start_height or 0
        self.end_height = end_height
        self.hashes = hashes
        self._count = 0

    def __iter__(self) -> Iterator[dict]:
        blk_files = sorted(
            f for f in os.listdir(self.blk_dir) if f.startswith("blk") and f.endswith(".dat")
        )

        for fname in blk_files:
            path = os.path.join(self.blk_dir, fname)

            with open(path, "rb") as f:
                while True:
                    magic = f.read(MAGIC_LEN)
                    if not magic:
                        break  # EOF

                    if magic != MAGIC_BYTES:
                        raise ValueError("No se encontró magic number válido")

                    raw_len = f.read(LENGTH_LEN)
                    if len(raw_len) < 4:
                        break
                    block_size = struct.unpack("<I", raw_len)[0]
                    raw_block = f.read(block_size)

                    if len(raw_block) < block_size:
                        break  # bloque incompleto al final

                    if self._count < self.start_height:
                        self._count += 1
                        continue
                    if self.end_height is not None and self._count > self.end_height:
                        return

                    blk_hash = CBlock.deserialize(raw_block).GetHash()

                    # En el futuro, aquí podrías hacer: if self.hashes and blk_hash.hex() not in self.hashes: continue

                    yield {
                        "height": self._count,
                        "hash": blk_hash.hex(),
                        "raw": raw_block,
                    }

                    self._count += 1
