import os
import struct
import json
import multiprocessing
from bitcoin.core import CBlock
from typing import Iterator, Optional
from tqdm import tqdm
from pathlib import Path

MAGIC_BYTES = b"\xf9\xbe\xb4\xd9"
MAGIC_LEN = 4
LENGTH_LEN = 4
INDEX_FILE = ".blkindex.json"

# ─────────────────────────────────────────────────────────────
def build_index(blk_dir: str) -> dict:
    index = {}
    blk_files = sorted(
        os.path.join(blk_dir, f)
        for f in os.listdir(blk_dir)
        if f.startswith("blk") and f.endswith(".dat")
    )
    height = 0
    for path in blk_files:
        with open(path, "rb") as f:
            offset = 0
            while True:
                magic = f.read(MAGIC_LEN)
                if not magic:
                    break
                if magic != MAGIC_BYTES:
                    f.seek(offset + 1)
                    offset += 1
                    continue
                raw_len = f.read(LENGTH_LEN)
                if len(raw_len) < 4:
                    break
                block_size = struct.unpack("<I", raw_len)[0]
                raw_block = f.read(block_size)
                if len(raw_block) < block_size:
                    break
                index[height] = {"file": os.path.basename(path), "offset": offset}
                offset = f.tell()
                height += 1
    with open(os.path.join(blk_dir, INDEX_FILE), "w") as f:
        json.dump(index, f)
    return index


class BlkFileSource:
    def __init__(self, blk_dir, start_height=0, end_height=None):
        self.blk_dir = blk_dir
        self.start_height = start_height or 0
        self.end_height = end_height
        self.index_path = os.path.join(blk_dir, INDEX_FILE)
        self.index = self._load_or_build_index()

    def _load_or_build_index(self):
        if Path(self.index_path).exists():
            with open(self.index_path) as f:
                return json.load(f)
        return build_index(self.blk_dir)

    def __iter__(self):
        expected_blocks = sum(
            1 for h in range(self.start_height, self.end_height + 1)
            if str(h) in self.index or h in self.index
        )

        bar = tqdm(total=expected_blocks, desc="Reading blk*.dat", unit="blk", dynamic_ncols=True)

        for h in range(self.start_height, self.end_height + 1):
            meta = self.index.get(str(h)) or self.index.get(h)
            if not meta:
                continue
            path = os.path.join(self.blk_dir, meta["file"])
            with open(path, "rb") as f:
                f.seek(meta["offset"])
                magic = f.read(MAGIC_LEN)
                if magic != MAGIC_BYTES:
                    continue
                raw_len = f.read(LENGTH_LEN)
                if len(raw_len) < 4:
                    continue
                block_size = struct.unpack("<I", raw_len)[0]
                raw_block = f.read(block_size)
                blk_hash = CBlock.deserialize(raw_block).GetHash()
                bar.update(1)
                yield {
                    "height": int(h),
                    "hash": blk_hash.hex(),
                    "raw": raw_block,
                }
        bar.close()



def _process_file_for_range(args):
    path, height_offset, start_height, end_height = args
    results = []
    local_count = 0
    global_height = height_offset
    with open(path, "rb") as f:
        while True:
            magic = f.read(MAGIC_LEN)
            if not magic:
                break
            if magic != MAGIC_BYTES:
                continue
            raw_len = f.read(LENGTH_LEN)
            if len(raw_len) < 4:
                break
            block_size = struct.unpack("<I", raw_len)[0]
            raw_block = f.read(block_size)
            if len(raw_block) < block_size:
                break
            if global_height < start_height:
                local_count += 1
                global_height += 1
                continue
            if global_height > end_height:
                break
            blk_hash = CBlock.deserialize(raw_block).GetHash()
            results.append({
                "height": global_height,
                "hash": blk_hash.hex(),
                "raw": raw_block,
            })
            local_count += 1
            global_height += 1
    return results


class ParallelBlkFileSource:
    def __init__(
        self,
        blk_dir: str,
        start_height: Optional[int] = 0,
        end_height: Optional[int] = None,
        processes: int = 4,
    ):
        self.blk_dir = blk_dir
        self.start_height = start_height or 0
        self.end_height = end_height or 0xFFFFFFFF
        self.processes = processes

    def __iter__(self) -> Iterator[dict]:
        blk_files = sorted(
            f for f in os.listdir(self.blk_dir)
            if f.startswith("blk") and f.endswith(".dat")
        )
        full_paths = [os.path.join(self.blk_dir, f) for f in blk_files]
        estimated_offsets = {path: i * 3000 for i, path in enumerate(full_paths)}
        args = [
            (path, estimated_offsets[path], self.start_height, self.end_height)
            for path in full_paths
        ]

        total_files = len(args)
        with multiprocessing.Pool(processes=self.processes) as pool, tqdm(
            total=total_files, desc="Parallel blk*.dat", unit="file", dynamic_ncols=True
        ) as bar:
            for result in pool.imap_unordered(_process_file_for_range, args):
                for blk in result:
                    yield blk
                bar.update(1)

