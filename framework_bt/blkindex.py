# framework_bt/blkindex.py
import os
import json
import struct
from pathlib import Path
from tqdm import tqdm
from typing import Dict
from bitcoin.core import CBlock

MAGIC = b"\xf9\xbe\xb4\xd9"
MAGIC_LEN = 4
LENGTH_LEN = 4

INDEX_FILE = ".blkindex.json"


def build_blk_index(blk_dir: str, save_path: str = None) -> Dict[int, dict]:
    """
    Scans all blk*.dat files and builds an index mapping block height to
    file path, offset, and size. Optionally saves the index to JSON.
    """
    blk_dir = Path(blk_dir)
    index = {}
    height = 0

    blk_files = sorted(
        f for f in blk_dir.iterdir()
        if f.name.startswith("blk") and f.name.endswith(".dat")
    )

    for path in blk_files:
        with path.open("rb") as f:
            offset = 0
            pbar = tqdm(desc=f"Indexing {path.name}", unit="blk", dynamic_ncols=True)

            while True:
                magic = f.read(MAGIC_LEN)
                if not magic:
                    break
                if magic != MAGIC:
                    offset += 1
                    f.seek(offset)
                    continue

                raw_len = f.read(LENGTH_LEN)
                if len(raw_len) < 4:
                    break
                block_size = struct.unpack("<I", raw_len)[0]
                raw_block = f.read(block_size)
                if len(raw_block) < block_size:
                    break

                try:
                    blk_hash = CBlock.deserialize(raw_block).GetHash().hex()
                except Exception:
                    offset += 1
                    f.seek(offset)
                    continue

                index[height] = {
                    "file": path.name,
                    "offset": offset,
                    "size": block_size + MAGIC_LEN + LENGTH_LEN,
                    "hash": blk_hash
                }

                offset = f.tell()
                height += 1
                pbar.update(1)

            pbar.close()

    if save_path is None:
        save_path = blk_dir / INDEX_FILE
    with open(save_path, "w") as fp:
        json.dump(index, fp, indent=2)

    return index